"""Script idempotente para poblar datos ficticios de prueba (PF-04)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))

from app.core.database import SessionLocal
from app.core.fechas import ahora_utc
from app.models.enums import (
    EstadoEvento,
    Modalidad,
    PublicoObjetivo,
    Rol,
    TipoDocumento,
    TipoEvento,
    TipoParticipante,
)
from app.models.evento import Evento
from app.models.usuario import Usuario

CLAVE_DEMO_FICTICIA = "DemoFicticia123!"


def _asegurar_usuario(
    db: Session,
    *,
    tipo_documento: TipoDocumento,
    numero_documento: str,
    nombre: str,
    correo: str,
    rol: Rol,
    tipo_participante: TipoParticipante | None,
    hash_password: str,
) -> tuple[Usuario, bool]:
    existente = db.execute(
        select(Usuario).where(
            Usuario.tipo_documento == tipo_documento.value,
            Usuario.numero_documento == numero_documento,
        )
    ).scalar_one_or_none()
    if existente is not None:
        return existente, False

    usuario = Usuario(
        tipo_documento=tipo_documento.value,
        numero_documento=numero_documento,
        nombre=nombre,
        correo=correo,
        tipo_participante=tipo_participante.value if tipo_participante else None,
        hash_password=hash_password,
        rol=rol.value,
        activo=True,
    )
    db.add(usuario)
    db.flush()
    return usuario, True


def _asegurar_evento(db: Session, *, organizador_id: int, datos: dict) -> bool:
    existente = db.execute(
        select(Evento).where(
            Evento.titulo == datos["titulo"],
            Evento.organizador_id == organizador_id,
        )
    ).scalar_one_or_none()
    if existente is not None:
        return False

    evento = Evento(organizador_id=organizador_id, **datos)
    db.add(evento)
    db.flush()
    return True


def poblar_datos(db: Session, *, ahora: datetime | None = None) -> dict[str, int]:
    """Inserta usuarios y eventos ficticios de forma idempotente."""
    ref = (ahora or ahora_utc()).astimezone(UTC)
    hash_demo = PasswordHasher().hash(CLAVE_DEMO_FICTICIA)
    usuarios_creados = 0
    eventos_creados = 0

    usuarios_base = [
        {
            "tipo_documento": TipoDocumento.CC,
            "numero_documento": "9000000001",
            "nombre": "Laura Gómez (Coordinación Demo)",
            "correo": "coordinacion.demo@example.edu",
            "rol": Rol.COORDINACION,
            "tipo_participante": None,
        },
        {
            "tipo_documento": TipoDocumento.CC,
            "numero_documento": "9000000002",
            "nombre": "Carlos Ruiz (Organizador Demo 1)",
            "correo": "organizador1.demo@example.edu",
            "rol": Rol.ORGANIZADOR,
            "tipo_participante": None,
        },
        {
            "tipo_documento": TipoDocumento.CC,
            "numero_documento": "9000000003",
            "nombre": "Marta Díaz (Organizador Demo 2)",
            "correo": "organizador2.demo@example.edu",
            "rol": Rol.ORGANIZADOR,
            "tipo_participante": None,
        },
        {
            "tipo_documento": TipoDocumento.CC,
            "numero_documento": "1000000001",
            "nombre": "Ana Torres (Estudiante Demo)",
            "correo": "participante1.demo@example.edu",
            "rol": Rol.PARTICIPANTE,
            "tipo_participante": TipoParticipante.ESTUDIANTE,
        },
        {
            "tipo_documento": TipoDocumento.CC,
            "numero_documento": "1000000002",
            "nombre": "Luis Pérez (Estudiante Demo)",
            "correo": "participante2.demo@example.edu",
            "rol": Rol.PARTICIPANTE,
            "tipo_participante": TipoParticipante.ESTUDIANTE,
        },
        {
            "tipo_documento": TipoDocumento.TI,
            "numero_documento": "1000000003",
            "nombre": "Sofía Castro (Estudiante Demo)",
            "correo": "participante3.demo@example.edu",
            "rol": Rol.PARTICIPANTE,
            "tipo_participante": TipoParticipante.ESTUDIANTE,
        },
        {
            "tipo_documento": TipoDocumento.CC,
            "numero_documento": "1000000004",
            "nombre": "Diego Morales (Estudiante Demo)",
            "correo": "participante4.demo@example.edu",
            "rol": Rol.PARTICIPANTE,
            "tipo_participante": TipoParticipante.ESTUDIANTE,
        },
        {
            "tipo_documento": TipoDocumento.CE,
            "numero_documento": "1000000005",
            "nombre": "Elena Vargas (Docente Demo)",
            "correo": "participante5.demo@example.edu",
            "rol": Rol.PARTICIPANTE,
            "tipo_participante": TipoParticipante.DOCENTE,
        },
        {
            "tipo_documento": TipoDocumento.PAS,
            "numero_documento": "PA1000006",
            "nombre": "Jorge Mendoza (Docente Demo)",
            "correo": "participante6.demo@example.edu",
            "rol": Rol.PARTICIPANTE,
            "tipo_participante": TipoParticipante.DOCENTE,
        },
    ]

    mapa_organizadores: list[Usuario] = []
    for item in usuarios_base:
        usuario, creado = _asegurar_usuario(db, hash_password=hash_demo, **item)
        if creado:
            usuarios_creados += 1
        if item["rol"] == Rol.ORGANIZADOR:
            mapa_organizadores.append(usuario)

    org_1, org_2 = mapa_organizadores[0], mapa_organizadores[1]

    eventos_base = [
        (
            org_1.id,
            {
                "titulo": "Seminario de Arquitectura Limpia en Python",
                "descripcion": "Sesión práctica sobre diseño por capas y pruebas.",
                "tipo": TipoEvento.SEMINARIO.value,
                "fecha_inicio": ref + timedelta(days=10),
                "fecha_fin": ref + timedelta(days=10, hours=3),
                "fecha_limite_inscripcion": ref + timedelta(days=9),
                "lugar": "Auditorio Bloque C",
                "modalidad": Modalidad.PRESENCIAL.value,
                "publico_objetivo": PublicoObjetivo.TODOS.value,
                "ponente": "Ing. Camila Rojas",
                "requisitos": "Conocimientos básicos de programación",
                "responsable_nombre": org_1.nombre,
                "responsable_correo": org_1.correo,
                "cupo_maximo": 30,
                "estado": EstadoEvento.PUBLICADO.value,
                "motivo_cancelacion": None,
            },
        ),
        (
            org_1.id,
            {
                "titulo": "Taller de Seguridad Web con FastAPI",
                "descripcion": "Cookies seguras, CSRF y validación de entradas.",
                "tipo": TipoEvento.TALLER.value,
                "fecha_inicio": ref + timedelta(days=15),
                "fecha_fin": ref + timedelta(days=15, hours=2),
                "fecha_limite_inscripcion": ref + timedelta(days=14),
                "lugar": "Enlace institucional",
                "modalidad": Modalidad.VIRTUAL.value,
                "publico_objetivo": PublicoObjetivo.ESTUDIANTES.value,
                "ponente": "MSc. Andrés León",
                "requisitos": "Portátil con Python 3.12",
                "responsable_nombre": org_1.nombre,
                "responsable_correo": org_1.correo,
                "cupo_maximo": 20,
                "estado": EstadoEvento.PUBLICADO.value,
                "motivo_cancelacion": None,
            },
        ),
        (
            org_2.id,
            {
                "titulo": "Capacitación Docente en Evaluación Formativa",
                "descripcion": "Estrategias de retroalimentación en cursos de ingeniería.",
                "tipo": TipoEvento.CAPACITACION.value,
                "fecha_inicio": ref + timedelta(days=20),
                "fecha_fin": ref + timedelta(days=20, hours=4),
                "fecha_limite_inscripcion": ref + timedelta(days=18),
                "lugar": "Sala 204",
                "modalidad": Modalidad.HIBRIDA.value,
                "publico_objetivo": PublicoObjetivo.DOCENTES.value,
                "ponente": "Dra. Paola Mejía",
                "requisitos": None,
                "responsable_nombre": org_2.nombre,
                "responsable_correo": org_2.correo,
                "cupo_maximo": 25,
                "estado": EstadoEvento.BORRADOR.value,
                "motivo_cancelacion": None,
            },
        ),
        (
            org_2.id,
            {
                "titulo": "Conferencia de Ciencia de Datos Aplicada",
                "descripcion": "Casos académicos de analítica institucional.",
                "tipo": TipoEvento.CONFERENCIA.value,
                "fecha_inicio": ref + timedelta(days=12),
                "fecha_fin": ref + timedelta(days=12, hours=2),
                "fecha_limite_inscripcion": ref + timedelta(days=11),
                "lugar": "Auditorio Principal",
                "modalidad": Modalidad.PRESENCIAL.value,
                "publico_objetivo": PublicoObjetivo.TODOS.value,
                "ponente": None,
                "requisitos": None,
                "responsable_nombre": org_2.nombre,
                "responsable_correo": org_2.correo,
                "cupo_maximo": 50,
                "estado": EstadoEvento.CANCELADO.value,
                "motivo_cancelacion": "Reprogramación de agenda institucional",
            },
        ),
        (
            org_1.id,
            {
                "titulo": "Jornada Histórica de Inducción Investigativa",
                "descripcion": "Evento de referencia ya finalizado para pruebas de estado.",
                "tipo": TipoEvento.SEMINARIO.value,
                "fecha_inicio": ref - timedelta(days=10),
                "fecha_fin": ref - timedelta(days=10) + timedelta(hours=3),
                "fecha_limite_inscripcion": ref - timedelta(days=11),
                "lugar": "Sala 101",
                "modalidad": Modalidad.PRESENCIAL.value,
                "publico_objetivo": PublicoObjetivo.TODOS.value,
                "ponente": "Comité Académico",
                "requisitos": None,
                "responsable_nombre": org_1.nombre,
                "responsable_correo": org_1.correo,
                "cupo_maximo": 40,
                "estado": EstadoEvento.PUBLICADO.value,
                "motivo_cancelacion": None,
            },
        ),
    ]

    for org_id, datos in eventos_base:
        if _asegurar_evento(db, organizador_id=org_id, datos=datos):
            eventos_creados += 1

    db.commit()
    return {"usuarios_creados": usuarios_creados, "eventos_creados": eventos_creados}


def main() -> None:
    """Ejecuta el seed idempotente sobre la base de datos configurada."""
    with SessionLocal() as db:
        resumen = poblar_datos(db)
    print(
        f"Seed completado: {resumen['usuarios_creados']} usuarios nuevos, "
        f"{resumen['eventos_creados']} eventos nuevos."
    )


if __name__ == "__main__":
    main()
