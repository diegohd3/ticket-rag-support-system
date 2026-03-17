from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.infrastructure.db.models.ticket_model import TicketModel
from app.infrastructure.db.session import SessionLocal


def _build_demo_tickets() -> list[TicketModel]:
    now = datetime.now(UTC)
    return [
        TicketModel(
            ticket_id="TCK-1001",
            titulo="Error ERR-401 al iniciar sesion en portal interno",
            descripcion_problema=(
                "Usuarios de soporte no pueden iniciar sesion en el portal administrativo. "
                "El sistema devuelve ERR-401 despues de autenticarse con SSO."
            ),
            descripcion_solucion=(
                "Se renovaron certificados expirados del proveedor SSO y se limpiaron tokens "
                "de sesion en cache de Redis."
            ),
            categoria="autenticacion",
            prioridad="alta",
            estado="cerrado",
            fecha_creacion=now - timedelta(days=19),
            fecha_cierre=now - timedelta(days=18),
            tags=["sso", "auth", "portal", "err-401"],
            usuario_creador="maria.romero",
            sistema_afectado="portal-soporte",
            logs={"error_code": "ERR-401", "component": "auth-gateway", "attempts": 238},
            causa_raiz="Certificado SSO expirado.",
            pasos_diagnostico=(
                "Validar vigencia de certificados, revisar callbacks de OAuth y auditar latencia "
                "de auth-gateway."
            ),
            entorno="produccion",
            version_sistema="2.13.7",
            impacto="Usuarios bloqueados para atender incidencias.",
            resuelto_exitosamente=True,
        ),
        TicketModel(
            ticket_id="TCK-1002",
            titulo="Latencia alta en API de tickets",
            descripcion_problema=(
                "Consultas de listado superan 8 segundos en horarios pico. Se observan timeouts en "
                "clientes web."
            ),
            descripcion_solucion=(
                "Se crearon indices compuestos en filtros frecuentes "
                "y se aplico paginacion estricta con limites maximos."
            ),
            categoria="performance",
            prioridad="media",
            estado="cerrado",
            fecha_creacion=now - timedelta(days=40),
            fecha_cierre=now - timedelta(days=39),
            tags=["api", "latencia", "postgres", "indexacion"],
            usuario_creador="jesus.herrera",
            sistema_afectado="ticket-api",
            logs={"p95_ms": 8100, "query": "SELECT tickets ...", "table": "tickets"},
            causa_raiz="Falta de indices y over-fetching.",
            pasos_diagnostico="Analizar EXPLAIN ANALYZE, revisar plan de ejecucion y payload.",
            entorno="produccion",
            version_sistema="3.1.0",
            impacto="Experiencia lenta en mesa de ayuda.",
            resuelto_exitosamente=True,
        ),
        TicketModel(
            ticket_id="TCK-1003",
            titulo="Fallo HTTP500 al generar reporte semanal",
            descripcion_problema=(
                "Modulo de reporteria devuelve HTTP500 cuando el rango supera 30 dias. "
                "Aparece stack trace en worker."
            ),
            descripcion_solucion=(
                "Se dividio la consulta por lotes y se corrigio serializacion "
                "de fechas en timezone UTC."
            ),
            categoria="backend",
            prioridad="alta",
            estado="cerrado",
            fecha_creacion=now - timedelta(days=12),
            fecha_cierre=now - timedelta(days=11),
            tags=["reportes", "http500", "batch", "utc"],
            usuario_creador="ana.molina",
            sistema_afectado="reporting-service",
            logs={"error_code": "HTTP500", "worker": "reports-worker", "trace_id": "7af12"},
            causa_raiz="Consulta monolitica sin paginacion + parsing de fechas ambiguo.",
            pasos_diagnostico="Reproducir con rango 60 dias y validar serializacion JSON.",
            entorno="produccion",
            version_sistema="4.2.5",
            impacto="Reporte de gerencia no disponible.",
            resuelto_exitosamente=True,
        ),
        TicketModel(
            ticket_id="TCK-1004",
            titulo="Desincronizacion de tags en tickets migrados",
            descripcion_problema=(
                "Tickets migrados desde sistema legado llegan sin tags o con tags truncadas."
            ),
            descripcion_solucion=(
                "Se normalizo parser CSV legado y se agrego validacion de longitud en el ETL."
            ),
            categoria="datos",
            prioridad="media",
            estado="cerrado",
            fecha_creacion=now - timedelta(days=30),
            fecha_cierre=now - timedelta(days=29),
            tags=["etl", "migracion", "tags", "calidad-datos"],
            usuario_creador="carlos.ruiz",
            sistema_afectado="data-pipeline",
            logs={"job_id": "etl-2208", "discarded_rows": 421},
            causa_raiz="Incompatibilidad de formato delimitado.",
            pasos_diagnostico="Auditar archivo fuente, encoding y columnas opcionales.",
            entorno="staging",
            version_sistema="1.9.2",
            impacto="Baja precisión en búsquedas por tags.",
            resuelto_exitosamente=True,
        ),
        TicketModel(
            ticket_id="TCK-1005",
            titulo="Error E503 en integracion con proveedor de correo",
            descripcion_problema=(
                "Notificaciones de cierre de ticket fallan intermitentemente con E503."
            ),
            descripcion_solucion=(
                "Se aplico retry exponencial con circuit breaker y cola de reintentos asincrona."
            ),
            categoria="integraciones",
            prioridad="alta",
            estado="cerrado",
            fecha_creacion=now - timedelta(days=9),
            fecha_cierre=now - timedelta(days=8),
            tags=["email", "e503", "retry", "circuit-breaker"],
            usuario_creador="sofia.perez",
            sistema_afectado="notification-service",
            logs={"error_code": "E503", "provider": "mail-cloud", "fail_rate": 0.37},
            causa_raiz="Rate limiting no manejado correctamente.",
            pasos_diagnostico="Verificar cuota de proveedor y headers de backoff.",
            entorno="produccion",
            version_sistema="5.0.1",
            impacto="Usuarios no reciben confirmaciones.",
            resuelto_exitosamente=True,
        ),
        TicketModel(
            ticket_id="TCK-1006",
            titulo="Busqueda interna no encuentra codigos de error",
            descripcion_problema=(
                "Analistas reportan que al buscar ERR-401 o HTTP500 no aparecen tickets "
                "relevantes en el primer bloque."
            ),
            descripcion_solucion=(
                "Se ajusto ranking para ponderar mas coincidencias por codigo de error y tags."
            ),
            categoria="busqueda",
            prioridad="media",
            estado="cerrado",
            fecha_creacion=now - timedelta(days=5),
            fecha_cierre=now - timedelta(days=4),
            tags=["search", "ranking", "error-codes"],
            usuario_creador="laura.santos",
            sistema_afectado="support-assistant",
            logs={"top_k": 10, "metric": "nDCG", "before": 0.52, "after": 0.74},
            causa_raiz="Ponderacion uniforme de señales heterogeneas.",
            pasos_diagnostico="Comparar ranking manual vs ranking automatico con query reales.",
            entorno="staging",
            version_sistema="0.1.0",
            impacto="Recomendaciones poco útiles para soporte.",
            resuelto_exitosamente=True,
        ),
        TicketModel(
            ticket_id="TCK-1007",
            titulo="Incidente abierto: caida parcial en ingestion de logs",
            descripcion_problema=(
                "Se pierden eventos de diagnostico durante picos de trafico. No hay trazabilidad "
                "completa para nuevos incidentes."
            ),
            descripcion_solucion="Pendiente, incidente en investigacion.",
            categoria="observabilidad",
            prioridad="alta",
            estado="abierto",
            fecha_creacion=now - timedelta(days=1),
            fecha_cierre=None,
            tags=["logs", "ingestion", "kafka", "incidente-abierto"],
            usuario_creador="oncall.engineer",
            sistema_afectado="log-ingestor",
            logs={"dropped_events": 12450, "cluster": "kafka-prod-2"},
            causa_raiz=None,
            pasos_diagnostico="Monitorear lag de consumidores y saturacion de particiones.",
            entorno="produccion",
            version_sistema="2.4.0",
            impacto="Diagnostico incompleto de incidencias nuevas.",
            resuelto_exitosamente=False,
        ),
        TicketModel(
            ticket_id="TCK-1008",
            titulo="Error ERR-422 al crear ticket con adjuntos grandes",
            descripcion_problema=(
                "Al adjuntar archivos de mas de 15MB, el backend devuelve ERR-422 aunque el limite "
                "configurado es 25MB."
            ),
            descripcion_solucion=(
                "Se corrigio validacion en gateway que usaba limite legacy de 10MB y se unifico "
                "configuracion en todos los servicios."
            ),
            categoria="validacion",
            prioridad="media",
            estado="cerrado",
            fecha_creacion=now - timedelta(days=16),
            fecha_cierre=now - timedelta(days=15),
            tags=["adjuntos", "err-422", "gateway", "upload"],
            usuario_creador="miguel.torres",
            sistema_afectado="ticket-gateway",
            logs={"error_code": "ERR-422", "limit_mb": 10, "expected_limit_mb": 25},
            causa_raiz="Diferencia de configuraciones entre servicios.",
            pasos_diagnostico="Comparar variables de entorno y validadores de payload.",
            entorno="produccion",
            version_sistema="3.7.4",
            impacto="Usuarios no pueden cargar evidencia completa.",
            resuelto_exitosamente=True,
        ),
    ]


def run_seed() -> None:
    with SessionLocal() as session:
        already_exists = session.execute(select(TicketModel.id).limit(1)).scalar_one_or_none()
        if already_exists:
            print("Seed omitido: ya existen tickets en la base de datos.")
            return

        records = _build_demo_tickets()
        session.add_all(records)
        session.commit()
        print(f"Seed completado: {len(records)} tickets insertados.")


if __name__ == "__main__":
    run_seed()
