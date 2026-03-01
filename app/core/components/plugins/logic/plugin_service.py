import os
import sys
import shutil
import asyncio
import zipfile
import httpx
from pathlib import Path

from core.logger import get_logger
from core.bus import bus

log = get_logger("PluginService")

class PluginService:
    def __init__(self):
        # Pfad zum Plugin-Verzeichnis (z.B. app/plugins)
        self.plugin_dir = Path("plugins")
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # GitHub API Base für Repository-Infos
        self.github_api_base = "https://api.github.com/repos"

    def _extract_repo_info(self, github_url: str):
        """Macht aus 'https://github.com/user/repo' ein Tuple ('user', 'repo')"""
        parts = github_url.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        raise ValueError("Ungültige GitHub URL")

    async def install_plugin(self, github_url: str):
        """Lädt ein Plugin von GitHub herunter, installiert es und lädt die Requirements."""
        user, repo = self._extract_repo_info(github_url)
        plugin_path = self.plugin_dir / repo
        
        log.info(f"📥 Starte Installation von {repo} aus {github_url}...")
        bus.emit("plugin:install_started", {"repo": repo})

        if plugin_path.exists():
            log.warning(f"⚠️ Plugin {repo} existiert bereits. Nutze Update.")
            return False

        try:
            # 1. Standard-Branch ermitteln (main oder master)
            async with httpx.AsyncClient() as client:
                api_url = f"{self.github_api_base}/{user}/{repo}"
                repo_info = (await client.get(api_url)).json()
                default_branch = repo_info.get("default_branch", "main")
                
                # 2. ZIP herunterladen
                zip_url = f"{github_url}/archive/refs/heads/{default_branch}.zip"
                zip_path = self.plugin_dir / f"{repo}.zip"
                
                log.info(f"⬇️ Lade {zip_url} herunter...")
                response = await client.get(zip_url, follow_redirects=True)
                response.raise_for_status()
                
                with open(zip_path, 'wb') as f:
                    f.write(response.content)

            # 3. ZIP entpacken
            log.info("📦 Entpacke Dateien...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # GitHub packt alles in einen Unterordner (z.B. lyndrix-meeting-bingo-main)
                root_folder = zip_ref.namelist()[0]
                zip_ref.extractall(self.plugin_dir)
            
            # Ordner umbenennen zu sauberem Repo-Namen und aufräumen
            extracted_dir = self.plugin_dir / root_folder.strip("/")
            extracted_dir.rename(plugin_path)
            zip_path.unlink() # ZIP löschen

            # 4. Requirements installieren
            await self._install_requirements(plugin_path)

            log.info(f"✅ Plugin {repo} erfolgreich installiert!")
            bus.emit("plugin:installed", {"repo": repo, "path": str(plugin_path)})
            
            # Jetzt dem Manager sagen, dass er das neue Plugin laden soll
            from core.components.plugins.logic.manager import module_manager
            module_manager.load_module(repo) # Angenommen, dein Manager hat so eine Funktion

            return True

        except Exception as e:
            log.error(f"❌ Fehler bei der Installation von {repo}: {str(e)}")
            # Aufräumen bei Fehler
            if plugin_path.exists():
                shutil.rmtree(plugin_path)
            bus.emit("plugin:install_failed", {"repo": repo, "error": str(e)})
            return False

    async def update_plugin(self, github_url: str):
        """Aktualisiert ein Plugin (Deinstallieren -> Neu installieren)."""
        user, repo = self._extract_repo_info(github_url)
        log.info(f"🔄 Starte Update für {repo}...")
        
        await self.uninstall_plugin(repo)
        await self.install_plugin(github_url)

    async def uninstall_plugin(self, plugin_name: str):
        """Entfernt ein Plugin komplett vom System."""
        plugin_path = self.plugin_dir / plugin_name
        
        if not plugin_path.exists():
            log.warning(f"⚠️ Plugin {plugin_name} nicht gefunden.")
            return False

        log.info(f"🗑️ Deinstalliere Plugin {plugin_name}...")
        
        try:
            # Dem Manager sagen, dass das Plugin entladen werden soll
            from core.components.plugins.logic.manager import module_manager
            # module_manager.unload_module(plugin_name) # Falls implementiert
            
            shutil.rmtree(plugin_path)
            log.info(f"✅ Plugin {plugin_name} deinstalliert.")
            bus.emit("plugin:uninstalled", {"repo": plugin_name})
            return True
        except Exception as e:
            log.error(f"❌ Fehler bei der Deinstallation von {plugin_name}: {str(e)}")
            return False

    async def _install_requirements(self, plugin_path: Path):
        """Installiert externe Abhängigkeiten aus der requirements.txt des Plugins."""
        req_file = plugin_path / "requirements.txt"
        if req_file.exists():
            log.info(f"⚙️ Installiere Python-Abhängigkeiten für {plugin_path.name}...")
            # Wir nutzen sys.executable, um sicherzustellen, dass pip im korrekten .venv ausgeführt wird
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", "-r", str(req_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                log.error(f"⚠️ Fehler beim Installieren der Requirements:\n{stderr.decode()}")
            else:
                log.info(f"✅ Requirements erfolgreich installiert.")

# Singleton-Instanz
plugin_service = PluginService()