from argon2 import PasswordHasher, low_level

# Wir instanziieren den Hasher mit sicheren Standardwerten (Argon2id)
ph = PasswordHasher(
    time_cost=3,          # Anzahl der Iterationen
    memory_cost=65536,    # Speicherverbrauch (64MB)
    parallelism=4,        # Anzahl der parallelen Threads
    hash_len=32,          # Länge des resultierenden Hashs
    type=low_level.Type.ID # Nutzt Argon2id (Schutz gegen Side-Channel & GPU-Attacks)
)

def hash_password(password: str) -> str:
    """
    Erzeugt einen sicheren Argon2-Hash für die Datenbank.
    Argon2 fügt automatisch ein zufälliges Salt hinzu.
    """
    return ph.hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    """
    Vergleicht einen gespeicherten Hash aus der DB mit einer Passworteingabe.
    Gibt True zurück, wenn sie übereinstimmen, sonst False.
    """
    try:
        return ph.verify(hashed_password, password)
    except Exception:
        # Falls der Hash ungültig ist oder das Passwort nicht stimmt
        return False