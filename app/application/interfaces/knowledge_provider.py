from __future__ import annotations

from abc import ABC, abstractmethod


class KnowledgeProvider(ABC):
    @abstractmethod
    def search(self, query_text: str, limit: int) -> list[str]:
        raise NotImplementedError
