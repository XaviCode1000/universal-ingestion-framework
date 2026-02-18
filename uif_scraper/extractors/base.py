from abc import ABC, abstractmethod
from typing import Any


class IExtractor(ABC):
    @abstractmethod
    async def extract(self, content: Any, url: str) -> dict[str, Any]:
        pass
