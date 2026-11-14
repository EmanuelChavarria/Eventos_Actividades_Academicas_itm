"""Pruebas de gestión del ciclo de vida y reglas de negocio de eventos (E3)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import CodigosError
from app.core.fechas import ZONA_BOGOTA, ahora_utc
from app.models.enums import EstadoEvento, EstadoInscripcion, Rol
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario

_NOMBRE_COOKIE = "pf04_session"
_ORIGEN_VALIDO = {"Origin": "https://testserver"}


def _autenticar_usuario(client: TestClient, usuario: Usuario) -> None:
    """Inyecta cookie JWT válida para el usuario indicado."""
    settings = get_settings()
    ahora = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(usuario.id),
            "iat": int(ahora.timestamp()),
            "exp": int((ahora + timedelta(minutes=60)).timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    client.cookies.set(_NOMBRE_COOKIE, token)


def _payload_evento(
    *,
    dias_inicio: int = 5,
    cupo_maximo: int = 30,
    **sobrescribir: Any,
) -> dict[str, Any]:
    """Construye un payload válido de creación de evento con fechas en America/Bogota."""
    inicio = (ahora_utc() + timedelta(days=dias_inicio)).astimezone(ZONA_BOGOTA)
    fin = inicio + timedelta(hours=3)
    limite = inicio - timedelta(days=1)
    datos: dict[str, Any] = {
        "titulo": "Seminario de Arquitectura Limpia",
        "descripcion": "Sesión académica práctica sobre diseño modular con FastAPI y SQLite.",
        "tipo": "seminario",
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
        "fecha_limite_inscripcion": limite.isoformat(),
        "lugar": "Auditorio Central",
        "modalidad": "presencial",
        "publico_objetivo": "todos",
        "ponente": "Dra. Ana Torres",
        "requisitos": "Portátil opcional",
        "responsable_nombre": "Carlos Pérez",
        "responsable_correo": "carlos.perez@ejemplo.edu",
        "cupo_maximo": cupo_maximo,
    }
    datos.update(sobrescribir)
    return datos


def _crear_evento_bd(
    db_session: Session,
    organizador: Usuario,
    *,
    estado: str = EstadoEvento.BORRADOR.value,
    dias_inicio: int = 5,
    duracion_horas: int = 3,
    cupo_maximo: int = 20,
    titulo: str = "Evento de prueba en BD",
) -> Evento:
    """Inserta directamente un evento en BD para preparar escenarios de regla."""
    inicio = ahora_utc() + timedelta(days=dias_inicio)
    fin = inicio + timedelta(hours=duracion_horas)
    limite = inicio - timedelta(hours=12)
    evento = Evento(
        titulo=titulo,
        descripcion="Descripción válida suficientemente extensa para pruebas automatizadas.",
        tipo="taller",
        fecha_inicio=inicio,
        fecha_fin=fin,
        fecha_limite_inscripcion=limite,
        lugar="Bloque C - Aula 204",
        modalidad="presencial",
        publico_objetivo="todos",
        ponente="Ing. Laura Gómez",
        requisitos=None,
        responsable_nombre="Responsable Base",
        responsable_correo="responsable@ejemplo.edu",
        cupo_maximo=cupo_maximo,
        estado=estado,
        organizador_id=organizador.id,
    )
    db_session.add(evento)
    db_session.commit()
    db_session.refresh(evento)
    return evento


def _registrar_inscripciones(
    db_session: Session,
    crear_usuario_factory,
    evento_id: int,
    *,
    activas: int,
    canceladas: int = 0,
    prefijo_doc: str = "810000",
) -> None:
    """Crea inscripciones reales en BD para verificar cálculo de ocupación y RN-09."""
    total = activas + canceladas
    for idx in range(total):
        participante = crear_usuario_factory(
            numero_documento=f"{prefijo_doc}{evento_id}{idx:02d}",
            rol=Rol.PARTICIPANTE,
        )
        estado = (
            EstadoInscripcion.ACTIVA.value if idx < activas else EstadoInscripcion.CANCELADA.value
        )
        db_session.add(
            Inscripcion(
                evento_id=evento_id,
                participante_id=participante.id,
                estado=estado,
            )
        )
    db_session.commit()


def test_crear_evento_borrador_valido_retorna_201_y_persiste_utc(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
) -> None:
    """RF-05 / CA-01 / RN-18: crea borrador, retorna 201 y normaliza fechas a UTC."""
    _autenticar_usuario(client, usuario_organizador)
    resp = client.post("/api/v1/eventos", json=_payload_evento(), headers=_ORIGEN_VALIDO)
    assert resp.status_code == 201

    cuerpo = resp.json()
    assert cuerpo["estado"] == "borrador"
    assert cuerpo["estado_efectivo"] == "borrador"
    assert cuerpo["organizador_id"] == usuario_organizador.id
    assert cuerpo["inscripciones_activas"] == 0
    assert cuerpo["cupos_disponibles"] == 30
    assert cuerpo["inscripciones_abiertas"] is False

    evento_bd = db_session.get(Evento, cuerpo["id"])
    assert evento_bd is not None
    assert evento_bd.estado == "borrador"
    assert evento_bd.fecha_inicio.tzinfo == UTC
    assert evento_bd.fecha_fin.tzinfo == UTC


def test_crear_evento_invalido_retorna_422_sin_persistir(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
) -> None:
    """PF-02 / RN-02 / RN-03 / RN-18: rechaza 422 sin guardar registros ni filtrar input."""
    _autenticar_usuario(client, usuario_organizador)
    inicio = datetime(2028, 5, 10, 14, 0, tzinfo=ZONA_BOGOTA)

    casos_invalidos = [
        _payload_evento(fecha_inicio="2028-05-10T14:00:00"),
        _payload_evento(cupo_maximo=0),
        _payload_evento(titulo="  "),
        _payload_evento(
            fecha_inicio=inicio.isoformat(),
            fecha_fin=(inicio - timedelta(hours=1)).isoformat(),
            fecha_limite_inscripcion=(inicio - timedelta(days=1)).isoformat(),
        ),
        _payload_evento(
            fecha_inicio=inicio.isoformat(),
            fecha_fin=(inicio + timedelta(hours=2)).isoformat(),
            fecha_limite_inscripcion=(inicio + timedelta(minutes=1)).isoformat(),
        ),
        _payload_evento(campo_no_permitido="valor"),
    ]

    for payload in casos_invalidos:
        resp = client.post("/api/v1/eventos", json=payload, headers=_ORIGEN_VALIDO)
        assert resp.status_code == 422
        error = resp.json()["error"]
        assert error["codigo"] == CodigosError.ERROR_VALIDACION
        for detalle in error["detalles"]:
            assert "input" not in detalle

    total_eventos = db_session.scalar(select(func.count()).select_from(Evento))
    assert total_eventos == 0


def test_publicar_evento_borrador_y_rechazos_estado_o_fecha_pasada(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
) -> None:
    """RF-06 / RN-12 / RN-20: publica directo desde borrador y rechaza no borrador o pasado."""
    _autenticar_usuario(client, usuario_organizador)
    ev_futuro = _crear_evento_bd(db_session, usuario_organizador, dias_inicio=4)

    ok = client.post(f"/api/v1/eventos/{ev_futuro.id}/publicar", headers=_ORIGEN_VALIDO)
    assert ok.status_code == 200
    datos_ok = ok.json()
    assert datos_ok["estado"] == "publicado"
    assert datos_ok["estado_efectivo"] == "publicado"
    assert datos_ok["inscripciones_abiertas"] is True

    repetido = client.post(f"/api/v1/eventos/{ev_futuro.id}/publicar", headers=_ORIGEN_VALIDO)
    assert repetido.status_code == 409

    ev_pasado = _crear_evento_bd(db_session, usuario_organizador, dias_inicio=-2)
    rechazo_fecha = client.post(f"/api/v1/eventos/{ev_pasado.id}/publicar", headers=_ORIGEN_VALIDO)
    assert rechazo_fecha.status_code == 422
    assert rechazo_fecha.json()["error"]["codigo"] == CodigosError.REGLA_NEGOCIO
    db_session.refresh(ev_pasado)
    assert ev_pasado.estado == "borrador"


def test_editar_evento_parcial_y_control_cupo_minimo_rn09(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
    usuario_organizador: Usuario,
) -> None:
    """RF-07 / CA-04 / RN-03 / RN-09: edición parcial y límite mínimo de cupo frente a activas."""
    _autenticar_usuario(client, usuario_organizador)
    evento = _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=7,
        cupo_maximo=10,
    )
    _registrar_inscripciones(
        db_session,
        crear_usuario_factory,
        evento.id,
        activas=3,
        canceladas=1,
        prefijo_doc="820000",
    )

    subir = client.patch(
        f"/api/v1/eventos/{evento.id}",
        json={"cupo_maximo": 20, "titulo": "Seminario Actualizado"},
        headers=_ORIGEN_VALIDO,
    )
    assert subir.status_code == 200
    assert subir.json()["cupo_maximo"] == 20
    assert subir.json()["inscripciones_activas"] == 3
    assert subir.json()["cupos_disponibles"] == 17

    igual_activas = client.patch(
        f"/api/v1/eventos/{evento.id}",
        json={"cupo_maximo": 3},
        headers=_ORIGEN_VALIDO,
    )
    assert igual_activas.status_code == 200
    assert igual_activas.json()["cupos_disponibles"] == 0

    bajo_activas = client.patch(
        f"/api/v1/eventos/{evento.id}",
        json={"cupo_maximo": 2},
        headers=_ORIGEN_VALIDO,
    )
    assert bajo_activas.status_code == 409
    db_session.refresh(evento)
    assert evento.cupo_maximo == 3

    # Edición parcial de fecha_fin <= fecha_inicio existente en BD -> 422
    fin_invalido = (evento.fecha_inicio - timedelta(minutes=30)).astimezone(ZONA_BOGOTA).isoformat()
    resp_fin = client.patch(
        f"/api/v1/eventos/{evento.id}",
        json={"fecha_fin": fin_invalido},
        headers=_ORIGEN_VALIDO,
    )
    assert resp_fin.status_code == 422

    # Edición parcial de fecha_limite_inscripcion > fecha_inicio existente -> 422
    limite_invalido = (
        (evento.fecha_inicio + timedelta(minutes=30)).astimezone(ZONA_BOGOTA).isoformat()
    )
    resp_limite = client.patch(
        f"/api/v1/eventos/{evento.id}",
        json={"fecha_limite_inscripcion": limite_invalido},
        headers=_ORIGEN_VALIDO,
    )
    assert resp_limite.status_code == 422


def test_editar_evento_cancelado_o_finalizado_retorna_409(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
) -> None:
    """RF-07 / RN-09: bloquea edición de eventos cancelados o ya finalizados."""
    _autenticar_usuario(client, usuario_organizador)

    ev_cancelado = _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.CANCELADO.value,
        dias_inicio=6,
    )
    ev_finalizado = _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=-3,
        duracion_horas=2,
    )

    resp_cancelado = client.patch(
        f"/api/v1/eventos/{ev_cancelado.id}",
        json={"cupo_maximo": 50},
        headers=_ORIGEN_VALIDO,
    )
    assert resp_cancelado.status_code == 409

    resp_finalizado = client.patch(
        f"/api/v1/eventos/{ev_finalizado.id}",
        json={"lugar": "Otro auditorio"},
        headers=_ORIGEN_VALIDO,
    )
    assert resp_finalizado.status_code == 409


def test_cancelar_evento_publicado_conserva_inscripciones_y_valida_motivo(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
    usuario_organizador: Usuario,
) -> None:
    """RF-08 / RN-11 / RN-12: cancela publicado con motivo y conserva inscripciones."""
    _autenticar_usuario(client, usuario_organizador)

    ev_publicado = _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=4,
    )
    _registrar_inscripciones(
        db_session,
        crear_usuario_factory,
        ev_publicado.id,
        activas=2,
        prefijo_doc="830000",
    )

    motivo_corto = client.post(
        f"/api/v1/eventos/{ev_publicado.id}/cancelar",
        json={"motivo": "  abc "},
        headers=_ORIGEN_VALIDO,
    )
    assert motivo_corto.status_code == 422

    ok = client.post(
        f"/api/v1/eventos/{ev_publicado.id}/cancelar",
        json={"motivo": "Suspensión por mantenimiento eléctrico"},
        headers=_ORIGEN_VALIDO,
    )
    assert ok.status_code == 200
    datos = ok.json()
    assert datos["estado"] == "cancelado"
    assert datos["estado_efectivo"] == "cancelado"
    assert datos["motivo_cancelacion"] == "Suspensión por mantenimiento eléctrico"
    assert datos["inscripciones_abiertas"] is False

    activas_despues = db_session.scalar(
        select(func.count())
        .select_from(Inscripcion)
        .where(
            Inscripcion.evento_id == ev_publicado.id,
            Inscripcion.estado == EstadoInscripcion.ACTIVA.value,
        )
    )
    assert activas_despues == 2

    re_cancelar = client.post(
        f"/api/v1/eventos/{ev_publicado.id}/cancelar",
        json={"motivo": "Intento repetido válido"},
        headers=_ORIGEN_VALIDO,
    )
    assert re_cancelar.status_code == 409

    ev_borrador = _crear_evento_bd(db_session, usuario_organizador, dias_inicio=4)
    assert (
        client.post(
            f"/api/v1/eventos/{ev_borrador.id}/cancelar",
            json={"motivo": "Motivo suficientemente largo"},
            headers=_ORIGEN_VALIDO,
        ).status_code
        == 409
    )

    ev_finalizado = _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=-2,
    )
    assert (
        client.post(
            f"/api/v1/eventos/{ev_finalizado.id}/cancelar",
            json={"motivo": "Motivo suficientemente largo"},
            headers=_ORIGEN_VALIDO,
        ).status_code
        == 409
    )


def test_listar_eventos_organizador_y_obtener_detalle_propio(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
    usuario_organizador: Usuario,
) -> None:
    """RF-09 / RF-10: lista solo eventos propios con estado efectivo finalizado y detalle propio."""
    otro_organizador = crear_usuario_factory(
        numero_documento="9001112221",
        rol=Rol.ORGANIZADOR,
        nombre="Otro Organizador",
    )
    ev_borrador = _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.BORRADOR.value,
        dias_inicio=5,
        titulo="Borrador A",
    )
    _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=6,
        titulo="Publicado A",
    )
    ev_finalizado = _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=-3,
        cupo_maximo=15,
        titulo="Finalizado A",
    )
    _registrar_inscripciones(
        db_session,
        crear_usuario_factory,
        ev_finalizado.id,
        activas=2,
        prefijo_doc="840000",
    )
    _crear_evento_bd(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.CANCELADO.value,
        dias_inicio=8,
        titulo="Cancelado A",
    )
    _crear_evento_bd(
        db_session,
        otro_organizador,
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=4,
        titulo="Ajeno B",
    )

    _autenticar_usuario(client, usuario_organizador)
    listado = client.get("/api/v1/organizador/eventos")
    assert listado.status_code == 200
    items = listado.json()
    assert len(items) == 4
    assert all(item["organizador_id"] == usuario_organizador.id for item in items)

    por_titulo = {item["titulo"]: item for item in items}
    assert por_titulo["Finalizado A"]["estado"] == "publicado"
    assert por_titulo["Finalizado A"]["estado_efectivo"] == "finalizado"
    assert por_titulo["Finalizado A"]["inscripciones_abiertas"] is False
    assert por_titulo["Finalizado A"]["inscripciones_activas"] == 2
    assert por_titulo["Finalizado A"]["cupos_disponibles"] == 13

    detalle = client.get(f"/api/v1/eventos/{ev_borrador.id}")
    assert detalle.status_code == 200
    assert detalle.json()["titulo"] == "Borrador A"

    inexistente = client.get("/api/v1/eventos/999999")
    assert inexistente.status_code == 404
    assert inexistente.json()["error"]["codigo"] == CodigosError.EVENTO_NO_ENCONTRADO


def test_vistas_web_organizador_autorizacion_y_modulo_seguro(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
    usuario_participante: Usuario,
    usuario_coordinacion: Usuario,
) -> None:
    """HU-E3-05 / RNF-06 / RNF-12: rutas web organizador (303/403/200) y JS sin innerHTML."""
    evento = _crear_evento_bd(db_session, usuario_organizador)
    rutas = [
        "/organizador/eventos",
        "/organizador/eventos/nuevo",
        f"/organizador/eventos/{evento.id}/editar",
    ]

    for ruta in rutas:
        anonimo = client.get(ruta, follow_redirects=False)
        assert anonimo.status_code == 303
        assert anonimo.headers["location"] == "/login"

    for sin_permiso in (usuario_participante, usuario_coordinacion):
        _autenticar_usuario(client, sin_permiso)
        for ruta in rutas:
            assert client.get(ruta, follow_redirects=False).status_code == 403

    _autenticar_usuario(client, usuario_organizador)
    for ruta in rutas:
        ok = client.get(ruta, follow_redirects=False)
        assert ok.status_code == 200
        assert "/static/js/eventos.js" in ok.text

    js_resp = client.get("/static/js/eventos.js")
    assert js_resp.status_code == 200
    assert "innerHTML" not in js_resp.text
