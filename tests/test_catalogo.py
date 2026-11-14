"""Pruebas del catálogo público, filtros, paginación, detalle en tiempo real y 404 (E4)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import CodigosError
from app.core.fechas import ZONA_BOGOTA, ahora_utc
from app.models.enums import EstadoEvento, EstadoInscripcion, Rol
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario

_NOMBRE_COOKIE = "pf04_session"


def _autenticar(client: TestClient, usuario: Usuario) -> None:
    """Inyecta cookie JWT para validar respuestas ante usuarios autenticados."""
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


def _crear_evento(
    db_session: Session,
    organizador: Usuario,
    *,
    titulo: str,
    estado: str = EstadoEvento.PUBLICADO.value,
    tipo: str = "seminario",
    modalidad: str = "presencial",
    dias_inicio: int = 5,
    duracion_horas: int = 3,
    limite_offset_horas: int = -12,
    cupo_maximo: int = 20,
    descripcion: str = "Descripción académica de prueba para el catálogo público.",
    lugar: str = "Auditorio Principal",
) -> Evento:
    """Crea un evento directamente en BD para pruebas del catálogo."""
    inicio = ahora_utc() + timedelta(days=dias_inicio)
    fin = inicio + timedelta(hours=duracion_horas)
    limite = inicio + timedelta(hours=limite_offset_horas)
    evento = Evento(
        titulo=titulo,
        descripcion=descripcion,
        tipo=tipo,
        fecha_inicio=inicio,
        fecha_fin=fin,
        fecha_limite_inscripcion=limite,
        lugar=lugar,
        modalidad=modalidad,
        publico_objetivo="todos",
        ponente="Dra. Camila Rojas",
        requisitos=None,
        responsable_nombre="Coordinación Académica",
        responsable_correo="eventos@ejemplo.edu",
        cupo_maximo=cupo_maximo,
        estado=estado,
        organizador_id=organizador.id,
    )
    db_session.add(evento)
    db_session.commit()
    db_session.refresh(evento)
    return evento


def test_catalogo_lista_solo_publicados_vigentes_orden_estable_y_paginacion(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
) -> None:
    """RF-11 / RN-01: expone solo publicados vigentes por defecto, ordenados y paginados."""
    _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Borrador oculto",
        estado=EstadoEvento.BORRADOR.value,
        dias_inicio=3,
    )
    _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Cancelado oculto",
        estado=EstadoEvento.CANCELADO.value,
        dias_inicio=4,
    )
    _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Publicado finalizado",
        estado=EstadoEvento.PUBLICADO.value,
        dias_inicio=-4,
        duracion_horas=2,
    )
    _crear_evento(db_session, usuario_organizador, titulo="Evento Tardío", dias_inicio=10)
    _crear_evento(db_session, usuario_organizador, titulo="Evento Próximo", dias_inicio=2)
    _crear_evento(db_session, usuario_organizador, titulo="Evento Medio", dias_inicio=6)

    pag1 = client.get("/api/v1/catalogo/eventos", params={"pagina": 1, "tamano": 2})
    assert pag1.status_code == 200
    datos1 = pag1.json()
    assert datos1["total"] == 3
    assert datos1["pagina"] == 1
    assert datos1["tamano"] == 2
    assert datos1["total_paginas"] == 2
    assert [ev["titulo"] for ev in datos1["items"]] == ["Evento Próximo", "Evento Medio"]
    assert "organizador_id" not in datos1["items"][0]
    assert "motivo_cancelacion" not in datos1["items"][0]

    pag2 = client.get("/api/v1/catalogo/eventos", params={"pagina": 2, "tamano": 2})
    assert pag2.status_code == 200
    assert [ev["titulo"] for ev in pag2.json()["items"]] == ["Evento Tardío"]

    pag_vacia = client.get("/api/v1/catalogo/eventos", params={"pagina": 3, "tamano": 2})
    assert pag_vacia.status_code == 200
    assert pag_vacia.json()["items"] == []
    assert pag_vacia.json()["total"] == 3

    con_finalizados = client.get(
        "/api/v1/catalogo/eventos",
        params={"incluir_finalizados": True, "tamano": 10},
    )
    assert con_finalizados.status_code == 200
    items_fin = con_finalizados.json()["items"]
    assert len(items_fin) == 4
    por_titulo = {item["titulo"]: item for item in items_fin}
    assert por_titulo["Publicado finalizado"]["estado_efectivo"] == "finalizado"
    assert por_titulo["Publicado finalizado"]["inscripciones_abiertas"] is False


def test_catalogo_filtra_por_tipo_modalidad_fechas_y_texto_con_comodines(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
) -> None:
    """RF-11 / RNF-08: filtros combinables y escape literal de `%` y `_` en búsqueda."""
    ev_100 = _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Taller 100% Python",
        tipo="taller",
        modalidad="presencial",
        dias_inicio=4,
    )
    _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Taller normal python_3",
        tipo="taller",
        modalidad="virtual",
        dias_inicio=7,
    )
    _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Conferencia de Java",
        tipo="conferencia",
        modalidad="presencial",
        dias_inicio=15,
    )

    resp_combo = client.get(
        "/api/v1/catalogo/eventos",
        params={"tipo": "taller", "modalidad": "presencial"},
    )
    assert resp_combo.status_code == 200
    assert [ev["id"] for ev in resp_combo.json()["items"]] == [ev_100.id]

    desde = (ahora_utc() + timedelta(days=3)).astimezone(ZONA_BOGOTA).isoformat()
    hasta = (ahora_utc() + timedelta(days=8)).astimezone(ZONA_BOGOTA).isoformat()
    resp_fechas = client.get(
        "/api/v1/catalogo/eventos",
        params={"fecha_desde": desde, "fecha_hasta": hasta},
    )
    assert resp_fechas.status_code == 200
    titulos_rango = [ev["titulo"] for ev in resp_fechas.json()["items"]]
    assert titulos_rango == ["Taller 100% Python", "Taller normal python_3"]

    resp_porcentaje = client.get("/api/v1/catalogo/eventos", params={"texto": "100%"})
    assert resp_porcentaje.status_code == 200
    assert [ev["titulo"] for ev in resp_porcentaje.json()["items"]] == ["Taller 100% Python"]

    resp_guion = client.get("/api/v1/catalogo/eventos", params={"texto": "python_3"})
    assert resp_guion.status_code == 200
    assert [ev["titulo"] for ev in resp_guion.json()["items"]] == ["Taller normal python_3"]


def test_catalogo_rechaza_parametros_invalidos_con_422(client: TestClient) -> None:
    """RNF-02 / RN-18: rechaza paginación inválida, fechas naive o rango invertido."""
    fecha_a = "2028-06-10T10:00:00-05:00"
    fecha_b = "2028-06-05T10:00:00-05:00"
    casos = [
        {"pagina": 0},
        {"tamano": 0},
        {"tamano": 51},
        {"tipo": "inexistente"},
        {"fecha_desde": "2028-06-10T10:00:00"},
    ]

    resp_invertido = client.get(
        "/api/v1/catalogo/eventos",
        params={"fecha_desde": fecha_a, "fecha_hasta": fecha_b},
    )
    assert resp_invertido.status_code == 422

    for params in casos:
        resp = client.get("/api/v1/catalogo/eventos", params=params)
        assert resp.status_code == 422
        error = resp.json()["error"]
        assert error["codigo"] in {CodigosError.ERROR_VALIDACION, CodigosError.REGLA_NEGOCIO}
        for detalle in error["detalles"]:
            assert "input" not in detalle


def test_detalle_catalogo_calcula_cupos_disponibles_en_tiempo_real(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
    usuario_organizador: Usuario,
) -> None:
    """RF-12 / CA-02: cupos disponibles e inscripciones_abiertas reflejan el estado real en BD."""
    evento = _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Seminario en tiempo real",
        cupo_maximo=10,
        dias_inicio=5,
        limite_offset_horas=-2,
    )
    p1 = crear_usuario_factory(numero_documento="8500001001", rol=Rol.PARTICIPANTE)
    p2 = crear_usuario_factory(numero_documento="8500001002", rol=Rol.PARTICIPANTE)
    p3 = crear_usuario_factory(numero_documento="8500001003", rol=Rol.PARTICIPANTE)

    insc1 = Inscripcion(
        evento_id=evento.id,
        participante_id=p1.id,
        estado=EstadoInscripcion.ACTIVA.value,
    )
    db_session.add_all(
        [
            insc1,
            Inscripcion(
                evento_id=evento.id,
                participante_id=p2.id,
                estado=EstadoInscripcion.ACTIVA.value,
            ),
            Inscripcion(
                evento_id=evento.id,
                participante_id=p3.id,
                estado=EstadoInscripcion.CANCELADA.value,
            ),
        ]
    )
    db_session.commit()

    det1 = client.get(f"/api/v1/catalogo/eventos/{evento.id}")
    assert det1.status_code == 200
    datos1 = det1.json()
    assert datos1["cupo_maximo"] == 10
    assert datos1["inscripciones_activas"] == 2
    assert datos1["cupos_disponibles"] == 8
    assert datos1["inscripciones_abiertas"] is True
    assert datos1["estado_efectivo"] == "publicado"

    insc1.estado = EstadoInscripcion.CANCELADA.value
    insc1.cancelada_en = ahora_utc()
    db_session.commit()

    det2 = client.get(f"/api/v1/catalogo/eventos/{evento.id}")
    assert det2.status_code == 200
    assert det2.json()["inscripciones_activas"] == 1
    assert det2.json()["cupos_disponibles"] == 9

    ev_finalizado = _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Evento ya finalizado",
        dias_inicio=-3,
        duracion_horas=2,
    )
    det_fin = client.get(f"/api/v1/catalogo/eventos/{ev_finalizado.id}")
    assert det_fin.status_code == 200
    assert det_fin.json()["estado_efectivo"] == "finalizado"
    assert det_fin.json()["inscripciones_abiertas"] is False

    ev_cierre = _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Inscripciones ya cerradas",
        dias_inicio=1,
        limite_offset_horas=-48,
    )
    det_cierre = client.get(f"/api/v1/catalogo/eventos/{ev_cierre.id}")
    assert det_cierre.status_code == 200
    assert det_cierre.json()["inscripciones_abiertas"] is False


def test_detalle_catalogo_retorna_404_si_inexistente_o_no_publicado(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
) -> None:
    """RF-13 / PF-04: inexistente, borrador y cancelado responden 404 EVENTO_NO_ENCONTRADO."""
    ev_borrador = _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Borrador privado",
        estado=EstadoEvento.BORRADOR.value,
    )
    ev_cancelado = _crear_evento(
        db_session,
        usuario_organizador,
        titulo="Cancelado privado",
        estado=EstadoEvento.CANCELADO.value,
    )

    for url in (
        "/api/v1/catalogo/eventos/999999",
        f"/api/v1/catalogo/eventos/{ev_borrador.id}",
        f"/api/v1/catalogo/eventos/{ev_cancelado.id}",
    ):
        resp = client.get(url)
        assert resp.status_code == 404
        assert resp.json()["error"]["codigo"] == CodigosError.EVENTO_NO_ENCONTRADO

    _autenticar(client, usuario_organizador)
    assert client.get(f"/api/v1/catalogo/eventos/{ev_borrador.id}").status_code == 404
    assert client.get(f"/api/v1/catalogo/eventos/{ev_cancelado.id}").status_code == 404
