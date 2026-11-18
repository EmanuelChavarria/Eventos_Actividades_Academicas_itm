"""Pruebas unitarias y de integración del reporte consolidado de coordinación (E7 / PF-11)."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.errors import CodigosError, NoAutorizado
from app.core.fechas import ahora_utc
from app.models.asistencia import Asistencia
from app.models.enums import (
    EstadoAsistencia,
    EstadoEvento,
    EstadoInscripcion,
    PublicoObjetivo,
    Rol,
)
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario
from app.schemas.reporte import ConsolidadoFiltros
from app.services import reporte_service


def _login(client: TestClient, usuario: Usuario) -> None:
    """Inicia sesión en TestClient para fijar cookie HttpOnly."""
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "tipo_documento": usuario.tipo_documento,
            "numero_documento": usuario.numero_documento,
            "password": "ClaveSegura123!",
        },
        headers={"Origin": "https://testserver"},
    )
    assert resp.status_code == 200


def _crear_evento_escenario(
    db: Session,
    *,
    organizador_id: int,
    titulo: str,
    tipo: str = "conferencia",
    modalidad: str = "presencial",
    estado: str = EstadoEvento.PUBLICADO.value,
    cupo_maximo: int = 10,
    inicio: datetime | None = None,
    fin: datetime | None = None,
) -> Evento:
    base = inicio or datetime(2026, 6, 10, 14, 0, tzinfo=UTC)
    fin_dt = fin or (base + timedelta(hours=3))
    ev = Evento(
        titulo=titulo,
        descripcion=f"Descripción de {titulo}",
        tipo=tipo,
        fecha_inicio=base,
        fecha_fin=fin_dt,
        fecha_limite_inscripcion=base - timedelta(days=1),
        lugar="Auditorio A",
        modalidad=modalidad,
        publico_objetivo=PublicoObjetivo.TODOS.value,
        responsable_nombre="Coord Eventos",
        responsable_correo="eventos@example.edu",
        cupo_maximo=cupo_maximo,
        estado=estado,
        organizador_id=organizador_id,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def test_servicio_consolidado_rechaza_no_coordinacion(
    db_session: Session, crear_usuario_factory
) -> None:
    """RN-11: solo coordinación puede consultar el servicio consolidado."""
    org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Org Uno")
    part = crear_usuario_factory(rol=Rol.PARTICIPANTE, nombre="Part Uno")

    for usuario in (org, part):
        with pytest.raises(NoAutorizado) as exc_info:
            reporte_service.obtener_consolidado(
                db_session,
                ConsolidadoFiltros(),
                usuario,
            )
        assert exc_info.value.codigo == CodigosError.SIN_PERMISO


def test_servicio_consolidado_totales_y_cero_inscritos(
    db_session: Session, crear_usuario_factory
) -> None:
    """RN-09: asistencia_pct == 0.0 con 0 inscritos y totales coherentes con filas."""
    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coordinación")
    org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Org Académico")
    p1 = crear_usuario_factory(rol=Rol.PARTICIPANTE, nombre="Part 1")
    p2 = crear_usuario_factory(rol=Rol.PARTICIPANTE, nombre="Part 2")
    p3 = crear_usuario_factory(rol=Rol.PARTICIPANTE, nombre="Part 3")
    p4 = crear_usuario_factory(rol=Rol.PARTICIPANTE, nombre="Part 4")

    ahora_ref = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    ev1 = _crear_evento_escenario(
        db_session,
        organizador_id=org.id,
        titulo="Seminario IA",
        cupo_maximo=10,
        inicio=datetime(2026, 6, 10, 14, 0, tzinfo=UTC),
        fin=datetime(2026, 6, 10, 17, 0, tzinfo=UTC),  # Ya finalizado respecto a ahora_ref
    )
    _crear_evento_escenario(
        db_session,
        organizador_id=org.id,
        titulo="Taller Sin Inscritos",
        cupo_maximo=5,
        inicio=datetime(2026, 6, 20, 14, 0, tzinfo=UTC),
        fin=datetime(2026, 6, 20, 17, 0, tzinfo=UTC),
    )

    # En ev1: 3 activas (1 presente, 1 ausente, 1 sin registrar) + 1 cancelada
    ins1 = Inscripcion(
        evento_id=ev1.id, participante_id=p1.id, estado=EstadoInscripcion.ACTIVA.value
    )
    ins2 = Inscripcion(
        evento_id=ev1.id, participante_id=p2.id, estado=EstadoInscripcion.ACTIVA.value
    )
    ins3 = Inscripcion(
        evento_id=ev1.id, participante_id=p3.id, estado=EstadoInscripcion.ACTIVA.value
    )
    ins4 = Inscripcion(
        evento_id=ev1.id,
        participante_id=p4.id,
        estado=EstadoInscripcion.CANCELADA.value,
        cancelada_en=datetime(2026, 6, 8, 10, 0, tzinfo=UTC),
    )
    db_session.add_all([ins1, ins2, ins3, ins4])
    db_session.commit()
    db_session.refresh(ins1)
    db_session.refresh(ins2)

    db_session.add_all(
        [
            Asistencia(
                inscripcion_id=ins1.id,
                estado=EstadoAsistencia.PRESENTE.value,
                registrado_por_id=org.id,
                registrado_en=ahora_ref,
                actualizado_en=ahora_ref,
            ),
            Asistencia(
                inscripcion_id=ins2.id,
                estado=EstadoAsistencia.AUSENTE.value,
                registrado_por_id=org.id,
                registrado_en=ahora_ref,
                actualizado_en=ahora_ref,
            ),
        ]
    )
    db_session.commit()

    salida = reporte_service.obtener_consolidado(
        db_session,
        ConsolidadoFiltros(),
        coord,
        proveedor_ahora=lambda: ahora_ref,
    )

    assert len(salida.eventos) == 2
    fila1, fila2 = salida.eventos
    assert fila1.estado == "finalizado"
    assert fila1.inscritos_activos == 3
    assert fila1.disponibles == 7
    assert fila1.ocupacion_pct == pytest.approx(30.0)
    assert fila1.cancelaciones == 1
    assert fila1.presentes == 1
    assert fila1.ausentes == 1
    assert fila1.sin_registrar == 1
    assert fila1.asistencia_pct == pytest.approx(33.33)

    assert fila2.estado == "publicado"
    assert fila2.inscritos_activos == 0
    assert fila2.disponibles == 5
    assert fila2.ocupacion_pct == 0.0
    assert fila2.asistencia_pct == 0.0

    # Totales globales coherentes con las filas
    assert salida.totales.total_eventos == 2
    assert salida.totales.cupo_total == sum(e.cupo_maximo for e in salida.eventos)
    assert salida.totales.inscritos_activos == sum(e.inscritos_activos for e in salida.eventos)
    assert salida.totales.disponibles == sum(e.disponibles for e in salida.eventos)
    assert salida.totales.cancelaciones == sum(e.cancelaciones for e in salida.eventos)
    assert salida.totales.presentes == sum(e.presentes for e in salida.eventos)
    assert salida.totales.ausentes == sum(e.ausentes for e in salida.eventos)
    assert salida.totales.sin_registrar == sum(e.sin_registrar for e in salida.eventos)
    assert salida.totales.ocupacion_pct == pytest.approx(20.0)
    assert salida.totales.asistencia_pct == pytest.approx(33.33)


def test_csv_neutraliza_formulas_y_enmascara_documentos(
    db_session: Session, crear_usuario_factory
) -> None:
    """Seguridad CSV: celdas peligrosas (=,+,-,@) se neutralizan y se exporta consolidado."""
    assert reporte_service.sanitizar_celda_csv("=CMD|'/C calc'!A0") == "'=CMD|'/C calc'!A0"
    assert reporte_service.sanitizar_celda_csv("+1+1") == "'+1+1"
    assert reporte_service.sanitizar_celda_csv("-2+3") == "'-2+3"
    assert reporte_service.sanitizar_celda_csv("@SUM(A1:A2)") == "'@SUM(A1:A2)"
    assert reporte_service.sanitizar_celda_csv("Taller Normal") == "Taller Normal"
    assert reporte_service.enmascarar_documento("1020304567") == "••••4567"

    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coord CSV")
    org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="+Org Peligroso")
    _crear_evento_escenario(
        db_session,
        organizador_id=org.id,
        titulo='=HYPERLINK("http://evil","Click")',
    )

    csv_texto = reporte_service.exportar_consolidado_csv(
        db_session,
        ConsolidadoFiltros(),
        coord,
    )
    assert "'=HYPERLINK" in csv_texto
    assert "'+Org Peligroso" in csv_texto


def test_api_consolidado_requiere_coordinacion(client: TestClient, crear_usuario_factory) -> None:
    """RNF-06 / RN-11: anónimo recibe 401, organizador/participante 403 y coordinación 200."""
    resp_anon = client.get("/api/v1/reportes/consolidado")
    assert resp_anon.status_code == 401
    assert resp_anon.json()["error"]["codigo"] == CodigosError.CREDENCIALES_INVALIDAS

    for rol in (Rol.PARTICIPANTE, Rol.ORGANIZADOR):
        usuario = crear_usuario_factory(rol=rol)
        _login(client, usuario)
        resp_prohibido = client.get("/api/v1/reportes/consolidado")
        assert resp_prohibido.status_code == 403
        assert resp_prohibido.json()["error"]["codigo"] == CodigosError.SIN_PERMISO

    coord = crear_usuario_factory(rol=Rol.COORDINACION)
    _login(client, coord)
    resp_ok = client.get("/api/v1/reportes/consolidado")
    assert resp_ok.status_code == 200
    datos = resp_ok.json()
    assert datos["eventos"] == []
    assert datos["totales"]["total_eventos"] == 0


def test_api_consolidado_filtros_combinables_y_escape_like(
    client: TestClient, db_session: Session, crear_usuario_factory
) -> None:
    """RF-25 / PF-11: filtra por tipo, modalidad, estado, organizador, fechas y texto."""
    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coord Filtros")
    org_a = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Org Alfa")
    org_b = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Org Beta")
    ahora = ahora_utc()

    _crear_evento_escenario(
        db_session,
        organizador_id=org_a.id,
        titulo="Curso 100% Python_Pro",
        tipo="taller",
        modalidad="hibrida",
        estado=EstadoEvento.PUBLICADO.value,
        cupo_maximo=20,
        inicio=ahora - timedelta(days=5),
        fin=ahora - timedelta(days=4),  # finalizado
    )
    _crear_evento_escenario(
        db_session,
        organizador_id=org_b.id,
        titulo="Conferencia Java",
        tipo="conferencia",
        modalidad="virtual",
        estado=EstadoEvento.PUBLICADO.value,
        cupo_maximo=15,
        inicio=ahora + timedelta(days=3),
        fin=ahora + timedelta(days=4),  # publicado vigente
    )
    _crear_evento_escenario(
        db_session,
        organizador_id=org_a.id,
        titulo="Borrador Futuro",
        tipo="seminario",
        modalidad="presencial",
        estado=EstadoEvento.BORRADOR.value,
        cupo_maximo=30,
        inicio=ahora + timedelta(days=6),
        fin=ahora + timedelta(days=7),
    )

    _login(client, coord)

    # Filtro combinado sobre el evento finalizado e híbrido con comodín literal '%' y '_'
    resp = client.get(
        "/api/v1/reportes/consolidado",
        params={
            "tipo": "taller",
            "modalidad": "hibrida",
            "estado": "finalizado",
            "organizador_id": org_a.id,
            "texto": "100% Python_Pro",
            "fecha_desde": (ahora - timedelta(days=10)).isoformat(),
            "fecha_hasta": (ahora - timedelta(days=1)).isoformat(),
        },
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["totales"]["total_eventos"] == 1
    assert cuerpo["eventos"][0]["titulo"] == "Curso 100% Python_Pro"
    assert cuerpo["eventos"][0]["estado"] == "finalizado"

    # Buscar '%Pro' literal NO debe coincidir con 'Conferencia Java' (escape de LIKE)
    resp_like = client.get("/api/v1/reportes/consolidado", params={"texto": "Java%"})
    assert resp_like.status_code == 200
    assert resp_like.json()["totales"]["total_eventos"] == 0

    # Filtrar estado 'borrador' solo devuelve el borrador
    resp_borrador = client.get("/api/v1/reportes/consolidado", params={"estado": "borrador"})
    assert resp_borrador.status_code == 200
    assert [e["titulo"] for e in resp_borrador.json()["eventos"]] == ["Borrador Futuro"]


def test_api_consolidado_rechaza_fechas_sin_zona_o_rango_invertido(
    client: TestClient, crear_usuario_factory
) -> None:
    """RF-25 / RNF-08: rechaza 422 si falta zona horaria o si fecha_hasta < fecha_desde."""
    coord = crear_usuario_factory(rol=Rol.COORDINACION)
    _login(client, coord)

    resp_naive = client.get(
        "/api/v1/reportes/consolidado",
        params={"fecha_desde": "2026-06-10T10:00:00"},
    )
    assert resp_naive.status_code == 422

    resp_invertido = client.get(
        "/api/v1/reportes/consolidado",
        params={
            "fecha_desde": "2026-06-20T10:00:00-05:00",
            "fecha_hasta": "2026-06-10T10:00:00-05:00",
        },
    )
    assert resp_invertido.status_code == 422


def test_api_consolidado_csv_headers_contenido_y_permisos(
    client: TestClient, db_session: Session, crear_usuario_factory
) -> None:
    """E7 CSV: exige coordinación, BOM UTF-8, delimitador `;`, fechas locales y orden por ID."""
    assert client.get("/api/v1/reportes/consolidado/csv").status_code == 401

    org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Marta Díaz")
    _login(client, org)
    assert client.get("/api/v1/reportes/consolidado/csv").status_code == 403

    # Evento 1 finalizado (2026-06) y evento 2 futuro publicado para validar orden por evento_id
    ev1 = _crear_evento_escenario(
        db_session,
        organizador_id=org.id,
        titulo="=1+1 Capacitación Histórica",
        tipo="capacitacion",
        modalidad="hibrida",
        inicio=datetime(2026, 6, 20, 22, 1, 34, 50340, tzinfo=UTC),
        fin=datetime(2026, 6, 21, 1, 1, 34, 50340, tzinfo=UTC),
    )
    ahora = ahora_utc()
    ev2 = _crear_evento_escenario(
        db_session,
        organizador_id=org.id,
        titulo="Evaluación e Inducción",
        tipo="capacitacion",
        modalidad="virtual",
        inicio=ahora + timedelta(days=5),
        fin=ahora + timedelta(days=5, hours=2),
    )
    _crear_evento_escenario(
        db_session,
        organizador_id=org.id,
        titulo="Charla Limpia",
        tipo="conferencia",
    )

    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coord Export")
    _login(client, coord)
    resp = client.get("/api/v1/reportes/consolidado/csv", params={"tipo": "capacitacion"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert 'filename="consolidado_eventos.csv"' in resp.headers.get("content-disposition", "")

    # Firma UTF-8 BOM simple y sin doble BOM
    assert resp.content.startswith(b"\xef\xbb\xbf")
    assert not resp.content.startswith(b"\xef\xbb\xbf\xef\xbb\xbf")

    texto_sin_bom = resp.content.decode("utf-8-sig")
    lector = csv.DictReader(io.StringIO(texto_sin_bom), delimiter=";")
    assert lector.fieldnames == [
        "ID Evento",
        "Título",
        "Tipo",
        "Modalidad",
        "Estado",
        "Fecha Inicio",
        "Fecha Fin",
        "Organizador",
        "Cupo Máximo",
        "Inscritos Activos",
        "Disponibles",
        "Ocupación (%)",
        "Cancelaciones",
        "Presentes",
        "Ausentes",
        "Sin Registrar",
        "Asistencia (%)",
    ]

    filas = list(lector)
    assert len(filas) == 2
    assert [int(f["ID Evento"]) for f in filas] == [ev1.id, ev2.id]
    assert filas[0]["Título"] == "'=1+1 Capacitación Histórica"
    assert filas[0]["Tipo"] == "Capacitación"
    assert filas[0]["Modalidad"] == "Híbrida"
    assert filas[0]["Estado"] == "Finalizado"
    assert filas[1]["Estado"] == "Publicado"
    assert filas[0]["Organizador"] == "Marta Díaz"
    # 2026-06-20 22:01 UTC -> 2026-06-20 17:01 America/Bogota (-05:00), sin microsegundos ni +00:00
    assert filas[0]["Fecha Inicio"] == "2026-06-20 17:01"
    assert filas[0]["Fecha Fin"] == "2026-06-20 20:01"


def test_web_panel_consolidado_acceso_y_js_sin_innerhtml(
    client: TestClient, crear_usuario_factory
) -> None:
    """Web E7: /coordinacion/consolidado solo permite coordinación y JS evita innerHTML."""
    resp_anon = client.get("/coordinacion/consolidado", follow_redirects=False)
    assert resp_anon.status_code == 303
    assert resp_anon.headers["location"].endswith("/login")

    org = crear_usuario_factory(rol=Rol.ORGANIZADOR)
    _login(client, org)
    assert client.get("/coordinacion/consolidado", follow_redirects=False).status_code == 403

    coord = crear_usuario_factory(rol=Rol.COORDINACION)
    _login(client, coord)
    resp_ok = client.get("/coordinacion/consolidado")
    assert resp_ok.status_code == 200
    assert "/static/js/reportes.js" in resp_ok.text

    contenido_js = Path("app/static/js/reportes.js").read_text(encoding="utf-8")
    assert "innerHTML" not in contenido_js


def test_web_consolidado_estilos_tabla_y_navegacion_asistencia(
    client: TestClient,
    db_session: Session,
    crear_usuario_factory,
) -> None:
    """Regresión E7+E6+E5: CSS compartido, atributos en crearNodo y Ver asistencia."""
    org = crear_usuario_factory(rol=Rol.ORGANIZADOR, nombre="Org Visual")
    part = crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="8877665544",
        nombre="Part Visual",
    )
    coord = crear_usuario_factory(rol=Rol.COORDINACION, nombre="Coord Visual")
    evento = _crear_evento_escenario(
        db_session,
        organizador_id=org.id,
        titulo="Simposio Consolidado",
    )
    insc = Inscripcion(
        evento_id=evento.id,
        participante_id=part.id,
        estado=EstadoInscripcion.ACTIVA.value,
    )
    db_session.add(insc)
    db_session.commit()

    # Verificar hoja de estilos compartida para filtros, KPIs y tablas responsivas
    css = Path("app/static/css/styles.css").read_text(encoding="utf-8")
    for selector in (
        ".formulario-filtros",
        ".campo-busqueda",
        ".grid-totales",
        ".tarjeta-metrica",
        ".tabla-responsiva",
        ".col-numerica",
        ".acciones-tabla",
    ):
        assert selector in css

    # Verificar api.js procesa atributos (href en enlaces y value en options)
    api_js = Path("app/static/js/api.js").read_text(encoding="utf-8")
    assert "atributos = {}" in api_js
    assert "nodo.setAttribute(clave, String(valor))" in api_js

    # Verificar reportes.js usa mostrarAlerta(alerta, mensaje, "error") en el orden correcto
    reportes_js = Path("app/static/js/reportes.js").read_text(encoding="utf-8")
    assert 'mostrarAlerta(alerta, extraerMensajeError(error), "error")' in reportes_js
    assert "`/eventos/${item.evento_id}/asistencia`" in reportes_js

    # Coordinación consulta consolidado y navega a la vista de asistencia del evento
    _login(client, coord)
    panel = client.get("/coordinacion/consolidado")
    assert panel.status_code == 200
    assert "tabla-responsiva" in panel.text
    assert "campo-busqueda" in panel.text

    resp_asist_web = client.get(f"/eventos/{evento.id}/asistencia")
    assert resp_asist_web.status_code == 200
    assert 'href="/coordinacion/consolidado"' in resp_asist_web.text
    assert "tabla-responsiva" in resp_asist_web.text

    resp_asist_api = client.get(f"/api/v1/eventos/{evento.id}/asistencia")
    assert resp_asist_api.status_code == 200
    nomina = resp_asist_api.json()
    assert len(nomina) == 1
    assert nomina[0]["numero_documento"] == "••••5544"

    # Vista E5 mis inscripciones también usa tabla responsiva y conserva alerta al cancelar
    _login(client, part)
    resp_mias = client.get("/mis-inscripciones")
    assert resp_mias.status_code == 200
    assert "tabla-responsiva" in resp_mias.text
    inscripciones_js = Path("app/static/js/inscripciones.js").read_text(encoding="utf-8")
    assert ".innerHTML" not in inscripciones_js
    assert "limpiarAlerta: false" in inscripciones_js
