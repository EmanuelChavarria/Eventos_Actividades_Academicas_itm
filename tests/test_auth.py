"""Pruebas automatizadas de autenticación, registro, cookies JWT y rate limit (E2)."""

from __future__ import annotations

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import CodigosError
from app.models.enums import Rol, TipoDocumento, TipoParticipante
from app.models.usuario import Usuario


@pytest.fixture(autouse=True)
def _limpiar_rate_limit_si_existe() -> None:
    """Reinicia el contador en memoria de intentos fallidos entre pruebas si ya existe."""
    from app.core import security

    control = getattr(security, "control_intentos_login", None)
    if control is not None and hasattr(control, "reiniciar_todo"):
        control.reiniciar_todo()


def test_registro_exitoso_normaliza_documento_y_oculta_hash(
    client: TestClient,
    db_session: Session,
) -> None:
    """RF-01 / RN-14 / RN-21: el registro normaliza documento, cifra con argon2id y fuerza rol."""
    resp = client.post(
        "/api/v1/auth/registro",
        json={
            "tipo_documento": "CC",
            "numero_documento": " 1.001 234.567 ",
            "nombre": "  Ana Sofía Gómez  ",
            "correo": "ana.sofia@example.edu",
            "tipo_participante": "estudiante",
            "password": "ClaveSegura123!",
        },
    )
    assert resp.status_code == 201
    datos = resp.json()
    assert datos["tipo_documento"] == "CC"
    assert datos["numero_documento"] == "1001234567"
    assert datos["nombre"] == "Ana Sofía Gómez"
    assert datos["rol"] == Rol.PARTICIPANTE.value
    assert datos["tipo_participante"] == TipoParticipante.ESTUDIANTE.value
    assert datos["activo"] is True
    assert "hash_password" not in datos
    assert "password" not in datos

    usuario_bd = db_session.execute(
        select(Usuario).where(Usuario.numero_documento == "1001234567")
    ).scalar_one()
    assert usuario_bd.hash_password.startswith("$argon2id$")
    assert usuario_bd.rol == Rol.PARTICIPANTE.value


def test_registro_pasaporte_normaliza_mayusculas(client: TestClient) -> None:
    """RN-14: el pasaporte elimina espacios/puntos y pasa a mayúsculas."""
    resp = client.post(
        "/api/v1/auth/registro",
        json={
            "tipo_documento": "PAS",
            "numero_documento": " ab 12345 ",
            "nombre": "Carlos Méndez",
            "correo": "carlos.mendez@example.edu",
            "tipo_participante": "docente",
            "password": "ClaveSegura123!",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["numero_documento"] == "AB12345"


def test_registro_documento_duplicado_retorna_409_y_permite_otro_tipo_o_correo_igual(
    client: TestClient,
) -> None:
    """RN-13: (tipo, doc) único -> 409; distinto tipo o correo repetido -> 201."""
    payload_base = {
        "tipo_documento": "CC",
        "numero_documento": "1002223334",
        "nombre": "Laura Torres",
        "correo": "compartido@example.edu",
        "tipo_participante": "estudiante",
        "password": "ClaveSegura123!",
    }
    primero = client.post("/api/v1/auth/registro", json=payload_base)
    assert primero.status_code == 201

    duplicado = client.post(
        "/api/v1/auth/registro",
        json={**payload_base, "numero_documento": "1.002.223.334", "correo": "otro@example.edu"},
    )
    assert duplicado.status_code == 409
    error_dup = duplicado.json()["error"]
    assert error_dup["codigo"] == CodigosError.DOCUMENTO_DUPLICADO
    assert "1002223334" not in str(error_dup)

    otro_tipo = client.post(
        "/api/v1/auth/registro",
        json={
            **payload_base,
            "tipo_documento": "CE",
            "nombre": "Laura Extranjera",
        },
    )
    assert otro_tipo.status_code == 201


def test_registro_rechaza_entradas_invalidas_y_campo_rol_sin_input(client: TestClient) -> None:
    """RNF-02 / RNF-07 / RN-21: 422 sin campo input por formato o campo extra."""
    casos = [
        {
            "tipo_documento": "CC",
            "numero_documento": "12AB56",
            "nombre": "Usuario Inválido",
            "correo": "valido@example.edu",
            "tipo_participante": "estudiante",
            "password": "ClaveSegura123!",
        },
        {
            "tipo_documento": "CC",
            "numero_documento": "1003334445",
            "nombre": "Usuario Clave Corta",
            "correo": "valido@example.edu",
            "tipo_participante": "estudiante",
            "password": "123",
        },
        {
            "tipo_documento": "CC",
            "numero_documento": "1003334446",
            "nombre": "Usuario Escalamiento",
            "correo": "valido@example.edu",
            "tipo_participante": "estudiante",
            "password": "ClaveSegura123!",
            "rol": "organizador",
        },
    ]
    for cuerpo in casos:
        resp = client.post("/api/v1/auth/registro", json=cuerpo)
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["codigo"] == CodigosError.ERROR_VALIDACION
        for detalle in data["error"]["detalles"]:
            assert "input" not in detalle


def test_login_exitoso_emite_cookie_segura_jwt_yo_y_logout_204(
    client: TestClient,
    crear_usuario_factory,
) -> None:
    """RF-02 / RNF-05: login emite cookie HttpOnly/SameSite=Lax/Secure/Max-Age=3600 con sub=id."""
    usuario = crear_usuario_factory(
        rol=Rol.ORGANIZADOR,
        tipo_documento=TipoDocumento.CC,
        numero_documento="1004445556",
        password="ClaveOrganizador123!",
    )

    resp_login = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": "CC",
            "numero_documento": "1.004.445.556",
            "password": "ClaveOrganizador123!",
        },
    )
    assert resp_login.status_code == 200
    cuerpo = resp_login.json()
    assert cuerpo["id"] == usuario.id
    assert "access_token" not in cuerpo
    assert "hash_password" not in cuerpo

    set_cookie = resp_login.headers.get("set-cookie", "")
    set_cookie_lower = set_cookie.lower()
    assert "httponly" in set_cookie_lower
    assert "samesite=lax" in set_cookie_lower
    assert "path=/" in set_cookie_lower
    assert "max-age=3600" in set_cookie_lower
    assert "secure" in set_cookie_lower

    valor_cookie = next(iter(client.cookies.values()))
    settings = get_settings()
    claims = jwt.decode(valor_cookie, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert claims["sub"] == str(usuario.id)
    assert "numero_documento" not in claims
    assert "correo" not in claims

    yo = client.get("/api/v1/auth/yo")
    assert yo.status_code == 200
    assert yo.json()["id"] == usuario.id
    assert yo.json()["rol"] == Rol.ORGANIZADOR.value

    logout = client.post("/api/v1/auth/logout", headers={"Origin": "https://testserver"})
    assert logout.status_code == 204

    yo_despues = client.get("/api/v1/auth/yo")
    assert yo_despues.status_code == 401
    assert yo_despues.json()["error"]["codigo"] == CodigosError.CREDENCIALES_INVALIDAS


def test_login_credenciales_invalidas_y_usuario_inactivo_retornan_401_uniforme(
    client: TestClient,
    crear_usuario_factory,
) -> None:
    """RF-02 / V: documento inexistente, clave errónea o usuario inactivo devuelven 401 uniforme."""
    crear_usuario_factory(
        numero_documento="1005556661",
        password="ClaveCorrecta123!",
        activo=True,
    )
    crear_usuario_factory(
        numero_documento="1005556662",
        password="ClaveCorrecta123!",
        activo=False,
    )

    resp_inexistente = client.post(
        "/api/v1/auth/login",
        json={"tipo_documento": "CC", "numero_documento": "9999999999", "password": "x"},
    )
    resp_clave_mal = client.post(
        "/api/v1/auth/login",
        json={"tipo_documento": "CC", "numero_documento": "1005556661", "password": "incorrecta"},
    )
    resp_inactivo = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": "CC",
            "numero_documento": "1005556662",
            "password": "ClaveCorrecta123!",
        },
    )

    for r in (resp_inexistente, resp_clave_mal, resp_inactivo):
        assert r.status_code == 401
        assert r.json()["error"]["codigo"] == CodigosError.CREDENCIALES_INVALIDAS

    assert resp_inexistente.json()["error"]["mensaje"] == resp_clave_mal.json()["error"]["mensaje"]
    assert resp_clave_mal.json()["error"]["mensaje"] == resp_inactivo.json()["error"]["mensaje"]


def test_login_bloquea_tras_10_intentos_fallidos_y_reinicia_al_exito(
    client: TestClient,
    crear_usuario_factory,
) -> None:
    """RNF-05: 10 fallos -> 429 en el intento 11; login exitoso previo reinicia."""
    crear_usuario_factory(numero_documento="1006667771", password="ClaveCorrecta123!")
    crear_usuario_factory(numero_documento="1006667772", password="ClaveCorrecta123!")

    for _ in range(10):
        resp = client.post(
            "/api/v1/auth/login",
            json={"tipo_documento": "CC", "numero_documento": "1006667771", "password": "mala"},
        )
        assert resp.status_code == 401

    bloqueado = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": "CC",
            "numero_documento": "1006667771",
            "password": "ClaveCorrecta123!",
        },
    )
    assert bloqueado.status_code == 429
    assert bloqueado.json()["error"]["codigo"] == CodigosError.DEMASIADOS_INTENTOS

    # Otro documento del mismo cliente sigue independiente y reinicia tras login exitoso.
    for _ in range(9):
        r = client.post(
            "/api/v1/auth/login",
            json={"tipo_documento": "CC", "numero_documento": "1006667772", "password": "mala"},
        )
        assert r.status_code == 401

    ok = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": "CC",
            "numero_documento": "1006667772",
            "password": "ClaveCorrecta123!",
        },
    )
    assert ok.status_code == 200
    assert (
        client.post("/api/v1/auth/logout", headers={"Origin": "https://testserver"}).status_code
        == 204
    )

    for _ in range(2):
        r2 = client.post(
            "/api/v1/auth/login",
            json={"tipo_documento": "CC", "numero_documento": "1006667772", "password": "mala"},
        )
        assert r2.status_code == 401


def test_vistas_login_registro_y_navegacion_por_rol(
    client: TestClient,
    crear_usuario_factory,
) -> None:
    """RF-03 / RF-27 / RNF-12: vistas auth, redirección si autenticado, menú por rol y JS seguro."""
    login_html = client.get("/login")
    assert login_html.status_code == 200
    assert 'id="form-login"' in login_html.text
    assert "/static/js/auth.js" in login_html.text

    registro_html = client.get("/registro")
    assert registro_html.status_code == 200
    assert 'id="form-registro"' in registro_html.text
    assert "/static/js/auth.js" in registro_html.text

    auth_js = client.get("/static/js/auth.js")
    assert auth_js.status_code == 200
    assert "innerHTML" not in auth_js.text

    api_js = client.get("/static/js/api.js")
    assert api_js.status_code == 200
    assert "innerHTML" not in api_js.text
    assert "/auth/logout" in api_js.text

    # Visitante anónimo ve enlaces de login/registro y no opciones autenticadas.
    inicio_anon = client.get("/")
    assert inicio_anon.status_code == 200
    assert 'href="/login"' in inicio_anon.text
    assert 'href="/registro"' in inicio_anon.text
    assert "btn-cerrar-sesion" not in inicio_anon.text

    casos_rol = [
        (Rol.PARTICIPANTE, "1008889991", "/mis-inscripciones", "/organizador/eventos"),
        (Rol.ORGANIZADOR, "1008889992", "/organizador/eventos", "/coordinacion/consolidado"),
        (Rol.COORDINACION, "1008889993", "/coordinacion/consolidado", "/mis-inscripciones"),
    ]
    for rol, doc, enlace_esperado, enlace_ajeno in casos_rol:
        crear_usuario_factory(rol=rol, numero_documento=doc, password="ClaveSegura123!")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"tipo_documento": "CC", "numero_documento": doc, "password": "ClaveSegura123!"},
        )
        assert login_resp.status_code == 200

        # Con sesión activa, /login y /registro redirigen 303 a /
        assert client.get("/login", follow_redirects=False).status_code == 303
        assert client.get("/registro", follow_redirects=False).status_code == 303

        inicio_auth = client.get("/")
        assert inicio_auth.status_code == 200
        assert enlace_esperado in inicio_auth.text
        assert enlace_ajeno not in inicio_auth.text
        assert "btn-cerrar-sesion" in inicio_auth.text

        logout = client.post("/api/v1/auth/logout", headers={"Origin": "https://testserver"})
        assert logout.status_code == 204
