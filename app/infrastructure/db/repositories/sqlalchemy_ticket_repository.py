from __future__ import annotations

from sqlalchemy import Select, Text, literal, or_, select
from sqlalchemy.orm import Session

from app.application.interfaces.ticket_repository import TicketRepository
from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_query import SearchQuery
from app.infrastructure.db.models.ticket_model import TicketModel


class SqlAlchemyTicketRepository(TicketRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        statement = (
            select(TicketModel)
            .order_by(TicketModel.fecha_creacion.desc())
            .limit(limit)
            .offset(offset)
        )
        models = self._session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def search_candidates(self, query: SearchQuery, limit: int) -> list[Ticket]:
        statement: Select[tuple[TicketModel]] = select(TicketModel)
        filters = []

        if query.normalized_text:
            like_value = f"%{query.normalized_text}%"
            filters.append(
                or_(
                    TicketModel.titulo.ilike(like_value),
                    TicketModel.descripcion_problema.ilike(like_value),
                    TicketModel.descripcion_solucion.ilike(like_value),
                    TicketModel.causa_raiz.ilike(like_value),
                    TicketModel.pasos_diagnostico.ilike(like_value),
                )
            )

        for keyword in query.keywords:
            like_value = f"%{keyword}%"
            filters.append(
                or_(
                    TicketModel.titulo.ilike(like_value),
                    TicketModel.descripcion_problema.ilike(like_value),
                    TicketModel.descripcion_solucion.ilike(like_value),
                    TicketModel.categoria.ilike(like_value),
                    TicketModel.sistema_afectado.ilike(like_value),
                )
            )

        for code in query.error_codes:
            like_value = f"%{code}%"
            filters.append(
                or_(
                    TicketModel.descripcion_problema.ilike(like_value),
                    TicketModel.descripcion_solucion.ilike(like_value),
                    TicketModel.logs.cast(Text).ilike(like_value),
                )
            )

        if query.tags:
            filters.append(TicketModel.tags.overlap(query.tags))

        if filters:
            statement = statement.where(or_(*filters))

        statement = statement.order_by(TicketModel.fecha_creacion.desc()).limit(limit)
        models = self._session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def semantic_search(
        self,
        query_embedding: list[float],
        limit: int,
    ) -> list[tuple[Ticket, float]]:
        similarity_score = (
            literal(1.0) - TicketModel.embedding.cosine_distance(query_embedding)
        ).label(
            "semantic_score",
        )
        statement = (
            select(TicketModel, similarity_score)
            .where(TicketModel.embedding.is_not(None))
            .order_by(similarity_score.desc())
            .limit(limit)
        )
        rows = self._session.execute(statement).all()
        return [(self._to_domain(model), float(score)) for model, score in rows]

    def list_tickets_without_embeddings(self, limit: int) -> list[Ticket]:
        statement = (
            select(TicketModel)
            .where(TicketModel.embedding.is_(None))
            .order_by(TicketModel.fecha_creacion.asc())
            .limit(limit)
        )
        models = self._session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def update_ticket_embedding(self, ticket_id: str, embedding: list[float]) -> bool:
        statement = select(TicketModel).where(TicketModel.ticket_id == ticket_id)
        model = self._session.execute(statement).scalar_one_or_none()
        if not model:
            return False

        model.embedding = embedding
        self._session.add(model)
        self._session.commit()
        return True

    def create_ticket(self, ticket: Ticket) -> Ticket:
        model = TicketModel(
            ticket_id=ticket.ticket_id,
            titulo=ticket.titulo,
            descripcion_problema=ticket.descripcion_problema,
            descripcion_solucion=ticket.descripcion_solucion,
            categoria=ticket.categoria,
            prioridad=ticket.prioridad,
            estado=ticket.estado,
            fecha_creacion=ticket.fecha_creacion,
            fecha_cierre=ticket.fecha_cierre,
            tags=ticket.tags,
            usuario_creador=ticket.usuario_creador,
            sistema_afectado=ticket.sistema_afectado,
            logs=ticket.logs,
            causa_raiz=ticket.causa_raiz,
            pasos_diagnostico=ticket.pasos_diagnostico,
            entorno=ticket.entorno,
            version_sistema=ticket.version_sistema,
            impacto=ticket.impacto,
            resuelto_exitosamente=ticket.resuelto_exitosamente,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: TicketModel) -> Ticket:
        return Ticket(
            ticket_id=model.ticket_id,
            titulo=model.titulo,
            descripcion_problema=model.descripcion_problema,
            descripcion_solucion=model.descripcion_solucion,
            categoria=model.categoria,
            prioridad=model.prioridad,
            estado=model.estado,
            fecha_creacion=model.fecha_creacion,
            fecha_cierre=model.fecha_cierre,
            tags=model.tags or [],
            usuario_creador=model.usuario_creador,
            sistema_afectado=model.sistema_afectado,
            logs=model.logs or {},
            causa_raiz=model.causa_raiz,
            pasos_diagnostico=model.pasos_diagnostico,
            entorno=model.entorno,
            version_sistema=model.version_sistema,
            impacto=model.impacto,
            resuelto_exitosamente=model.resuelto_exitosamente,
        )
