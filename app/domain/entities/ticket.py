from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Ticket:
    ticket_id: str
    titulo: str
    descripcion_problema: str
    descripcion_solucion: str
    categoria: str
    prioridad: str
    estado: str
    fecha_creacion: datetime
    fecha_cierre: datetime | None
    tags: list[str]
    usuario_creador: str
    sistema_afectado: str
    logs: dict[str, Any]
    causa_raiz: str | None = None
    pasos_diagnostico: str | None = None
    entorno: str | None = None
    version_sistema: str | None = None
    impacto: str | None = None
    resuelto_exitosamente: bool = True
