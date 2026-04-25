from __future__ import annotations

from abc import ABC, abstractmethod

from research_intel.models import SourceResult


class DataSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, target: str) -> SourceResult:
        raise NotImplementedError

