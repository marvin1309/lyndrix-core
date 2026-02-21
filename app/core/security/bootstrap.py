import os
import json
import base64
from argon2 import PasswordHasher, low_level
from Crypto.Cipher import AES

# Pfad zur verschlüsselten Schlüsseldatei
KEY_FILE = "/data/security/vault_keys.enc"

def derive_key(master_key: str, salt: bytes) -> bytes:
    """Nutzt Argon2id, um einen 256-Bit Key aus der Passphrase zu generieren."""
    return low_level.hash_secret_raw(
        secret=master_key.encode(),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4, 
        hash_len=32,
        type=low_level.Type.ID
    )

def encrypt_vault_data(master_key: str, vault_payload: dict) -> bytes:
    """Verschlüsselt Vault-Keys mit AES-256-GCM."""
    salt = os.urandom(16)
    key = derive_key(master_key, salt)
    
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(vault_payload).encode())
    
    # Wir speichern: Salt (16b) + Nonce (16b) + Tag (16b) + Ciphertext
    return salt + cipher.nonce + tag + ciphertext

def decrypt_vault_data(master_key: str, encrypted_blob: bytes) -> dict:
    """Entschlüsselt die Daten mit dem Master Key."""
    salt = encrypted_blob[:16]
    nonce = encrypted_blob[16:32]
    tag = encrypted_blob[32:48]
    ciphertext = encrypted_blob[48:]
    
    key = derive_key(master_key, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(decrypted_data.decode())

# --- Ergänzung für Passwort-Hashing (Benutzer-Logins) ---

# Wir instanziieren den Standard-Hasher für User-Passwörter
# Dieser fügt automatisch ein zufälliges Salt hinzu und speichert es im Hash-String
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    type=low_level.Type.ID
)

def hash_password(password: str) -> str:
    """Erzeugt einen sicheren Argon2-Hash für die Datenbank."""
    return ph.hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    """Vergleicht einen gespeicherten Hash mit einer Passworteingabe."""
    try:
        return ph.verify(hashed_password, password)
    except Exception:
        # Falls der Hash ungültig ist oder das PW nicht stimmt
        return False