"""
Encrypts sensitive fields (API keys, passwords) for storage in the
database. Uses Fernet (symmetric, authenticated encryption) with a key
derived from NetBox's own SECRET_KEY - so no additional secret-management
mechanism is needed.

IMPORTANT: This protects against plaintext leaks in DB dumps/backups, but
is NOT a substitute for full secrets management (e.g. Vault). If NetBox's
SECRET_KEY is compromised, these values are compromised too - a deliberate
trade-off for a homelab setup, not an enterprise-grade guarantee.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet() -> Fernet:
    # SECRET_KEY is arbitrary length / not a valid Fernet key -> reduce it to
    # exactly 32 bytes via SHA-256 and base64-url-encode it as Fernet requires.
    digest = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    if not plaintext:
        return ''
    token = _get_fernet().encrypt(plaintext.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ''
    try:
        return _get_fernet().decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        # SECRET_KEY changed, or the data is corrupt/tampered with. Fail loudly
        # on purpose instead of silently returning an empty string - otherwise
        # a sync ends up running with an empty password and no clue why.
        raise ValueError(
            'Konnte gespeicherten Wert nicht entschluesseln. '
            'Hat sich SECRET_KEY geaendert? Zugangsdaten muessen neu eingegeben werden.'
        )
