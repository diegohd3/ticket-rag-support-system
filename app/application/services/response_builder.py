from __future__ import annotations

from app.application.services.ticket_search_service import RankedTicket


class ResponseBuilder:
    def build_internal_support_response(
        self,
        query_text: str,
        ranked_tickets: list[RankedTicket],
    ) -> str:
        if not ranked_tickets:
            return (
                "No clear matches were found in the internal ticket base. "
                "Provide the exact error code, affected component, and reproduction steps "
                "to improve search precision."
            )

        best_match = ranked_tickets[0].ticket
        lines = [
            f"Based on historical incidents, the most relevant ticket is {best_match.ticket_id}.",
            f"Detected issue: {best_match.descripcion_problema}",
            f"Suggested solution: {best_match.descripcion_solucion}",
        ]

        if best_match.pasos_diagnostico:
            lines.append(f"Recommended diagnostic steps: {best_match.pasos_diagnostico}")

        lines.append("Recommendation priority: internal ticket knowledge base.")
        return "\n".join(lines)
