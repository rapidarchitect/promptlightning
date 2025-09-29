from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable
from ..model import TemplateSpec

class Registry(ABC):
    @abstractmethod
    def list_ids(self) -> Iterable[str]: ...
    @abstractmethod
    def load(self, template_id: str) -> TemplateSpec: ...