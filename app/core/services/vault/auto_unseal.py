import os
from core.bus import bus
from core.logger import get_logger
from core.services.vault.crypto import KEY_FILE

log = get_logger("AutoUnseal")

class AutoUnsealManager:
    def __init__(self):
        # Wir hören auf den Systemstart für den normalen Unseal (wenn KEY_FILE existiert)
        bus.subscribe("system:started")(self.attempt_auto_unseal)
        # Wir hören auf das Ready-Signal für den allerersten Init
        bus.subscribe("vault:ready_for_init")(self.handle_vault_ready)
        self._init_done = False

    async def handle_vault_ready(self, payload):
        """Wird gerufen, wenn der Vault-Server erreichbar, aber leer ist."""
        if self._init_done: return
        
        auto_key = os.getenv("LYNDRIX_MASTER_KEY")
        if auto_key and not os.path.exists(KEY_FILE):
            log.info("🪄 Vault signalisiert Init-Bereitschaft. Starte AUTO-INIT...")
            bus.emit("vault:init_requested", {"key": auto_key})
            self._init_done = True

    async def attempt_auto_unseal(self, payload):
        """Regulärer Unseal beim Booten, wenn das System schon initialisiert wurde."""
        auto_key = os.getenv("LYNDRIX_MASTER_KEY")
        if auto_key and os.path.exists(KEY_FILE):
            log.info("🔑 Master-Key gefunden. Starte AUTO-UNSEAL...")
            bus.emit("vault:unseal_requested", {"key": auto_key})

auto_unseal_manager = AutoUnsealManager()