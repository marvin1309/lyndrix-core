# 🔐 Security & Vault Integration

Sicherheit ist kein nachträgliches Feature in Lyndrix Core, sondern das Fundament. Anstatt Datenbank-Passwörter oder API-Keys (z.B. für Discord, Docker-Nodes oder Cloud-Provider) im Klartext zu speichern, nutzt Lyndrix **HashiCorp Vault**.

## Die Vault-Architektur

Vault ist ein Container, der strikt vom Hauptsystem isoliert ist.

- Lyndrix Core kann Daten nur speichern und abrufen, wenn der Vault "entsiegelt" (unsealed) ist.
- Nach einem Server-Neustart ist der Vault automatisch gesperrt. Er muss durch Eingabe des `Master-Keys` in der Lyndrix-UI (oder per `.env` Variable in Dev-Umgebungen) wieder freigeschaltet werden.

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

Lade die Daten bei Bedarf wieder in den Arbeitsspeicher deines Plugins.

```python
def setup(ctx):
    webhook_url = ctx.get_secret("discord_webhook")
    if not webhook_url:
        ctx.log.warning("Kein Webhook konfiguriert!")

```

> ⚠️ **Sicherheits-Regel:** Logge niemals Secrets (`ctx.log.info(webhook_url)`)! Die Logs werden unverschlüsselt in der Datenbank und auf der Festplatte abgelegt.
