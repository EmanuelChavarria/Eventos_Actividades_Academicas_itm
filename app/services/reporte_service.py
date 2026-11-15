"""Lógica de negocio del reporte consolidado de coordinación (E7)."""

from __future__ import annotations

import csv
import io
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.core.errors import CodigosError, NoAutorizado
from app.core.fechas import ProveedorAhora, ahora_utc, asegurar_utc
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.repositories import reporte_repo
from app.schemas.reporte import (
    ConsolidadoFiltros,
    ConsolidadoSalida,
    ConsolidadoTotales,
    EventoConsolidadoItem,
)
from app.services.asistencia_service import _enmascarar_documento
from app.services.evento_service import calcular_estado_efectivo


def _validar_coordinacion(usuario: Usuario) -> None:
    """Garantiza que solo usuarios activos de coordinación accedan al consolidado."""
    if not usuario.activo or usuario.rol != Rol.COORDINACION.value:
        raise NoAutorizado(
            codigo=CodigosError.SIN_PERMISO,
            mensaje="Solo coordinación puede consultar el reporte consolidado.",
        )


def _calcular_porcentaje(numerador: int, denominador: int) -> float:
    """Calcula porcentaje redondeado a 2 decimales evitando división por cero."""
    if denominador <= 0:
        return 0.0
    return round((numerador / denominador) * 100, 2)


def obtener_consolidado(
    db: Session,
    filtros: ConsolidadoFiltros,
    usuario: Usuario,
    proveedor_ahora: ProveedorAhora = ahora_utc,
) -> ConsolidadoSalida:
    """Genera las métricas por evento y los totales globales del reporte consolidado."""
    _validar_coordinacion(usuario)
    referencia = asegurar_utc(proveedor_ahora())
    filas = reporte_repo.obtener_consolidado_eventos(db, filtros, referencia)

    eventos: list[EventoConsolidadoItem] = []
    for fila in filas:
        estado_efectivo = calcular_estado_efectivo(
            SimpleNamespace(estado=fila.estado_almacenado, fecha_fin=fila.fecha_fin),  # type: ignore[arg-type]
            referencia,
        )
        disponibles = max(fila.cupo_maximo - fila.inscritos_activos, 0)
        sin_registrar = max(fila.inscritos_activos - fila.presentes - fila.ausentes, 0)
        eventos.append(
            EventoConsolidadoItem(
                evento_id=fila.evento_id,
                titulo=fila.titulo,
                tipo=fila.tipo,
                modalidad=fila.modalidad,
                estado=estado_efectivo,
                fecha_inicio=fila.fecha_inicio,
                fecha_fin=fila.fecha_fin,
                organizador_id=fila.organizador_id,
                organizador_nombre=fila.organizador_nombre,
                cupo_maximo=fila.cupo_maximo,
                inscritos_activos=fila.inscritos_activos,
                disponibles=disponibles,
                ocupacion_pct=_calcular_porcentaje(fila.inscritos_activos, fila.cupo_maximo),
                cancelaciones=fila.cancelaciones,
                presentes=fila.presentes,
                ausentes=fila.ausentes,
                sin_registrar=sin_registrar,
                asistencia_pct=_calcular_porcentaje(fila.presentes, fila.inscritos_activos),
            )
        )

    cupo_total = sum(item.cupo_maximo for item in eventos)
    inscritos_totales = sum(item.inscritos_activos for item in eventos)
    presentes_totales = sum(item.presentes for item in eventos)
    totales = ConsolidadoTotales(
        total_eventos=len(eventos),
        cupo_total=cupo_total,
        inscritos_activos=inscritos_totales,
        disponibles=sum(item.disponibles for item in eventos),
        ocupacion_pct=_calcular_porcentaje(inscritos_totales, cupo_total),
        cancelaciones=sum(item.cancelaciones for item in eventos),
        presentes=presentes_totales,
        ausentes=sum(item.ausentes for item in eventos),
        sin_registrar=sum(item.sin_registrar for item in eventos),
        asistencia_pct=_calcular_porcentaje(presentes_totales, inscritos_totales),
    )
    return ConsolidadoSalida(eventos=eventos, totales=totales)


def listar_organizadores(db: Session, usuario: Usuario) -> list[tuple[int, str]]:
    """Lista organizadores visibles para el filtro del panel de coordinación."""
    _validar_coordinacion(usuario)
    return reporte_repo.listar_organizadores(db)


def enmascarar_documento(numero: str) -> str:
    """Enmascara números de documento antes de exponerlos en exportaciones."""
    return _enmascarar_documento(numero)


def sanitizar_celda_csv(valor: object) -> str:
    """Neutraliza celdas que inician con =, +, -, @ o caracteres de control (CWE-1236)."""
    texto = "" if valor is None else str(valor)
    if texto and (
        texto[0] in {"=", "+", "-", "@", "\t", "\r"}
        or texto.lstrip().startswith(("=", "+", "-", "@"))
    ):
        return f"'{texto}"
    return texto


def exportar_consolidado_csv(
    db: Session,
    filtros: ConsolidadoFiltros,
    usuario: Usuario,
    proveedor_ahora: ProveedorAhora = ahora_utc,
) -> str:
    """Exporta las filas filtradas del consolidado en formato CSV neutralizado."""
    consolidado = obtener_consolidado(db, filtros, usuario, proveedor_ahora=proveedor_ahora)
    buffer = io.StringIO()
    escritor = csv.writer(buffer, lineterminator="\n")
    escritor.writerow(
        [
            "evento_id",
            "titulo",
            "tipo",
            "modalidad",
            "estado",
            "fecha_inicio",
            "fecha_fin",
            "organizador_nombre",
            "cupo_maximo",
            "inscritos_activos",
            "disponibles",
            "ocupacion_pct",
            "cancelaciones",
            "presentes",
            "ausentes",
            "sin_registrar",
            "asistencia_pct",
        ]
    )
    for evento in consolidado.eventos:
        fila = [
            evento.evento_id,
            evento.titulo,
            evento.tipo,
            evento.modalidad,
            evento.estado,
            evento.fecha_inicio.isoformat(),
            evento.fecha_fin.isoformat(),
            evento.organizador_nombre,
            evento.cupo_maximo,
            evento.inscritos_activos,
            evento.disponibles,
            f"{evento.ocupacion_pct:.2f}",
            evento.cancelaciones,
            evento.presentes,
            evento.ausentes,
            evento.sin_registrar,
            f"{evento.asistencia_pct:.2f}",
        ]
        escritor.writerow([sanitizar_celda_csv(celda) for celda in fila])
    return buffer.getvalue()
