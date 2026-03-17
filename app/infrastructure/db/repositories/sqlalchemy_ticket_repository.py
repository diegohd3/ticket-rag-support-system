from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, Text, func, literal, or_, select, text
from sqlalchemy.orm import Session

from app.application.interfaces.ticket_repository import TicketRepository
from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_filters import SearchFilters
from app.domain.value_objects.search_query import SearchQuery
from app.infrastructure.db.models.ticket_model import TicketModel


class SqlAlchemyTicketRepository(TicketRepository):
    def __init__(self, session: Session, vector_probes: int = 10) -> None:
        self._session = session
        self._vector_probes = vector_probes

    def count_tickets(self) -> int:
        statement = select(func.count(TicketModel.id))
        return int(self._session.execute(statement).scalar_one())

    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        statement = (
            select(TicketModel)
            .order_by(TicketModel.fecha_creacion.desc())
            .limit(limit)
            .offset(offset)
        )
        models = self._session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def get_ticket_by_ticket_id(self, ticket_id: str) -> Ticket | None:
        model = self._get_model_by_ticket_id(ticket_id)
        if not model:
            return None
        return self._to_domain(model)

    def search_candidates(self, query: SearchQuery, limit: int) -> list[Ticket]:
        statement: Select[tuple[TicketModel]] = select(TicketModel)
        statement = self._apply_metadata_filters(statement, query.filters)
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
        filters: SearchFilters | None = None,
    ) -> list[tuple[Ticket, float]]:
        if self._vector_probes > 0:
            probes = int(self._vector_probes)
            self._session.execute(text(f"SET LOCAL ivfflat.probes = {probes}"))

        distance = TicketModel.embedding.cosine_distance(query_embedding)
        similarity_score = (literal(1.0) - distance).label("semantic_score")
        statement = select(TicketModel, similarity_score).where(TicketModel.embedding.is_not(None))
        statement = self._apply_metadata_filters(statement, filters)
        # Order by vector distance to let pgvector ANN indexes participate.
        statement = statement.order_by(distance.asc()).limit(limit)
        rows = self._session.execute(statement).all()
        return [(self._to_domain(model), float(score)) for model, score in rows]

    def list_tickets_without_embeddings(self, limit: int, offset: int = 0) -> list[Ticket]:
        statement = (
            select(TicketModel)
            .where(TicketModel.embedding.is_(None))
            .order_by(TicketModel.fecha_creacion.asc())
            .limit(limit)
            .offset(offset)
        )
        models = self._session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def list_tickets_with_stale_embeddings(
        self,
        limit: int,
        embedding_model: str,
        offset: int = 0,
    ) -> list[Ticket]:
        statement = (
            select(TicketModel)
            .where(
                or_(
                    TicketModel.embedding.is_(None),
                    TicketModel.embedding_updated_at.is_(None),
                    TicketModel.updated_at > TicketModel.embedding_updated_at,
                    TicketModel.embedding_model.is_(None),
                    TicketModel.embedding_model != embedding_model,
                )
            )
            .order_by(TicketModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = self._session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def update_ticket_embedding(
        self,
        ticket_id: str,
        embedding: list[float],
        embedding_model: str,
    ) -> bool:
        model = self._get_model_by_ticket_id(ticket_id)
        if not model:
            return False

        model.embedding = embedding
        model.embedding_model = embedding_model
        model.embedding_updated_at = datetime.now(UTC)
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

    def update_ticket_fields(self, ticket_id: str, fields: dict[str, Any]) -> Ticket | None:
        model = self._get_model_by_ticket_id(ticket_id)
        if not model:
            return None

        for field_name, value in fields.items():
            if hasattr(model, field_name):
                setattr(model, field_name, value)

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def _get_model_by_ticket_id(self, ticket_id: str) -> TicketModel | None:
        statement = select(TicketModel).where(TicketModel.ticket_id == ticket_id)
        return self._session.execute(statement).scalar_one_or_none()

    @staticmethod
    def _apply_metadata_filters(
        statement: Select[tuple[TicketModel]] | Select[tuple[TicketModel, float]],
        filters: SearchFilters | None,
    ) -> Select:
        if not filters:
            return statement

        if filters.categoria:
            value = f"%{filters.categoria.strip()}%"
            statement = statement.where(TicketModel.categoria.ilike(value))
        if filters.prioridad:
            value = f"%{filters.prioridad.strip()}%"
            statement = statement.where(TicketModel.prioridad.ilike(value))
        if filters.estado:
            value = f"%{filters.estado.strip()}%"
            statement = statement.where(TicketModel.estado.ilike(value))
        if filters.sistema_afectado:
            value = f"%{filters.sistema_afectado.strip()}%"
            statement = statement.where(
                TicketModel.sistema_afectado.ilike(value)
            )

        return statement

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
