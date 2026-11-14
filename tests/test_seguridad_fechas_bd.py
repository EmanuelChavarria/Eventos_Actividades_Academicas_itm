"""Pruebas iniciales (rojo -> verde) de reglas base de fundación E1."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_config_secret_key_insegura_falla() -> None:
    """RNF-05: el arranque falla si SECRET_KEY es vacía, corta o igual al valor de ejemplo."""
    from app.core.config import VALOR_EJEMPLO_SECRET_KEY, Settings

    with pytest.raises(ValueError):
        Settings(SECRET_KEY="", COOKIE_SECURE=True, DATABASE_URL="sqlite:///./a.db")

    with pytest.raises(ValueError):
        Settings(SECRET_KEY="muy_corta", COOKIE_SECURE=True, DATABASE_URL="sqlite:///./a.db")

    with pytest.raises(ValueError):
        Settings(
            SECRET_KEY=VALOR_EJEMPLO_SECRET_KEY,
            COOKIE_SECURE=True,
            DATABASE_URL="sqlite:///./a.db",
        )


def test_config_cookie_secure_false_falla() -> None:
    """RNF-05: la aplicación falla al arrancar si COOKIE_SECURE no es true."""
    from app.core.config import Settings

    with pytest.raises(ValueError):
        Settings(
            SECRET_KEY="clave_segura_de_al_menos_treinta_y_dos_caracteres_ok",
            COOKIE_SECURE=False,
            DATABASE_URL="sqlite:///./a.db",
        )


def test_fechas_sin_zona_horaria_rechazada() -> None:
    """RNF-16 / RN-18: rechaza fechas naive sin zona horaria."""
    from app.core.errors import ReglaNegocio
    from app.core.fechas import asegurar_utc

    naive = datetime(2026, 11, 20, 14, 0, 0)
    with pytest.raises((ReglaNegocio, ValueError)):
        asegurar_utc(naive)


def test_fechas_conversion_utc_y_bogota() -> None:
    """RNF-16 / RN-18: convierte de -05:00 a UTC y presenta en America/Bogota."""
    from app.core.fechas import a_bogota, asegurar_utc

    bogota_tz = timezone(timedelta(hours=-5))
    local = datetime(2026, 11, 20, 10, 0, 0, tzinfo=bogota_tz)
    en_utc = asegurar_utc(local)
    assert en_utc.tzinfo == UTC
    assert en_utc.hour == 15

    de_vuelta = a_bogota(en_utc)
    assert de_vuelta.hour == 10
    assert de_vuelta.utcoffset() == timedelta(hours=-5)


def test_fechas_ventana_asistencia_48h() -> None:
    """RN-08 / RN-17: ventana de asistencia válida desde inicio hasta fin + 48 h en UTC."""
    from app.core.fechas import esta_en_ventana_asistencia

    inicio = datetime(2026, 11, 20, 14, 0, 0, tzinfo=UTC)
    fin = datetime(2026, 11, 20, 16, 0, 0, tzinfo=UTC)

    assert esta_en_ventana_asistencia(inicio, fin, ahora=inicio) is True
    assert esta_en_ventana_asistencia(inicio, fin, ahora=fin + timedelta(hours=48)) is True
    assert esta_en_ventana_asistencia(inicio, fin, ahora=inicio - timedelta(seconds=1)) is False
    assert (
        esta_en_ventana_asistencia(
            inicio,
            fin,
            ahora=fin + timedelta(hours=48, seconds=1),
        )
        is False
    )


def test_sqlite_pragmas_foreign_keys_y_busy_timeout(db_session: Session, tmp_path: Path) -> None:
    """RNF-03: get_db y motor SQLite activan foreign_keys=ON y busy_timeout=5000."""
    from sqlalchemy.orm import sessionmaker

    from app.core.database import crear_motor

    fk = db_session.execute(text("PRAGMA foreign_keys;")).scalar_one()
    busy = db_session.execute(text("PRAGMA busy_timeout;")).scalar_one()
    assert fk == 1
    assert busy == 5000

    motor_tmp = crear_motor(f"sqlite:///{tmp_path / 'motor_pragmas.db'}")
    sesion_factory = sessionmaker(autocommit=False, autoflush=False, bind=motor_tmp)
    try:
        with sesion_factory() as sesion_app:
            assert sesion_app.execute(text("PRAGMA foreign_keys;")).scalar_one() == 1
            assert sesion_app.execute(text("PRAGMA busy_timeout;")).scalar_one() == 5000
    finally:
        motor_tmp.dispose()


def test_bd_documento_unico_y_correo_repetido(db_session: Session, crear_usuario_factory) -> None:
    """RN-13 / RNF-03: UNIQUE(tipo, num) permite distinto tipo y correo repetido."""
    crear_usuario_factory(
        numero_documento="1000000201",
        correo="compartido@example.edu",
    )
    otro_tipo = crear_usuario_factory(
        tipo_documento="CE",
        numero_documento="1000000201",
        correo="compartido@example.edu",
    )
    assert otro_tipo.id is not None

    with pytest.raises(IntegrityError):
        crear_usuario_factory(
            numero_documento="1000000201",
            correo="otro@example.edu",
        )
    db_session.rollback()


def test_bd_restricciones_check_y_indice_parcial(
    db_session: Session, usuario_organizador, usuario_participante
) -> None:
    """RNF-03 / RN-02 / RN-03 / RN-04: valida CHECK de cupo/fechas e índice único parcial activa."""
    from app.models.enums import (
        EstadoEvento,
        EstadoInscripcion,
        Modalidad,
        PublicoObjetivo,
        TipoEvento,
    )
    from app.models.evento import Evento
    from app.models.inscripcion import Inscripcion

    inicio = datetime(2026, 12, 1, 14, 0, 0, tzinfo=UTC)
    fin = datetime(2026, 12, 1, 16, 0, 0, tzinfo=UTC)
    limite = datetime(2026, 11, 30, 23, 59, 0, tzinfo=UTC)

    evento_invalido = Evento(
        titulo="Evento Cupo Cero",
        descripcion="Prueba",
        tipo=TipoEvento.TALLER,
        fecha_inicio=inicio,
        fecha_fin=fin,
        fecha_limite_inscripcion=limite,
        lugar="Auditorio",
        modalidad=Modalidad.PRESENCIAL,
        publico_objetivo=PublicoObjetivo.TODOS,
        responsable_nombre="Resp",
        responsable_correo="resp@example.edu",
        cupo_maximo=0,
        estado=EstadoEvento.BORRADOR,
        organizador_id=usuario_organizador.id,
    )
    db_session.add(evento_invalido)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    evento_valido = Evento(
        titulo="Evento Válido",
        descripcion="Prueba integridad",
        tipo=TipoEvento.CONFERENCIA,
        fecha_inicio=inicio,
        fecha_fin=fin,
        fecha_limite_inscripcion=limite,
        lugar="Sala A",
        modalidad=Modalidad.HIBRIDA,
        publico_objetivo=PublicoObjetivo.TODOS,
        responsable_nombre="Resp",
        responsable_correo="resp@example.edu",
        cupo_maximo=10,
        estado=EstadoEvento.PUBLICADO,
        organizador_id=usuario_organizador.id,
    )
    db_session.add(evento_valido)
    db_session.commit()
    db_session.refresh(evento_valido)

    # Dos inscripciones canceladas + una activa para la misma pareja deben permitirse.
    db_session.add_all(
        [
            Inscripcion(
                evento_id=evento_valido.id,
                participante_id=usuario_participante.id,
                estado=EstadoInscripcion.CANCELADA,
            ),
            Inscripcion(
                evento_id=evento_valido.id,
                participante_id=usuario_participante.id,
                estado=EstadoInscripcion.CANCELADA,
            ),
            Inscripcion(
                evento_id=evento_valido.id,
                participante_id=usuario_participante.id,
                estado=EstadoInscripcion.ACTIVA,
            ),
        ]
    )
    db_session.commit()

    # Una segunda inscripción activa para la misma pareja debe fallar por índice parcial.
    db_session.add(
        Inscripcion(
            evento_id=evento_valido.id,
            participante_id=usuario_participante.id,
            estado=EstadoInscripcion.ACTIVA,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_errores_formato_uniforme_sin_input() -> None:
    """RNF-07: ErrorDominio y RequestValidationError usan formato uniforme y omiten input."""
    from app.core.errors import Conflicto, registrar_manejadores_errores

    app_prueba = FastAPI()
    registrar_manejadores_errores(app_prueba)

    class _Entrada(BaseModel):
        password: str = Field(min_length=8)

    @app_prueba.post("/validar")
    def _validar(datos: _Entrada):
        return datos

    @app_prueba.get("/conflicto")
    def _conflicto():
        raise Conflicto(codigo="DOCUMENTO_DUPLICADO", mensaje="Documento duplicado.")

    with TestClient(app_prueba, base_url="https://testserver") as tc:
        resp_422 = tc.post("/validar", json={"password": "secreto_muy_corto"})
        assert resp_422.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        cuerpo_422 = resp_422.json()
        assert set(cuerpo_422.keys()) == {"error"}
        assert set(cuerpo_422["error"].keys()) == {"codigo", "mensaje", "detalles"}
        assert "secreto_muy_corto" not in resp_422.text
        for detalle in cuerpo_422["error"]["detalles"]:
            assert "input" not in detalle

        resp_409 = tc.get("/conflicto")
        assert resp_409.status_code == status.HTTP_409_CONFLICT
        assert resp_409.json() == {
            "error": {
                "codigo": "DOCUMENTO_DUPLICADO",
                "mensaje": "Documento duplicado.",
                "detalles": [],
            }
        }
