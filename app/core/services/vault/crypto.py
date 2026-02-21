import os
import json
from argon2 import PasswordHasher, low_level
from Crypto.Cipher import AES

KEY_FILE = "/data/security/vault_keys.enc"

def derive_key(master_key: str, salt: bytes) -> bytes:
    return low_level.hash_secret_raw(
        secret=master_key.encode(),
        salt=salt,
        time_cost=3, memory_cost=65536, parallelism=4, 
        hash_len=32, type=low_level.Type.ID
    )

def encrypt_vault_keys(master_key: str, vault_payload: dict) -> bytes:
    salt = os.urandom(16)
    key = derive_key(master_key, salt)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(vault_payload).encode())
    return salt + cipher.nonce + tag + ciphertext

def decrypt_vault_keys(master_key: str, encrypted_blob: bytes) -> dict:
    salt, nonce, tag, ciphertext = encrypted_blob[:16], encrypted_blob[16:32], encrypted_blob[32:48], encrypted_blob[48:]
    key = derive_key(master_key, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return json.loads(cipher.decrypt_and_verify(ciphertext, tag).decode())