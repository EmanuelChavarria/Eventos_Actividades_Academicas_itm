"""Pruebas de integración de plataforma E1: health, web base, deps, conteo, seed y CLI."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.errors import CodigosError, Conflicto, NoAutenticado, NoAutorizado, ReglaNegocio
from app.models.enums import (
    EstadoEvento,
    EstadoInscripcion,
    Modalidad,
    PublicoObjetivo,
    Rol,
    TipoDocumento,
    TipoEvento,
)
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario
from app.repositories.inscripcion_repo import contar_activas, contar_activas_por_eventos
from scripts.crear_usuario import crear_personal
from scripts.seed import poblar_datos


def test_health_responde_ok_con_bd_activa(client: TestClient) -> None:
    """RNF-22: GET /health verifica conectividad con SQLite y claves foráneas."""
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "database": "ok"}


def test_web_base_docs_y_estaticos_sin_innerhtml(client: TestClient) -> None:
    """RF-27 / RF-28 / RNF-12: /, /docs y /static cargan con HTTP 200 y api.js es seguro."""
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200

    portada = client.get("/")
    assert portada.status_code == 200
    assert "/static/js/api.js" in portada.text
    assert "/static/css/styles.css" in portada.text

    js = client.get("/static/js/api.js")
    assert js.status_code == 200
    assert "innerHTML" not in js.text
    assert "America/Bogota" in js.text


def test_stubs_api_v1_responden_501_uniforme(client: TestClient) -> None:
    """RNF-07: los endpoints stub de E2-E7 devuelven 501 NO_IMPLEMENTADO uniforme."""
    rutas = [
        ("GET", "/api/v1/auth/yo"),
        ("POST", "/api/v1/eventos"),
        ("GET", "/api/v1/catalogo/eventos"),
        ("GET", "/api/v1/inscripciones/mias"),
        ("GET", "/api/v1/eventos/1/asistencia"),
        ("GET", "/api/v1/reportes/consolidado"),
    ]
    for metodo, ruta in rutas:
        resp = client.request(metodo, ruta)
        assert resp.status_code == 501
        cuerpo = resp.json()
        assert cuerpo["error"]["codigo"] == CodigosError.NO_IMPLEMENTADO


def test_deps_rechaza_sin_sesion_inactivo_y_rol_insuficiente(crear_usuario_factory) -> None:
    """RNF-06 / RF-03: get_current_user exige sesión activa y require_roles valida rol."""
    with pytest.raises(NoAutenticado) as exc_none:
        get_current_user(usuario=None)
    assert exc_none.value.codigo == CodigosError.CREDENCIALES_INVALIDAS

    inactivo = crear_usuario_factory(numero_documento="1000000301", activo=False)
    with pytest.raises(NoAutenticado):
        get_current_user(usuario=inactivo)

    participante = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="1000000302",
    )
    validador_org = require_roles(Rol.ORGANIZADOR)
    with pytest.raises(NoAutorizado) as exc_rol:
        validador_org(participante)
    assert exc_rol.value.codigo == CodigosError.SIN_PERMISO


def test_repositorio_contar_activas_ignora_canceladas(
    db_session: Session,
    usuario_organizador: Usuario,
    crear_usuario_factory,
) -> None:
    """RN-04 / CA-02: contar_activas y contar_activas_por_eventos cuentan solo activas."""
    inicio = datetime(2026, 12, 10, 14, 0, tzinfo=UTC)
    fin = inicio + timedelta(hours=2)
    limite = inicio - timedelta(days=1)

    ev1 = Evento(
        titulo="Evento Conteo 1",
        descripcion="Prueba conteo",
        tipo=TipoEvento.TALLER.value,
        fecha_inicio=inicio,
        fecha_fin=fin,
        fecha_limite_inscripcion=limite,
        lugar="Sala 1",
        modalidad=Modalidad.PRESENCIAL.value,
        publico_objetivo=PublicoObjetivo.TODOS.value,
        responsable_nombre="Resp",
        responsable_correo="resp@example.edu",
        cupo_maximo=10,
        estado=EstadoEvento.PUBLICADO.value,
        organizador_id=usuario_organizador.id,
    )
    ev2 = Evento(
        titulo="Evento Conteo 2",
        descripcion="Sin inscritos",
        tipo=TipoEvento.SEMINARIO.value,
        fecha_inicio=inicio,
        fecha_fin=fin,
        fecha_limite_inscripcion=limite,
        lugar="Sala 2",
        modalidad=Modalidad.VIRTUAL.value,
        publico_objetivo=PublicoObjetivo.TODOS.value,
        responsable_nombre="Resp",
        responsable_correo="resp@example.edu",
        cupo_maximo=10,
        estado=EstadoEvento.PUBLICADO.value,
        organizador_id=usuario_organizador.id,
    )
    db_session.add_all([ev1, ev2])
    db_session.commit()

    p1 = crear_usuario_factory(numero_documento="1000000401")
    p2 = crear_usuario_factory(numero_documento="1000000402")
    db_session.add_all(
        [
            Inscripcion(evento_id=ev1.id, participante_id=p1.id, estado=EstadoInscripcion.ACTIVA),
            Inscripcion(
                evento_id=ev1.id,
                participante_id=p2.id,
                estado=EstadoInscripcion.CANCELADA,
            ),
        ]
    )
    db_session.commit()

    assert contar_activas(db_session, ev1.id) == 1
    assert contar_activas(db_session, ev2.id) == 0
    assert contar_activas_por_eventos(db_session, [ev1.id, ev2.id]) == {
        ev1.id: 1,
        ev2.id: 0,
    }
    assert contar_activas_por_eventos(db_session, []) == {}


def test_seed_idempotente_y_cantidades_minimas(db_session: Session) -> None:
    """RF-29 / RNF-15: seed crea cantidades mínimas ficticias y no duplica al reejecutarse."""
    primero = poblar_datos(db_session)
    assert primero["usuarios_creados"] >= 9
    assert primero["eventos_creados"] >= 5

    coordinacion = db_session.execute(
        select(func.count(Usuario.id)).where(Usuario.rol == Rol.COORDINACION.value)
    ).scalar_one()
    organizadores = db_session.execute(
        select(func.count(Usuario.id)).where(Usuario.rol == Rol.ORGANIZADOR.value)
    ).scalar_one()
    participantes = db_session.execute(
        select(func.count(Usuario.id)).where(Usuario.rol == Rol.PARTICIPANTE.value)
    ).scalar_one()
    estados_eventos = set(db_session.execute(select(Evento.estado)).scalars().all())

    assert coordinacion >= 1
    assert organizadores >= 2
    assert participantes >= 6
    assert {
        EstadoEvento.BORRADOR.value,
        EstadoEvento.PUBLICADO.value,
        EstadoEvento.CANCELADO.value,
    }.issubset(estados_eventos)

    segundo = poblar_datos(db_session)
    assert segundo == {"usuarios_creados": 0, "eventos_creados": 0}


def test_crear_usuario_cli_y_rechazo_documento_duplicado(db_session: Session) -> None:
    """RF-04 / RN-13 / RN-14: crea personal con documento normalizado y rechaza duplicado."""
    creado = crear_personal(
        db_session,
        rol=Rol.ORGANIZADOR,
        tipo_documento=TipoDocumento.CC,
        numero_documento="900.123.456 ",
        nombre="Admin Nuevo",
        correo="admin.nuevo@example.edu",
        password="PasswordSegura123",
    )
    assert creado.numero_documento == "900123456"
    assert creado.tipo_participante is None

    with pytest.raises(Conflicto) as exc_dup:
        crear_personal(
            db_session,
            rol=Rol.COORDINACION,
            tipo_documento=TipoDocumento.CC,
            numero_documento="900123456",
            nombre="Otro Admin",
            correo="otro.admin@example.edu",
            password="PasswordSegura123",
        )
    assert exc_dup.value.codigo == CodigosError.DOCUMENTO_DUPLICADO

    with pytest.raises(ReglaNegocio):
        crear_personal(
            db_session,
            rol=Rol.PARTICIPANTE,
            tipo_documento=TipoDocumento.CC,
            numero_documento="900123457",
            nombre="No Personal",
            correo="part@example.edu",
            password="PasswordSegura123",
        )


def test_logging_omits_cookies_tokens_y_documentos(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """RNF-22 / RN-19: los logs de acceso omiten cookies, tokens y parámetros sensibles."""
    caplog.set_level(logging.INFO, logger="pf04.acceso")
    resp = client.get(
        "/health?documento=9988776655",
        headers={
            "Authorization": "Bearer secreto_jwt_no_loguear",
            "Cookie": "access_token=cookie_secreta_no_loguear",
        },
    )
    assert resp.status_code == 200
    texto_logs = caplog.text
    assert "GET /health -> 200" in texto_logs
    assert "9988776655" not in texto_logs
    assert "secreto_jwt_no_loguear" not in texto_logs
    assert "cookie_secreta_no_loguear" not in texto_logs


def test_scripts_certificados_existen_con_soporte_mkcert() -> None:
    """RNF-05: existen scripts de certificados TLS para Windows y Unix."""
    ps1 = Path("scripts/generar_certificados.ps1").read_text(encoding="utf-8")
    sh = Path("scripts/generar_certificados.sh").read_text(encoding="utf-8")
    assert "mkcert" in ps1 and "openssl" in ps1
    assert "mkcert" in sh and "openssl" in sh
