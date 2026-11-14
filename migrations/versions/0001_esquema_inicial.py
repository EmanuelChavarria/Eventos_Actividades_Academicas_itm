"""Esquema inicial de usuarios, eventos, inscripciones y asistencias.

Revision ID: 0001_esquema_inicial
Revises:
Create Date: 2026-11-14 15:58:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_esquema_inicial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea las cuatro tablas del dominio con sus restricciones e índices."""
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tipo_documento", sa.String(length=4), nullable=False),
        sa.Column("numero_documento", sa.String(length=15), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("correo", sa.String(length=150), nullable=False),
        sa.Column("tipo_participante", sa.String(length=20), nullable=True),
        sa.Column("hash_password", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.String(length=32), nullable=False),
        sa.CheckConstraint("length(numero_documento) BETWEEN 5 AND 15", name="ck_usuarios_doc_len"),
        sa.CheckConstraint(
            "tipo_documento IN ('CC', 'CE', 'TI', 'PAS')",
            name="ck_usuarios_tipo_doc",
        ),
        sa.CheckConstraint(
            "rol IN ('participante', 'organizador', 'coordinacion')",
            name="ck_usuarios_rol",
        ),
        sa.CheckConstraint(
            "tipo_participante IS NULL OR tipo_participante IN ('estudiante', 'docente')",
            name="ck_usuarios_tipo_participante",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tipo_documento", "numero_documento", name="uq_usuarios_documento"),
    )

    op.create_table(
        "eventos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("fecha_inicio", sa.String(length=32), nullable=False),
        sa.Column("fecha_fin", sa.String(length=32), nullable=False),
        sa.Column("fecha_limite_inscripcion", sa.String(length=32), nullable=False),
        sa.Column("lugar", sa.String(length=200), nullable=False),
        sa.Column("modalidad", sa.String(length=20), nullable=False),
        sa.Column("publico_objetivo", sa.String(length=20), nullable=False),
        sa.Column("ponente", sa.String(length=150), nullable=True),
        sa.Column("requisitos", sa.Text(), nullable=True),
        sa.Column("responsable_nombre", sa.String(length=120), nullable=False),
        sa.Column("responsable_correo", sa.String(length=150), nullable=False),
        sa.Column("cupo_maximo", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("motivo_cancelacion", sa.Text(), nullable=True),
        sa.Column("organizador_id", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.String(length=32), nullable=False),
        sa.Column("actualizado_en", sa.String(length=32), nullable=False),
        sa.CheckConstraint("cupo_maximo >= 1", name="ck_eventos_cupo"),
        sa.CheckConstraint("fecha_fin > fecha_inicio", name="ck_eventos_fechas"),
        sa.CheckConstraint("fecha_limite_inscripcion <= fecha_inicio", name="ck_eventos_limite"),
        sa.CheckConstraint(
            "estado IN ('borrador', 'publicado', 'cancelado')",
            name="ck_eventos_estado",
        ),
        sa.CheckConstraint(
            "tipo IN ('conferencia', 'taller', 'seminario', 'capacitacion')",
            name="ck_eventos_tipo",
        ),
        sa.CheckConstraint(
            "modalidad IN ('presencial', 'virtual', 'hibrida')",
            name="ck_eventos_modalidad",
        ),
        sa.CheckConstraint(
            "publico_objetivo IN ('todos', 'estudiantes', 'docentes')",
            name="ck_eventos_publico",
        ),
        sa.ForeignKeyConstraint(["organizador_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eventos_estado_inicio", "eventos", ["estado", "fecha_inicio"])
    op.create_index("ix_eventos_organizador", "eventos", ["organizador_id"])

    op.create_table(
        "inscripciones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evento_id", sa.Integer(), nullable=False),
        sa.Column("participante_id", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("creado_en", sa.String(length=32), nullable=False),
        sa.Column("cancelada_en", sa.String(length=32), nullable=True),
        sa.CheckConstraint("estado IN ('activa', 'cancelada')", name="ck_inscripciones_estado"),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["participante_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inscripciones_evento", "inscripciones", ["evento_id"])
    op.create_index("ix_inscripciones_participante", "inscripciones", ["participante_id"])
    op.create_index(
        "ux_inscripciones_activa",
        "inscripciones",
        ["evento_id", "participante_id"],
        unique=True,
        sqlite_where=sa.text("estado = 'activa'"),
    )

    op.create_table(
        "asistencias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inscripcion_id", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("registrado_por_id", sa.Integer(), nullable=False),
        sa.Column("registrado_en", sa.String(length=32), nullable=False),
        sa.Column("actualizado_en", sa.String(length=32), nullable=False),
        sa.CheckConstraint("estado IN ('presente', 'ausente')", name="ck_asistencias_estado"),
        sa.ForeignKeyConstraint(["inscripcion_id"], ["inscripciones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["registrado_por_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inscripcion_id", name="uq_asistencias_inscripcion"),
    )


def downgrade() -> None:
    """Elimina todas las tablas e índices del esquema inicial."""
    op.drop_table("asistencias")
    op.drop_index("ux_inscripciones_activa", table_name="inscripciones")
    op.drop_index("ix_inscripciones_participante", table_name="inscripciones")
    op.drop_index("ix_inscripciones_evento", table_name="inscripciones")
    op.drop_table("inscripciones")
    op.drop_index("ix_eventos_organizador", table_name="eventos")
    op.drop_index("ix_eventos_estado_inicio", table_name="eventos")
    op.drop_table("eventos")
    op.drop_table("usuarios")
