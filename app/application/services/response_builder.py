from __future__ import annotations

from app.application.services.ticket_search_service import RankedTicket


class ResponseBuilder:
    def build_internal_support_response(self, query_text: str, ranked_tickets: list[RankedTicket]) -> str:
        if not ranked_tickets:
            return (
                "No encontré coincidencias claras en la base interna. "
                "Captura el error exacto, componente afectado y pasos de reproducción "
                "para una búsqueda más precisa."
            )

        best_match = ranked_tickets[0].ticket
        lines = [
            f"Basado en incidentes históricos, el ticket más relevante es {best_match.ticket_id}.",
            f"Problema detectado: {best_match.descripcion_problema}",
            f"Solución sugerida: {best_match.descripcion_solucion}",
        ]

        if best_match.pasos_diagnostico:
            lines.append(f"Pasos de diagnóstico recomendados: {best_match.pasos_diagnostico}")

        lines.append("La recomendación se prioriza usando la base de tickets interna.")
        return "\n".join(lines)
