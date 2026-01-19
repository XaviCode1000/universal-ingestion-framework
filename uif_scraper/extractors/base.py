from abc import ABC, abstractmethod
from typing import Any, Dict


class IExtractor(ABC):
    @abstractmethod
    async def extract(self, content: Any, url: str) -> Dict[str, Any]:
        pass
