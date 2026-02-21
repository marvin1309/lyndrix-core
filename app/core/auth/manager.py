import os
from typing import List, Dict, Optional
from core.auth.base import BaseAuthProvider

class AuthManager:
    def __init__(self):
        self.providers: Dict[str, BaseAuthProvider] = {}

    def register_provider(self, provider: BaseAuthProvider):
        name = provider.get_provider_name()
        self.providers[name] = provider
        print(f"[Auth] Provider '{name}' registriert.")

    async def login(self, username: str, password: str, preferred_provider: str = "local"):
        credentials = {"username": username, "password": password}
        if preferred_provider in self.providers:
            # WICHTIG: await hier!
            user_data = await self.providers[preferred_provider].authenticate(credentials)
            return user_data
        return None

# Globaler Instanz-Speicher
auth_manager = AuthManager()