---
paths:
  - "migrations/**"
  - "alembic.ini"
  - "app/models/**/*.py"
---

# Reglas para migraciones y modelos (Alembic + SQLAlchemy 2.x)

- **Contrato compartido:** `app/models/` y `migrations/` son de A y solo cambian con acuerdo de ambos integrantes y con la spec actualizada antes.
- **Una migración por cambio lógico**, con nombre descriptivo; nunca editar una migración ya fusionada en `main` (crear otra).
- **Integridad en BD:** PK, FK con `PRAGMA foreign_keys=ON` y `PRAGMA busy_timeout=5000` por conexión, `UNIQUE(tipo_documento, numero_documento)` en `usuarios` (el correo **no** es único), `CHECK(cupo_maximo >= 1)`, `CHECK(fecha_fin > fecha_inicio)`, `CHECK(fecha_limite_inscripcion <= fecha_inicio)`, `UNIQUE(inscripcion_id)` en `asistencias` e **índice único parcial** `(evento_id, participante_id) WHERE estado='activa'`.
- **Estados guardados:** `borrador`, `publicado`, `cancelado` (evento) y `activa`, `cancelada` (inscripción). `finalizado`, «inscripciones cerradas» y `cupos_disponibles` se calculan, no son columnas.
- **Fechas UTC:** usar un `TypeDecorator` (o tipo estricto en ORM) que normalice a UTC al guardar y devuelva `datetime` con `tzinfo=timezone.utc` al leer, manteniendo un formato ISO UTC uniforme en SQLite para que `CHECK(fecha_fin > fecha_inicio)` sea fiable.
- **SQLite:** usar `batch_alter_table` para alterar tablas; índices en FK y columnas de filtro.
- **Reproducibilidad:** `alembic upgrade head` debe funcionar en limpio y el seed ser idempotente, con documentos ficticios obviamente falsos.
- Nunca commitear `*.db`.
