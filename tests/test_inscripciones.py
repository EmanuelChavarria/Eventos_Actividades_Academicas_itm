"""Pruebas automatizadas de inscripciones y control atomico de cupos (E5).

Cubre RF-14..RF-19, RN-04..RN-07, RN-11, RNF-03, RNF-04, RNF-06, RNF-08.
Incluye prueba de concurrencia con hilos (PF-07) sobre INSERT condicional
BEGIN IMMEDIATE para garantizar cero sobrecupos.
"""

from __future__ import annotations

import concurrent.futures
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import CodigosError
from app.core.fechas import ahora_utc
from app.models.enums import (
    EstadoEvento,
    EstadoInscripcion,
    PublicoObjetivo,
    Rol,
    TipoDocumento,
)
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario
from app.repositories import inscripcion_repo
from app.services import inscripcion_service

# ---------------------------------------------------------------------------
# Helpers de prueba
# ---------------------------------------------------------------------------


def _crear_organizador_dummy(db: Session) -> Usuario:
    """Crea un organizador ficticio en la BD para usarlo como organizador_id de eventos."""
    from argon2 import PasswordHasher

    hasher = PasswordHasher()
    usuario = Usuario(
        tipo_documento=TipoDocumento.CC.value,
        numero_documento="9000000001",
        nombre="Organizador Dummy",
        correo="organizador.dummy@example.edu",
        tipo_participante=None,
        hash_password=hasher.hash("ClaveSegura123!"),
        rol=Rol.ORGANIZADOR.value,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def _crear_evento(
    db: Session,
    *,
    titulo: str = "Evento de prueba",
    cupo_maximo: int = 10,
    estado: str = EstadoEvento.PUBLICADO.value,
    publico_objetivo: str = PublicoObjetivo.TODOS.value,
    dias_limite: int = 7,
    dias_inicio: int = 14,
    organizador_id: int | None = None,
) -> Evento:
    """Crea un evento en la BD temporal para pruebas de inscripcion."""
    if organizador_id is None:
        org = _crear_organizador_dummy(db)
        organizador_id = org.id
    ahora = ahora_utc()
    evento = Evento(
        titulo=titulo,
        descripcion="Descripcion del evento de prueba",
        tipo="conferencia",
        fecha_inicio=ahora + timedelta(days=dias_inicio),
        fecha_fin=ahora + timedelta(days=dias_inicio + 1),
        fecha_limite_inscripcion=ahora + timedelta(days=dias_limite),
        lugar="Auditorio Principal",
        modalidad="presencial",
        publico_objetivo=publico_objetivo,
        responsable_nombre="Responsable Prueba",
        responsable_correo="responsable@example.edu",
        cupo_maximo=cupo_maximo,
        estado=estado,
        organizador_id=organizador_id,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


def _login_participante(client: TestClient, usuario: Usuario) -> None:
    """Inicia sesion del participante para obtener cookie JWT."""
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": usuario.tipo_documento,
            "numero_documento": usuario.numero_documento,
            "password": "ClaveSegura123!",
        },
        headers={"Origin": "https://testserver"},
    )
    assert resp.status_code == 200, f"Login fallo: {resp.text}"


def _inscribirse(client: TestClient, evento_id: int):
    """Realiza POST de inscripcion con cabecera CSRF."""
    return client.post(
        f"/api/v1/eventos/{evento_id}/inscripciones",
        headers={"Origin": "https://testserver"},
    )


def _cancelar(client: TestClient, inscripcion_id: int):
    """Realiza PATCH de cancelacion con cabecera CSRF."""
    return client.patch(
        f"/api/v1/inscripciones/{inscripcion_id}/cancelar",
        headers={"Origin": "https://testserver"},
    )


# ---------------------------------------------------------------------------
# Pruebas de inscripcion exitosa (US1)
# ---------------------------------------------------------------------------


def test_inscripcion_exitosa_reduce_cupo(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """RF-14: inscripcion valida -> 201 y cupo disponible disminuye en 1."""
    evento = _crear_evento(db_session, cupo_maximo=5)
    _login_participante(client, usuario_participante)

    antes = inscripcion_repo.contar_activas(db_session, evento.id)
    assert antes == 0

    resp = _inscribirse(client, evento.id)
    assert resp.status_code == 201, resp.text
    datos = resp.json()
    assert datos["estado"] == "activa"
    assert datos["evento_id"] == evento.id
    assert datos["participante_id"] == usuario_participante.id

    despues = inscripcion_repo.contar_activas(db_session, evento.id)
    assert despues == 1


def test_inscripcion_evento_no_encontrado_retorna_404(
    client: TestClient,
    usuario_participante: Usuario,
) -> None:
    """RF-14: evento inexistente -> 404 EVENTO_NO_ENCONTRADO."""
    _login_participante(client, usuario_participante)
    resp = _inscribirse(client, 999999)
    assert resp.status_code == 404
    assert resp.json()["error"]["codigo"] == CodigosError.EVENTO_NO_ENCONTRADO


def test_inscripcion_evento_no_publicado_retorna_409(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """RF-14: evento borrador -> 409 EVENTO_NO_PUBLICADO."""
    evento = _crear_evento(
        db_session,
        estado=EstadoEvento.BORRADOR.value,
    )
    _login_participante(client, usuario_participante)
    resp = _inscribirse(client, evento.id)
    assert resp.status_code == 409
    assert resp.json()["error"]["codigo"] == CodigosError.EVENTO_NO_PUBLICADO


def test_inscripciones_cerradas_despues_de_limite_retorna_409(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """RN-07: fecha_limite_inscripcion pasada -> 409 INSCRIPCIONES_CERRADAS."""
    evento = _crear_evento(
        db_session,
        cupo_maximo=5,
        dias_limite=-1,
        dias_inicio=14,
    )
    _login_participante(client, usuario_participante)
    resp = _inscribirse(client, evento.id)
    assert resp.status_code == 409
    assert resp.json()["error"]["codigo"] == CodigosError.INSCRIPCIONES_CERRADAS


def test_publico_no_permitido_retorna_409(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """RN-11: estudiante en evento solo docentes -> 409 PUBLICO_NO_PERMITIDO."""
    evento = _crear_evento(
        db_session,
        cupo_maximo=5,
        publico_objetivo=PublicoObjetivo.DOCENTES.value,
    )
    _login_participante(client, usuario_participante)
    resp = _inscribirse(client, evento.id)
    assert resp.status_code == 409
    assert resp.json()["error"]["codigo"] == CodigosError.PUBLICO_NO_PERMITIDO


# ---------------------------------------------------------------------------
# Pruebas de cupo y duplicados (US1, US2)
# ---------------------------------------------------------------------------


def test_cupo_agotado_retorna_409_sin_insertar(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """RN-05/CA-04: cupo lleno -> 409 CUPO_AGOTADO y no inserta registro."""
    evento = _crear_evento(db_session, cupo_maximo=1)

    usuario1 = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="2000000001",
        nombre="Usuario Uno",
    )
    _login_participante(client, usuario1)
    resp1 = _inscribirse(client, evento.id)
    assert resp1.status_code == 201

    usuario2 = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="2000000002",
        nombre="Usuario Dos",
    )
    _login_participante(client, usuario2)
    resp2 = _inscribirse(client, evento.id)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["codigo"] == CodigosError.CUPO_AGOTADO

    assert inscripcion_repo.contar_activas(db_session, evento.id) == 1


def test_inscripcion_duplicada_activa_retorna_409(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """RN-05: ya tiene inscripcion activa -> 409 INSCRIPCION_DUPLICADA."""
    evento = _crear_evento(db_session, cupo_maximo=5)
    _login_participante(client, usuario_participante)

    resp1 = _inscribirse(client, evento.id)
    assert resp1.status_code == 201

    resp2 = _inscribirse(client, evento.id)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["codigo"] == CodigosError.INSCRIPCION_DUPLICADA

    assert inscripcion_repo.contar_activas(db_session, evento.id) == 1


def test_reinscripcion_tras_cancelacion_crea_nuevo_registro(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """US1 escenario 2: reinscripcion tras cancelacion crea registro nuevo."""
    evento = _crear_evento(db_session, cupo_maximo=5)
    _login_participante(client, usuario_participante)

    resp1 = _inscribirse(client, evento.id)
    assert resp1.status_code == 201
    inscripcion_id_1 = resp1.json()["id"]

    resp_cancel = _cancelar(client, inscripcion_id_1)
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["estado"] == "cancelada"

    resp2 = _inscribirse(client, evento.id)
    assert resp2.status_code == 201
    inscripcion_id_2 = resp2.json()["id"]
    assert inscripcion_id_2 != inscripcion_id_1

    assert inscripcion_repo.contar_activas(db_session, evento.id) == 1
    total = db_session.query(Inscripcion).filter(Inscripcion.evento_id == evento.id).count()
    assert total == 2


# ---------------------------------------------------------------------------
# Pruebas de cancelacion (US3)
# ---------------------------------------------------------------------------


def test_cancelar_inscripcion_exitosa_antes_de_inicio(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """US3: cancelar antes de fecha_inicio -> 200, estado cancelada, cupo liberado."""
    evento = _crear_evento(db_session, cupo_maximo=5, dias_inicio=14)
    _login_participante(client, usuario_participante)

    resp_insc = _inscribirse(client, evento.id)
    assert resp_insc.status_code == 201
    inscripcion_id = resp_insc.json()["id"]

    resp_cancel = _cancelar(client, inscripcion_id)
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["estado"] == "cancelada"
    assert resp_cancel.json()["cancelada_en"] is not None

    assert inscripcion_repo.contar_activas(db_session, evento.id) == 0


def test_cancelar_despues_de_fecha_inicio_retorna_409(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """RN-07: cancelar despues de fecha_inicio -> 409 CANCELACION_NO_PERMITIDA."""
    evento = _crear_evento(
        db_session,
        cupo_maximo=5,
        dias_inicio=-1,
        dias_limite=-2,  # limite antes de inicio (CHECK constraint)
    )
    _login_participante(client, usuario_participante)

    # Crear inscripcion activa directamente en BD (no se puede por API en evento iniciado)
    inscripcion = Inscripcion(
        evento_id=evento.id,
        participante_id=usuario_participante.id,
        estado=EstadoInscripcion.ACTIVA.value,
        creado_en=ahora_utc(),
    )
    db_session.add(inscripcion)
    db_session.commit()
    db_session.refresh(inscripcion)

    resp_cancel = _cancelar(client, inscripcion.id)
    assert resp_cancel.status_code == 409
    assert resp_cancel.json()["error"]["codigo"] == CodigosError.CANCELACION_NO_PERMITIDA


def test_cancelar_inscripcion_ajena_retorna_403(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """RN-04: cancelar inscripcion de otro usuario -> 403 SIN_PERMISO."""
    evento = _crear_evento(db_session, cupo_maximo=5)

    usuario_dueno = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="3000000001",
        nombre="Usuario Dueno",
    )
    usuario_ajeno = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="3000000002",
        nombre="Usuario Ajeno",
    )

    _login_participante(client, usuario_dueno)
    resp_insc = _inscribirse(client, evento.id)
    assert resp_insc.status_code == 201
    inscripcion_id = resp_insc.json()["id"]

    _login_participante(client, usuario_ajeno)
    resp_cancel = _cancelar(client, inscripcion_id)
    assert resp_cancel.status_code == 403
    assert resp_cancel.json()["error"]["codigo"] == CodigosError.SIN_PERMISO


# ---------------------------------------------------------------------------
# Pruebas de consultas (US4, US5)
# ---------------------------------------------------------------------------


def test_listar_mis_inscripciones(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
) -> None:
    """US5: GET /inscripciones/mias retorna historial del participante."""
    evento = _crear_evento(db_session, cupo_maximo=5)
    _login_participante(client, usuario_participante)

    _inscribirse(client, evento.id)

    resp = client.get("/api/v1/inscripciones/mias")
    assert resp.status_code == 200
    datos = resp.json()
    assert len(datos) == 1
    assert datos[0]["estado"] == "activa"
    assert datos[0]["evento_id"] == evento.id
    assert datos[0]["titulo_evento"] == evento.titulo
    assert datos[0]["fecha_inicio_evento"] == evento.fecha_inicio.isoformat().replace("+00:00", "Z")
    assert datos[0]["estado_evento"] == "publicado"


def test_listar_inscritos_organizador_ve_documento_completo(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
    usuario_organizador: Usuario,
) -> None:
    """US4: organizador dueno ve documento completo de inscritos."""
    evento = _crear_evento(
        db_session,
        cupo_maximo=5,
        organizador_id=usuario_organizador.id,
    )
    _login_participante(client, usuario_participante)
    _inscribirse(client, evento.id)

    resp_login = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": usuario_organizador.tipo_documento,
            "numero_documento": usuario_organizador.numero_documento,
            "password": "ClaveSegura123!",
        },
        headers={"Origin": "https://testserver"},
    )
    assert resp_login.status_code == 200

    resp = client.get(
        f"/api/v1/eventos/{evento.id}/inscripciones",
        headers={"Origin": "https://testserver"},
    )
    assert resp.status_code == 200
    datos = resp.json()
    assert len(datos) == 1
    assert datos[0]["numero_documento"] == usuario_participante.numero_documento


def test_listar_inscritos_coordinacion_ve_documento_enmascarado(
    client: TestClient,
    db_session: Session,
    usuario_participante: Usuario,
    usuario_coordinacion: Usuario,
) -> None:
    """US4: coordinacion ve documento enmascarado (bullet••••1234)."""
    evento = _crear_evento(db_session, cupo_maximo=5)
    _login_participante(client, usuario_participante)
    _inscribirse(client, evento.id)

    resp_login = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": usuario_coordinacion.tipo_documento,
            "numero_documento": usuario_coordinacion.numero_documento,
            "password": "ClaveSegura123!",
        },
        headers={"Origin": "https://testserver"},
    )
    assert resp_login.status_code == 200

    resp = client.get(
        f"/api/v1/eventos/{evento.id}/inscripciones",
        headers={"Origin": "https://testserver"},
    )
    assert resp.status_code == 200
    datos = resp.json()
    assert len(datos) == 1
    doc = datos[0]["numero_documento"]
    assert doc.startswith("••••")
    assert doc.endswith(usuario_participante.numero_documento[-4:])


def test_listar_inscritos_sin_permiso_retorna_403(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """US4: participante no dueno ni coordinacion -> 403 SIN_PERMISO."""
    organizador = crear_usuario_factory(
        rol=Rol.ORGANIZADOR,
        numero_documento="4000000001",
        nombre="Organizador",
    )
    participante_ajeno = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="4000000002",
        nombre="Participante Ajeno",
    )
    evento = _crear_evento(db_session, cupo_maximo=5, organizador_id=organizador.id)

    _login_participante(client, participante_ajeno)
    resp = client.get(
        f"/api/v1/eventos/{evento.id}/inscripciones",
        headers={"Origin": "https://testserver"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["codigo"] == CodigosError.SIN_PERMISO


# ---------------------------------------------------------------------------
# Prueba de concurrencia (US1, RNF-04, PF-07)
# ---------------------------------------------------------------------------


def _inscribir_con_sesion_propia(db_path: str, evento_id: int, participante_id: int) -> str:
    """Intenta inscribir con una sesion BD propia; retorna codigo de dominio o 'ok'."""
    from app.core.errors import ErrorDominio

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _configurar_pragmas(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()

    import app.models  # noqa: F401
    from app.core.database import Base

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        usuario = session.get(Usuario, participante_id)
        if usuario is None:
            return "usuario_no_existe"
        try:
            inscripcion_service.inscribir(session, evento_id, usuario)
            return "ok"
        except ErrorDominio as exc:
            return exc.codigo
    finally:
        session.close()
        engine.dispose()


def test_concurrencia_cupo_atomico(
    db_session: Session,
    crear_usuario_factory,
    tmp_path,
) -> None:
    """RNF-04 / PF-07: 20 hilos disputando 5 cupos -> exactamente 5 exitosos, 15 CUPO_AGOTADO."""
    # Usa archivo DB separado para evitar bloqueo con la sesion de prueba principal
    db_path = str(tmp_path / "concurrencia_test.db")
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _configurar_pragmas(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()

    import app.models  # noqa: F401
    from app.core.database import Base

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        evento = _crear_evento(session, cupo_maximo=5)

        participantes = []
        for i in range(20):
            from argon2 import PasswordHasher

            hasher = PasswordHasher()
            u = Usuario(
                tipo_documento=TipoDocumento.CC.value,
                numero_documento=f"5000000{i:03d}",
                nombre=f"Usuario Concurrente {i}",
                correo=f"concurrente{i}@example.edu",
                tipo_participante="estudiante",
                hash_password=hasher.hash("ClaveSegura123!"),
                rol=Rol.PARTICIPANTE.value,
                activo=True,
            )
            session.add(u)
            session.commit()
            session.refresh(u)
            participantes.append(u.id)

        resultados = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futuros = [
                executor.submit(_inscribir_con_sesion_propia, db_path, evento.id, pid)
                for pid in participantes
            ]
            for futuro in concurrent.futures.as_completed(futuros):
                resultados.append(futuro.result())

        exitos = resultados.count("ok")
        rechazos = resultados.count(CodigosError.CUPO_AGOTADO)

        assert exitos == 5, f"Esperaba 5 exitosos, obtuvo {exitos}"
        assert rechazos == 15, f"Esperaba 15 rechazados por cupo, obtuvo {rechazos}"

        activas = inscripcion_repo.contar_activas(session, evento.id)
        assert activas == 5
    finally:
        session.close()
        engine.dispose()
