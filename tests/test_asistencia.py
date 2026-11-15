"""Pruebas unitarias y de integración de asistencia (E6 / PF-10)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import CodigosError, Conflicto, NoAutorizado, NoEncontrado
from app.core.fechas import VENTANA_ASISTENCIA_HORAS, ahora_utc
from app.models.asistencia import Asistencia
from app.models.enums import (
    EstadoAsistencia,
    EstadoEvento,
    EstadoInscripcion,
    PublicoObjetivo,
    Rol,
)
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario
from app.services import asistencia_service

ORIGEN = {"Origin": "https://testserver"}


def _crear_evento_y_participante(
    db: Session,
    crear_usuario_factory,
    *,
    estado_evento: str = EstadoEvento.PUBLICADO.value,
    estado_inscripcion: str = EstadoInscripcion.ACTIVA.value,
    inicio_offset_horas: int = -2,
    fin_offset_horas: int = 2,
    numero_documento: str | None = None,
):
    """Crea un organizador, un evento y una inscripción para pruebas de asistencia."""
    org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Org Asistencia")
    part = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento=numero_documento,
        nombre="Ana Participante",
        correo="ana.part@example.edu",
    )
    ahora = ahora_utc()
    inicio = ahora + timedelta(hours=inicio_offset_horas)
    fin = ahora + timedelta(hours=fin_offset_horas)
    evento = Evento(
        titulo="Taller de Pruebas E6",
        descripcion="Descripción de taller",
        tipo="taller",
        fecha_inicio=inicio,
        fecha_fin=fin,
        fecha_limite_inscripcion=inicio - timedelta(days=1),
        lugar="Sala 202",
        modalidad="presencial",
        publico_objetivo=PublicoObjetivo.TODOS.value,
        responsable_nombre="Responsable E6",
        responsable_correo="resp.e6@example.edu",
        cupo_maximo=20,
        estado=estado_evento,
        organizador_id=org.id,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)

    inscripcion = Inscripcion(
        evento_id=evento.id,
        participante_id=part.id,
        estado=estado_inscripcion,
    )
    db.add(inscripcion)
    db.commit()
    db.refresh(inscripcion)
    return org, part, evento, inscripcion


def _login(client: TestClient, usuario: Usuario) -> None:
    """Inicia sesión en TestClient para fijar cookie HttpOnly."""
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": usuario.tipo_documento,
            "numero_documento": usuario.numero_documento,
            "password": "ClaveSegura123!",
        },
        headers=ORIGEN,
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Pruebas unitarias de servicio (ventana 48 h, UPSERT, permisos y máscara)
# ---------------------------------------------------------------------------


def test_servicio_registrar_y_corregir_asistencia_sin_duplicar(
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """RN-08 / RN-10: registra y corrige asistencia haciendo UPSERT sobre el mismo registro."""
    org, _part, evento, inscripcion = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
    )
    t1 = datetime(2026, 11, 14, 15, 0, tzinfo=UTC)
    t2 = t1 + timedelta(minutes=10)
    evento.fecha_inicio = t1 - timedelta(hours=1)
    evento.fecha_fin = t1 + timedelta(hours=2)
    evento.fecha_limite_inscripcion = evento.fecha_inicio - timedelta(hours=1)
    db_session.commit()

    primera = asistencia_service.registrar_asistencia(
        db_session,
        evento.id,
        inscripcion.id,
        EstadoAsistencia.AUSENTE,
        org,
        proveedor_ahora=lambda: t1,
    )
    assert primera.estado == EstadoAsistencia.AUSENTE.value
    assert primera.registrado_por_id == org.id
    assert primera.registrado_en == t1

    segunda = asistencia_service.registrar_asistencia(
        db_session,
        evento.id,
        inscripcion.id,
        EstadoAsistencia.PRESENTE,
        org,
        proveedor_ahora=lambda: t2,
    )
    assert segunda.id == primera.id
    assert segunda.estado == EstadoAsistencia.PRESENTE.value
    assert segunda.registrado_en == t1
    assert segunda.actualizado_en == t2

    total = db_session.execute(
        select(func.count(Asistencia.id)).where(Asistencia.inscripcion_id == inscripcion.id)
    ).scalar_one()
    assert total == 1


def test_servicio_rechaza_fuera_de_ventana_48h(
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """RN-08: rechaza registro antes de fecha_inicio y en el segundo posterior a +48 h."""
    org, _part, evento, inscripcion = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
    )

    antes = evento.fecha_inicio - timedelta(seconds=1)
    with pytest.raises(Conflicto) as exc_antes:
        asistencia_service.registrar_asistencia(
            db_session,
            evento.id,
            inscripcion.id,
            EstadoAsistencia.PRESENTE,
            org,
            proveedor_ahora=lambda: antes,
        )
    assert exc_antes.value.codigo == CodigosError.ASISTENCIA_NO_PERMITIDA

    limite_exacto = evento.fecha_fin + timedelta(hours=VENTANA_ASISTENCIA_HORAS)
    despues = limite_exacto + timedelta(seconds=1)
    with pytest.raises(Conflicto) as exc_despues:
        asistencia_service.registrar_asistencia(
            db_session,
            evento.id,
            inscripcion.id,
            EstadoAsistencia.PRESENTE,
            org,
            proveedor_ahora=lambda: despues,
        )
    assert exc_despues.value.codigo == CodigosError.ASISTENCIA_NO_PERMITIDA

    en_limite = asistencia_service.registrar_asistencia(
        db_session,
        evento.id,
        inscripcion.id,
        EstadoAsistencia.PRESENTE,
        org,
        proveedor_ahora=lambda: limite_exacto,
    )
    assert en_limite.estado == EstadoAsistencia.PRESENTE.value


def test_servicio_rechaza_evento_o_inscripcion_cancelada(
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """No permite asistencia en evento cancelado ni en inscripción cancelada."""
    org1, _p1, ev_cancelado, insc1 = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
        estado_evento=EstadoEvento.CANCELADO.value,
    )
    with pytest.raises(Conflicto) as exc1:
        asistencia_service.registrar_asistencia(
            db_session, ev_cancelado.id, insc1.id, EstadoAsistencia.PRESENTE, org1
        )
    assert exc1.value.codigo == CodigosError.ASISTENCIA_NO_PERMITIDA

    org2, _p2, ev2, insc_cancelada = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
        estado_inscripcion=EstadoInscripcion.CANCELADA.value,
    )
    with pytest.raises(Conflicto) as exc2:
        asistencia_service.registrar_asistencia(
            db_session, ev2.id, insc_cancelada.id, EstadoAsistencia.PRESENTE, org2
        )
    assert exc2.value.codigo == CodigosError.ASISTENCIA_NO_PERMITIDA


def test_servicio_permisos_y_privacidad_diferencial(
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """RN-11: solo el organizador dueño registra; coordinación ve documento enmascarado."""
    org, part, evento, inscripcion = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
        numero_documento="1020304050",
    )
    otro_org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Otro Org")
    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coordinador")

    for actor in (otro_org, coord, part):
        with pytest.raises(NoAutorizado) as exc:
            asistencia_service.registrar_asistencia(
                db_session, evento.id, inscripcion.id, EstadoAsistencia.PRESENTE, actor
            )
        assert exc.value.codigo == CodigosError.SIN_PERMISO

    lista_org = asistencia_service.listar_asistencia_evento(db_session, evento.id, org)
    assert len(lista_org) == 1
    assert lista_org[0].numero_documento == "1020304050"
    assert lista_org[0].estado_asistencia == "pendiente"

    lista_coord = asistencia_service.listar_asistencia_evento(db_session, evento.id, coord)
    assert len(lista_coord) == 1
    assert lista_coord[0].numero_documento == "••••4050"

    with pytest.raises(NoAutorizado):
        asistencia_service.listar_asistencia_evento(db_session, evento.id, otro_org)

    with pytest.raises(NoEncontrado) as exc_nf:
        asistencia_service.listar_asistencia_evento(db_session, 999999, org)
    assert exc_nf.value.codigo == CodigosError.EVENTO_NO_ENCONTRADO


# ---------------------------------------------------------------------------
# Pruebas de integración HTTP (/api/v1 y vista web)
# ---------------------------------------------------------------------------


def test_api_registrar_corregir_y_consultar_asistencia(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """PF-10: PUT registra/corrige asistencia y GET respeta privacidad por rol."""
    org, _part, evento, inscripcion = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
        numero_documento="9988776655",
    )
    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coord API")

    # Sin sesión -> 401
    resp_401 = client.put(
        f"/api/v1/eventos/{evento.id}/inscripciones/{inscripcion.id}/asistencia",
        json={"estado": "presente"},
        headers=ORIGEN,
    )
    assert resp_401.status_code == 401

    _login(client, org)

    # Registro inicial -> 200 presente
    resp_put1 = client.put(
        f"/api/v1/eventos/{evento.id}/inscripciones/{inscripcion.id}/asistencia",
        json={"estado": "presente"},
        headers=ORIGEN,
    )
    assert resp_put1.status_code == 200
    cuerpo1 = resp_put1.json()
    assert cuerpo1["estado"] == "presente"
    assert cuerpo1["inscripcion_id"] == inscripcion.id

    # Corrección -> 200 ausente, mismo ID
    resp_put2 = client.put(
        f"/api/v1/eventos/{evento.id}/inscripciones/{inscripcion.id}/asistencia",
        json={"estado": "ausente"},
        headers=ORIGEN,
    )
    assert resp_put2.status_code == 200
    assert resp_put2.json()["id"] == cuerpo1["id"]
    assert resp_put2.json()["estado"] == "ausente"

    # Estado inválido -> 422
    resp_422 = client.put(
        f"/api/v1/eventos/{evento.id}/inscripciones/{inscripcion.id}/asistencia",
        json={"estado": "tarde"},
        headers=ORIGEN,
    )
    assert resp_422.status_code == 422

    # GET organizador dueño -> documento completo
    resp_get_org = client.get(f"/api/v1/eventos/{evento.id}/asistencia")
    assert resp_get_org.status_code == 200
    nomina_org = resp_get_org.json()
    assert len(nomina_org) == 1
    assert nomina_org[0]["numero_documento"] == "9988776655"
    assert nomina_org[0]["estado_asistencia"] == "ausente"

    # GET coordinación -> documento enmascarado
    _login(client, coord)
    resp_get_coord = client.get(f"/api/v1/eventos/{evento.id}/asistencia")
    assert resp_get_coord.status_code == 200
    nomina_coord = resp_get_coord.json()
    assert nomina_coord[0]["numero_documento"] == "••••6655"

    # PUT desde coordinación -> 403 SIN_PERMISO
    resp_coord_put = client.put(
        f"/api/v1/eventos/{evento.id}/inscripciones/{inscripcion.id}/asistencia",
        json={"estado": "presente"},
        headers=ORIGEN,
    )
    assert resp_coord_put.status_code == 403
    assert resp_coord_put.json()["error"]["codigo"] == CodigosError.SIN_PERMISO


def test_api_rechaza_evento_no_iniciado_y_organizador_ajeno(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """Verifica 409 antes del inicio del evento, 404 cruzado y 403 de otro organizador."""
    org, part, evento_futuro, insc_futura = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
        inicio_offset_horas=4,
        fin_offset_horas=6,
    )
    otro_org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Org Ajeno")
    _org2, _p2, otro_evento, insc_otro_evento = _crear_evento_y_participante(
        db_session,
        crear_usuario_factory,
    )

    _login(client, org)
    # Antes de fecha_inicio -> 409 ASISTENCIA_NO_PERMITIDA
    resp_futuro = client.put(
        f"/api/v1/eventos/{evento_futuro.id}/inscripciones/{insc_futura.id}/asistencia",
        json={"estado": "presente"},
        headers=ORIGEN,
    )
    assert resp_futuro.status_code == 409
    assert resp_futuro.json()["error"]["codigo"] == CodigosError.ASISTENCIA_NO_PERMITIDA

    # Inscripción de otro evento -> 404 INSCRIPCION_NO_ENCONTRADA
    resp_cruzado = client.put(
        f"/api/v1/eventos/{evento_futuro.id}/inscripciones/{insc_otro_evento.id}/asistencia",
        json={"estado": "presente"},
        headers=ORIGEN,
    )
    assert resp_cruzado.status_code == 404
    assert resp_cruzado.json()["error"]["codigo"] == CodigosError.INSCRIPCION_NO_ENCONTRADA

    # Organizador ajeno -> 403
    _login(client, otro_org)
    assert client.get(f"/api/v1/eventos/{evento_futuro.id}/asistencia").status_code == 403
    assert (
        client.put(
            f"/api/v1/eventos/{evento_futuro.id}/inscripciones/{insc_futura.id}/asistencia",
            json={"estado": "presente"},
            headers=ORIGEN,
        ).status_code
        == 403
    )

    # Participante -> 403
    _login(client, part)
    assert client.get(f"/api/v1/eventos/{evento_futuro.id}/asistencia").status_code == 403
    assert (
        client.put(
            f"/api/v1/eventos/{evento_futuro.id}/inscripciones/{insc_futura.id}/asistencia",
            json={"estado": "presente"},
            headers=ORIGEN,
        ).status_code
        == 403
    )
    _ = otro_evento


def test_vista_web_asistencia_y_js_sin_innerhtml(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """US4 / RNF: la vista web protege por sesión/rol y asistencia.js evita innerHTML."""
    org, part, evento, _insc = _crear_evento_y_participante(db_session, crear_usuario_factory)

    # Sin sesión -> redirige a /login
    sin_sesion = client.get(f"/eventos/{evento.id}/asistencia", follow_redirects=False)
    assert sin_sesion.status_code == 303
    assert sin_sesion.headers["location"] == "/login"

    # Participante -> 403
    _login(client, part)
    assert client.get(f"/eventos/{evento.id}/asistencia").status_code == 403

    # Organizador -> 200 HTML con script asistencia.js y enlace volver propio
    _login(client, org)
    vista = client.get(f"/eventos/{evento.id}/asistencia")
    assert vista.status_code == 200
    assert "/static/js/asistencia.js" in vista.text
    assert "tabla-responsiva" in vista.text
    assert 'href="/organizador/eventos"' in vista.text

    # Coordinación -> 200 HTML con enlace volver al consolidado
    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coord Web")
    _login(client, coord)
    vista_coord = client.get(f"/eventos/{evento.id}/asistencia")
    assert vista_coord.status_code == 200
    assert 'href="/coordinacion/consolidado"' in vista_coord.text

    contenido_js = Path("app/static/js/asistencia.js").read_text(encoding="utf-8")
    assert "innerHTML" not in contenido_js
    assert "limpiarAlerta: false" in contenido_js
