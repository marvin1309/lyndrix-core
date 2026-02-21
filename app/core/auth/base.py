from abc import ABC, abstractmethod
from typing import Optional, Dict

class BaseAuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, credentials: Dict) -> Optional[Dict]:
        """Prüft die Logindaten und gibt User-Info zurück oder None."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass