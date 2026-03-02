# Security & Vault Integration

Sicherheit ist kein nachträgliches Feature in Lyndrix Core, sondern das Fundament. Anstatt Datenbank-Passwörter oder API-Keys (z.B. für Discord, Docker-Nodes oder Cloud-Provider) im Klartext zu speichern, nutzt Lyndrix **HashiCorp Vault**.

## Die Vault-Architektur

Vault ist ein Container, der strikt vom Hauptsystem isoliert ist.

- Lyndrix Core nutzt eine isolierte **KV v2 Secret Engine** unter dem Pfad `lyndrix/` für alle Plugin-Secrets.
- Daten können nur gespeichert und abgerufen werden, wenn der Vault "entsiegelt" (unsealed) ist.
- Nach einem Server-Neustart oder einem manuellen Seal-Vorgang ist der Vault automatisch gesperrt (`sealed`). Dies ist ein Sicherheitsmechanismus, der sicherstellt, dass selbst bei einem Kompromittieren des Servers die Secrets nicht direkt aus dem Vault gelesen werden können.

### Der Unseal-Prozess und der Master-Key

Beim ersten Start von Lyndrix Core, wenn der Vault noch nicht initialisiert ist, wird ein **Master-Key** generiert. Dieser Master-Key ist entscheidend:

1.  **Initialisierung:** Lyndrix generiert intern eine Reihe von "Unseal Keys" und einen "Root Token" für den Vault. Diese kritischen Informationen werden dann mit deinem Master-Key verschlüsselt und in einer lokalen Datei (`.vault_keys`) gespeichert.
2.  **Entsiegeln (Unseal):** Jedes Mal, wenn der Vault gesperrt ist (z.B. nach einem Neustart), musst du den Master-Key in der Lyndrix-UI eingeben. Lyndrix verwendet diesen Key, um die gespeicherten Unseal Keys und den Root Token zu entschlüsseln.
    _Technischer Ablauf:_ Aus der Datei `.vault_keys` werden Salt, Nonce und Tag extrahiert. Der Master-Key wird zusammen mit dem Salt durch **Argon2id** geleitet, um den Entschlüsselungs-Key zu generieren. Mit diesem Key und dem Nonce wird der Datensatz via **AES-GCM** entschlüsselt und der Tag verifiziert. Erst nach erfolgreicher Prüfung werden die Keys an den Vault gesendet, um ihn zu entsiegeln.
3.  **Automatisches Entsiegeln (Entwicklung):** Für Entwicklungsumgebungen kannst du den Master-Key auch über die Umgebungsvariable `LYNDRIX_MASTER_KEY` bereitstellen. Dies ermöglicht ein automatisches Entsiegeln des Vaults beim Start, ist aber für Produktionsumgebungen aus Sicherheitsgründen nicht empfohlen.

**WICHTIG:** Der Master-Key ist der einzige Schlüssel zu deinen Vault-Secrets. Geht er verloren, sind alle im Vault gespeicherten Daten unwiederbringlich verloren. Bewahre ihn an einem extrem sicheren Ort auf! Lyndrix selbst speichert den Master-Key niemals im Klartext.

Sobald der Vault entsiegelt ist, sendet Lyndrix das Event `vault:ready_for_data` an alle Plugins, damit diese ihre Konfigurationen und Secrets sicher laden können.

#### Technische Details der Verschlüsselung

Der Master-Key wird niemals direkt als Verschlüsselungsschlüssel verwendet oder gespeichert. Stattdessen dient er als **Passphrase**, aus der ein kryptografisch sicherer Schlüssel abgeleitet wird. Die Implementierung in `app/core/components/vault/logic/crypto.py` verwendet folgende Mechanismen:

1.  **Schlüsselableitung (Key Derivation):**
    Aus dem Master-Key wird mittels **Argon2id** (via `argon2-cffi`) ein 256-Bit (32 Byte) Schlüssel abgeleitet.
    - **Parameter:** Time Cost: 3, Memory Cost: 64 MB (65536 KB), Parallelism: 4.
    - **Salt:** Ein zufälliger 16-Byte Salt (`os.urandom(16)`) wird für jede Verschlüsselung neu generiert.

2.  **Symmetrische Verschlüsselung:**
    Die Vault-Zugangsdaten (`root_token` und `unseal_keys`) werden als JSON serialisiert und mit **AES-256-GCM** (`pycryptodome`) verschlüsselt.
    - **Modus:** Galois/Counter Mode (GCM) garantiert Vertraulichkeit und Integrität.
    - **Nonce:** Ein 16-Byte Initialisierungsvektor.
    - **Tag:** Ein 16-Byte Authentication Tag zur Verifizierung der Datenintegrität.

3.  **Speicherformat:**
    Die Datei `.vault_keys` enthält die binären Daten in folgender Reihenfolge:
    `[Salt (16B)] [Nonce (16B)] [Tag (16B)] [Ciphertext (n)]`

Beim Entsperren extrahiert Lyndrix Salt, Nonce und Tag, leitet den Schlüssel mit demselben Salt und Master-Key erneut ab und verifiziert die Integrität der Daten vor der Entschlüsselung.

---

## Secrets im Plugin nutzen

Als Plugin-Entwickler musst du dich nicht mit der komplexen Vault-API (hvac) herumschlagen. Der `ModuleContext` (`ctx`), den dein Plugin beim Start erhält, bietet dir sichere Sandbox-Funktionen.

### Secrets speichern

Speichere Konfigurationen oder Passwörter sicher ab. Der Core sorgt automatisch dafür, dass dein Plugin nur auf **seinen eigenen** Vault-Pfad zugreifen darf.

```python
def setup(ctx):
    # Speichert einen API Key verschlüsselt im Vault ab
    success = ctx.set_secret("discord_webhook", "[https://discord.com/api/webhooks/](https://discord.com/api/webhooks/)...")
    if success:
        ctx.log.info("Webhook sicher gespeichert!")

```

### Secrets abrufen

Lade die Daten bei Bedarf wieder in den Arbeitsspeicher deines Plugins. Achte darauf, dies erst nach dem Event `vault:ready_for_data` zu tun.

```python
@ctx.subscribe('vault:ready_for_data')
async def load_secrets(payload):
    webhook_url = ctx.get_secret("discord_webhook")
    if webhook_url:
        ctx.log.info("Webhook erfolgreich geladen.")

```

> ⚠️ **Sicherheits-Regel:** Logge niemals Secrets (`ctx.log.info(webhook_url)`)! Die Logs werden unverschlüsselt in der Datenbank und auf der Festplatte abgelegt.
