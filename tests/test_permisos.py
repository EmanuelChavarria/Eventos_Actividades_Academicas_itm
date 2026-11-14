"""Pruebas automatizadas de autorización, estado activo, roles y defensa CSRF (E2)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import CodigosError, registrar_manejadores_errores
from app.core.fechas import ZONA_BOGOTA, ahora_utc
from app.models.enums import EstadoEvento, Rol
from app.models.evento import Evento
from app.models.usuario import Usuario

NOMBRE_COOKIE = "pf04_session"


def _emitir_jwt_prueba(
    sub: str | int,
    *,
    minutos_exp: int = 60,
    secreto: str | None = None,
    algoritmo: str | None = None,
) -> str:
    """Construye un JWT de prueba para validar decodificación y manejo de errores."""
    settings = get_settings()
    ahora = datetime.now(UTC)
    payload = {
        "sub": str(sub),
        "iat": int(ahora.timestamp()),
        "exp": int((ahora + timedelta(minutes=minutos_exp)).timestamp()),
    }
    return jwt.encode(
        payload,
        secreto or settings.SECRET_KEY,
        algorithm=algoritmo or settings.JWT_ALGORITHM,
    )


@pytest.fixture()
def client_permisos(db_session: Session) -> Generator[TestClient, None, None]:
    """App aislada con rutas de prueba protegidas por deps de API y web."""
    app_prueba = FastAPI()
    registrar_manejadores_errores(app_prueba)

    def _override_db() -> Generator[Session, None, None]:
        yield db_session

    app_prueba.dependency_overrides[get_db] = _override_db

    verificar_csrf = getattr(deps, "verificar_csrf", None)
    require_web_roles = getattr(deps, "require_web_roles", None)

    api_deps = [Depends(verificar_csrf)] if verificar_csrf is not None else []
    api_prueba = APIRouter(prefix="/api/v1", dependencies=api_deps)

    @api_prueba.get("/_prueba/solo-organizador")
    def _solo_org(
        usuario: Usuario = Depends(deps.require_roles(Rol.ORGANIZADOR)),
    ) -> dict[str, int | str]:
        return {"id": usuario.id, "rol": usuario.rol}

    @api_prueba.post("/_prueba/mutacion-organizador")
    def _mutacion_org(
        usuario: Usuario = Depends(deps.require_roles(Rol.ORGANIZADOR)),
    ) -> dict[str, int | str]:
        return {"ok": "si", "id": usuario.id}

    app_prueba.include_router(api_prueba)

    if require_web_roles is not None:

        @app_prueba.get("/_prueba/web-organizador")
        def _web_org(
            usuario: Usuario = Depends(require_web_roles(Rol.ORGANIZADOR)),
        ) -> dict[str, str]:
            return {"vista": "ok", "rol": usuario.rol}

    with TestClient(app_prueba, base_url="https://testserver") as tc:
        yield tc


def test_yo_rechaza_sin_cookie_expirada_alterada_o_usuario_inactivo(
    client: TestClient,
    crear_usuario_factory,
) -> None:
    """RF-03 / V: sin cookie, token expirado/alterado o usuario inactivo responden 401."""
    assert client.get("/api/v1/auth/yo").status_code == 401

    activo = crear_usuario_factory(numero_documento="1007778881", activo=True)
    inactivo = crear_usuario_factory(numero_documento="1007778882", activo=False)

    client.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(activo.id, minutos_exp=-5))
    assert client.get("/api/v1/auth/yo").status_code == 401

    client.cookies.set(
        NOMBRE_COOKIE,
        _emitir_jwt_prueba(activo.id, secreto="otra-clave-secreta-distinta-de-32-caracteres-xyz"),
    )
    assert client.get("/api/v1/auth/yo").status_code == 401

    client.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba("no-es-entero"))
    assert client.get("/api/v1/auth/yo").status_code == 401

    client.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(inactivo.id))
    resp_inactivo = client.get("/api/v1/auth/yo")
    assert resp_inactivo.status_code == 401
    assert resp_inactivo.json()["error"]["codigo"] == CodigosError.CREDENCIALES_INVALIDAS


def test_require_roles_retorna_401_403_y_200_segun_rol(
    client_permisos: TestClient,
    usuario_participante: Usuario,
    usuario_organizador: Usuario,
    usuario_coordinacion: Usuario,
) -> None:
    """RF-03 / RNF-06 / PF-09: sin sesión 401, rol insuficiente 403 SIN_PERMISO, permitido 200."""
    # Sin sesión
    sin_sesion = client_permisos.get("/api/v1/_prueba/solo-organizador")
    assert sin_sesion.status_code == 401
    assert sin_sesion.json()["error"]["codigo"] == CodigosError.CREDENCIALES_INVALIDAS

    # Rol participante en ruta de organizador -> 403
    client_permisos.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(usuario_participante.id))
    como_part = client_permisos.get("/api/v1/_prueba/solo-organizador")
    assert como_part.status_code == 403
    assert como_part.json()["error"]["codigo"] == CodigosError.SIN_PERMISO

    # Rol coordinación en ruta de organizador -> 403
    client_permisos.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(usuario_coordinacion.id))
    como_coord = client_permisos.get("/api/v1/_prueba/solo-organizador")
    assert como_coord.status_code == 403
    assert como_coord.json()["error"]["codigo"] == CodigosError.SIN_PERMISO

    # Rol organizador -> 200
    client_permisos.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(usuario_organizador.id))
    como_org = client_permisos.get("/api/v1/_prueba/solo-organizador")
    assert como_org.status_code == 200
    assert como_org.json()["id"] == usuario_organizador.id


def test_csrf_exige_origin_o_referer_valido_en_mutaciones_con_cookie(
    client: TestClient,
    client_permisos: TestClient,
    usuario_organizador: Usuario,
) -> None:
    """RNF-05: mutaciones con cookie sin Origin/Referer o con origen ajeno devuelven 403."""
    assert getattr(deps, "verificar_csrf", None) is not None

    token = _emitir_jwt_prueba(usuario_organizador.id)
    client_permisos.cookies.set(NOMBRE_COOKIE, token)

    sin_cabeceras = client_permisos.post("/api/v1/_prueba/mutacion-organizador")
    assert sin_cabeceras.status_code == 403
    assert sin_cabeceras.json()["error"]["codigo"] == CodigosError.SIN_PERMISO

    origen_malo = client_permisos.post(
        "/api/v1/_prueba/mutacion-organizador",
        headers={"Origin": "https://atacante.example"},
    )
    assert origen_malo.status_code == 403

    referer_malo = client_permisos.post(
        "/api/v1/_prueba/mutacion-organizador",
        headers={"Referer": "https://atacante.example/form"},
    )
    assert referer_malo.status_code == 403

    referer_valido = client_permisos.post(
        "/api/v1/_prueba/mutacion-organizador",
        headers={"Referer": "https://testserver/organizador/eventos"},
    )
    assert referer_valido.status_code == 200

    origen_valido = client_permisos.post(
        "/api/v1/_prueba/mutacion-organizador",
        headers={"Origin": "https://testserver"},
    )
    assert origen_valido.status_code == 200

    # También aplica sobre POST /api/v1/auth/logout cuando hay cookie
    client.cookies.set(NOMBRE_COOKIE, token)
    logout_sin_origen = client.post("/api/v1/auth/logout")
    assert logout_sin_origen.status_code == 403


def test_ruta_web_protegida_redirige_a_login_sin_sesion_y_rechaza_403_por_rol(
    client_permisos: TestClient,
    usuario_participante: Usuario,
    usuario_organizador: Usuario,
) -> None:
    """HU-E2-03: páginas protegidas redirigen 303 a /login sin sesión y 403 si rol no aplica."""
    assert getattr(deps, "require_web_roles", None) is not None

    anonimo = client_permisos.get("/_prueba/web-organizador", follow_redirects=False)
    assert anonimo.status_code == 303
    assert anonimo.headers["location"] == "/login"

    client_permisos.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(usuario_participante.id))
    sin_rol = client_permisos.get("/_prueba/web-organizador", follow_redirects=False)
    assert sin_rol.status_code == 403

    client_permisos.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(usuario_organizador.id))
    permitido = client_permisos.get("/_prueba/web-organizador", follow_redirects=False)
    assert permitido.status_code == 200


def _crear_evento_propietario(
    db_session: Session,
    organizador: Usuario,
    *,
    estado: str = EstadoEvento.BORRADOR.value,
) -> Evento:
    """Inserta un evento perteneciente al organizador indicado para pruebas de RN-10."""
    inicio = ahora_utc() + timedelta(days=5)
    evento = Evento(
        titulo="Evento de propiedad exclusiva",
        descripcion="Descripción de prueba para validar aislamiento entre organizadores.",
        tipo="conferencia",
        fecha_inicio=inicio,
        fecha_fin=inicio + timedelta(hours=2),
        fecha_limite_inscripcion=inicio - timedelta(days=1),
        lugar="Auditorio A",
        modalidad="presencial",
        publico_objetivo="todos",
        ponente="Ponente Invitado",
        requisitos=None,
        responsable_nombre="Responsable Evento",
        responsable_correo="responsable@ejemplo.edu",
        cupo_maximo=25,
        estado=estado,
        organizador_id=organizador.id,
    )
    db_session.add(evento)
    db_session.commit()
    db_session.refresh(evento)
    return evento


def test_endpoints_eventos_rechazan_sin_sesion_y_por_rol_e3(
    client: TestClient,
    db_session: Session,
    usuario_organizador: Usuario,
    usuario_participante: Usuario,
    usuario_coordinacion: Usuario,
) -> None:
    """RNF-06 / V: sin sesión responde 401; participante o coordinación reciben 403 SIN_PERMISO."""
    evento = _crear_evento_propietario(db_session, usuario_organizador)
    origen = {"Origin": "https://testserver"}
    inicio = (ahora_utc() + timedelta(days=6)).astimezone(ZONA_BOGOTA)
    payload_crear = {
        "titulo": "Taller sin permiso",
        "descripcion": "Descripción válida para probar autorización por rol en E3.",
        "tipo": "taller",
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": (inicio + timedelta(hours=2)).isoformat(),
        "fecha_limite_inscripcion": (inicio - timedelta(days=1)).isoformat(),
        "lugar": "Sala 1",
        "modalidad": "virtual",
        "publico_objetivo": "todos",
        "responsable_nombre": "Coord",
        "responsable_correo": "coord@ejemplo.edu",
        "cupo_maximo": 10,
    }

    rutas = [
        ("GET", "/api/v1/organizador/eventos", None),
        ("POST", "/api/v1/eventos", payload_crear),
        ("GET", f"/api/v1/eventos/{evento.id}", None),
        ("PATCH", f"/api/v1/eventos/{evento.id}", {"titulo": "Intento"}),
        ("POST", f"/api/v1/eventos/{evento.id}/publicar", None),
        ("POST", f"/api/v1/eventos/{evento.id}/cancelar", {"motivo": "Intento sin permiso"}),
    ]

    for metodo, url, body in rutas:
        kwargs = {"json": body} if body is not None else {}
        resp = client.request(metodo, url, **kwargs)
        assert resp.status_code == 401
        assert resp.json()["error"]["codigo"] == CodigosError.CREDENCIALES_INVALIDAS

    for usuario_sin_rol in (usuario_participante, usuario_coordinacion):
        client.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(usuario_sin_rol.id))
        for metodo, url, body in rutas:
            kwargs = {"json": body, "headers": origen} if metodo != "GET" else {}
            resp = client.request(metodo, url, **kwargs)
            assert resp.status_code == 403
            assert resp.json()["error"]["codigo"] == CodigosError.SIN_PERMISO


def test_organizador_ajeno_recibe_403_en_eventos_de_otro_propietario(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
    usuario_organizador: Usuario,
) -> None:
    """PF-09 / RN-10: otro organizador recibe 403 al leer, editar, publicar o cancelar."""
    otro_org = crear_usuario_factory(
        numero_documento="9005556661",
        rol=Rol.ORGANIZADOR,
        nombre="Organizador Ajeno",
    )
    ev_borrador = _crear_evento_propietario(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.BORRADOR.value,
    )
    ev_publicado = _crear_evento_propietario(
        db_session,
        usuario_organizador,
        estado=EstadoEvento.PUBLICADO.value,
    )

    origen = {"Origin": "https://testserver"}
    client.cookies.set(NOMBRE_COOKIE, _emitir_jwt_prueba(otro_org.id))

    for resp in (
        client.get(f"/api/v1/eventos/{ev_borrador.id}"),
        client.patch(
            f"/api/v1/eventos/{ev_borrador.id}",
            json={"titulo": "Alterado"},
            headers=origen,
        ),
        client.post(f"/api/v1/eventos/{ev_borrador.id}/publicar", headers=origen),
        client.post(
            f"/api/v1/eventos/{ev_publicado.id}/cancelar",
            json={"motivo": "Motivo no autorizado"},
            headers=origen,
        ),
    ):
        assert resp.status_code == 403
        assert resp.json()["error"]["codigo"] == CodigosError.SIN_PERMISO

    db_session.refresh(ev_borrador)
    db_session.refresh(ev_publicado)
    assert ev_borrador.titulo == "Evento de propiedad exclusiva"
    assert ev_borrador.estado == EstadoEvento.BORRADOR.value
    assert ev_publicado.estado == EstadoEvento.PUBLICADO.value
