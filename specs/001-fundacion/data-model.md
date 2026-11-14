# Modelo de datos y contrato inicial (E1)

- **Feature:** `001-fundacion` · **Motor:** SQLite 3 + SQLAlchemy 2.x + Alembic
- **Convenciones:** nombres en español (`snake_case`), fechas almacenadas en **UTC** (`UTCDateTime`), integridad garantizada tanto en servidor como en BD (`PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000`).

## 1. Enumeraciones (`app/models/enums.py`)

- `Rol`: `participante`, `organizador`, `coordinacion`
- `TipoDocumento`: `CC`, `CE`, `TI`, `PAS`
- `TipoParticipante`: `estudiante`, `docente`
- `TipoEvento`: `conferencia`, `taller`, `seminario`, `capacitacion`
- `Modalidad`: `presencial`, `virtual`, `hibrida`
- `PublicoObjetivo`: `todos`, `estudiantes`, `docentes`
- `EstadoEvento`: `borrador`, `publicado`, `cancelado`
- `EstadoInscripcion`: `activa`, `cancelada`
- `EstadoAsistencia`: `presente`, `ausente`

## 2. Tablas, columnas y restricciones

### `usuarios`
- `id` INTEGER PK autoincremental
- `tipo_documento` VARCHAR(4) NOT NULL (`CC` | `CE` | `TI` | `PAS`)
- `numero_documento` VARCHAR(15) NOT NULL (normalizado sin espacios/puntos; `PAS` en mayúsculas)
- `nombre` VARCHAR(120) NOT NULL
- `correo` VARCHAR(150) NOT NULL (**no único**)
- `tipo_participante` VARCHAR(20) NULL (`estudiante` | `docente`; `NULL` en personal)
- `hash_password` VARCHAR(255) NOT NULL (`argon2id`)
- `rol` VARCHAR(20) NOT NULL (`participante` | `organizador` | `coordinacion`)
- `activo` BOOLEAN NOT NULL DEFAULT `1`
- `creado_en` UTCDateTime NOT NULL
- **Restricciones:**
  - `UNIQUE (tipo_documento, numero_documento)` (`uq_usuarios_documento`)
  - `CHECK (length(numero_documento) BETWEEN 5 AND 15)` (`ck_usuarios_doc_len`)
  - `CHECK (tipo_documento IN ('CC','CE','TI','PAS'))` (`ck_usuarios_tipo_doc`)
  - `CHECK (rol IN ('participante','organizador','coordinacion'))` (`ck_usuarios_rol`)
  - `CHECK (tipo_participante IS NULL OR tipo_participante IN ('estudiante','docente'))` (`ck_usuarios_tipo_participante`)

### `eventos`
- `id` INTEGER PK autoincremental
- `titulo` VARCHAR(200) NOT NULL
- `descripcion` TEXT NOT NULL
- `tipo` VARCHAR(30) NOT NULL
- `fecha_inicio` UTCDateTime NOT NULL
- `fecha_fin` UTCDateTime NOT NULL
- `fecha_limite_inscripcion` UTCDateTime NOT NULL
- `lugar` VARCHAR(200) NOT NULL
- `modalidad` VARCHAR(20) NOT NULL
- `publico_objetivo` VARCHAR(20) NOT NULL DEFAULT `'todos'`
- `ponente` VARCHAR(150) NULL
- `requisitos` TEXT NULL
- `responsable_nombre` VARCHAR(120) NOT NULL
- `responsable_correo` VARCHAR(150) NOT NULL
- `cupo_maximo` INTEGER NOT NULL
- `estado` VARCHAR(20) NOT NULL DEFAULT `'borrador'`
- `motivo_cancelacion` TEXT NULL
- `organizador_id` INTEGER NOT NULL FK → `usuarios.id` (`ON DELETE RESTRICT`)
- `creado_en` UTCDateTime NOT NULL
- `actualizado_en` UTCDateTime NOT NULL
- **Restricciones e índices:**
  - `CHECK (cupo_maximo >= 1)` (`ck_eventos_cupo`)
  - `CHECK (fecha_fin > fecha_inicio)` (`ck_eventos_fechas`)
  - `CHECK (fecha_limite_inscripcion <= fecha_inicio)` (`ck_eventos_limite`)
  - `CHECK (estado IN ('borrador','publicado','cancelado'))` (`ck_eventos_estado`)
  - Índice `ix_eventos_estado_inicio (estado, fecha_inicio)` y `ix_eventos_organizador (organizador_id)`

### `inscripciones`
- `id` INTEGER PK autoincremental
- `evento_id` INTEGER NOT NULL FK → `eventos.id` (`ON DELETE RESTRICT`)
- `participante_id` INTEGER NOT NULL FK → `usuarios.id` (`ON DELETE RESTRICT`)
- `estado` VARCHAR(20) NOT NULL DEFAULT `'activa'`
- `creado_en` UTCDateTime NOT NULL
- `cancelada_en` UTCDateTime NULL
- **Restricciones e índices:**
  - `CHECK (estado IN ('activa','cancelada'))` (`ck_inscripciones_estado`)
  - **Índice único parcial:** `ux_inscripciones_activa ON inscripciones (evento_id, participante_id) WHERE estado = 'activa'`
  - Índices: `ix_inscripciones_evento (evento_id)`, `ix_inscripciones_participante (participante_id)`

### `asistencias`
- `id` INTEGER PK autoincremental
- `inscripcion_id` INTEGER NOT NULL FK → `inscripciones.id` (`ON DELETE RESTRICT`)
- `estado` VARCHAR(20) NOT NULL
- `registrado_por_id` INTEGER NOT NULL FK → `usuarios.id` (`ON DELETE RESTRICT`)
- `registrado_en` UTCDateTime NOT NULL
- `actualizado_en` UTCDateTime NOT NULL
- **Restricciones:**
  - `UNIQUE (inscripcion_id)` (`uq_asistencias_inscripcion`)
  - `CHECK (estado IN ('presente','ausente'))` (`ck_asistencias_estado`)
