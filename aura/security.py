"""API key encryption — protect keys at rest using Windows DPAPI.

Windows DPAPI encrypts data using the current user's login credentials.
No separate password is needed — only the logged-in user can decrypt.

Usage:
    python -m aura.security encrypt   # Encrypt the keys file
    python -m aura.security decrypt   # Decrypt and print (for debugging)
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

KEYS_FILE = Path(r"D:\automation\AI keys and tetails.txt")
ENCRYPTED_FILE = Path(r"D:\automation\aura\.cache\keys.enc")


def _dpapi_available() -> bool:
    """Check if Windows DPAPI is available."""
    try:
        import win32crypt  # noqa: F401
        return True
    except ImportError:
        return False


def encrypt_keys() -> str:
    """Encrypt the keys file content using Windows DPAPI.

    Returns path to the encrypted file.
    """
    if not _dpapi_available():
        return "DPAPI not available (install pywin32: pip install pywin32)"

    import win32crypt

    if not KEYS_FILE.exists():
        return f"Keys file not found: {KEYS_FILE}"

    plaintext = KEYS_FILE.read_bytes()

    # Encrypt using DPAPI (user-scoped)
    encrypted = win32crypt.CryptProtectData(
        plaintext,
        "AuraKeys",  # description
        None,  # optional entropy
        None,  # reserved
        None,  # prompt struct
        0,     # flags
    )

    ENCRYPTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENCRYPTED_FILE.write_bytes(encrypted)

    return f"Encrypted keys saved to: {ENCRYPTED_FILE}"


def decrypt_keys() -> str:
    """Decrypt the encrypted keys file using Windows DPAPI.

    Returns the decrypted content.
    """
    if not _dpapi_available():
        return "DPAPI not available (install pywin32: pip install pywin32)"

    import win32crypt

    if not ENCRYPTED_FILE.exists():
        return f"Encrypted file not found: {ENCRYPTED_FILE}"

    encrypted = ENCRYPTED_FILE.read_bytes()

    # Decrypt using DPAPI
    _, plaintext = win32crypt.CryptUnprotectData(
        encrypted,
        None,  # optional entropy
        None,  # reserved
        None,  # prompt struct
        0,     # flags
    )

    return plaintext.decode("utf-8")


def load_keys_secure() -> str:
    """Load keys, preferring encrypted file if available.

    Falls back to plaintext file if encrypted version doesn't exist.
    """
    if ENCRYPTED_FILE.exists() and _dpapi_available():
        return decrypt_keys()
    if KEYS_FILE.exists():
        return KEYS_FILE.read_text(encoding="utf-8")
    raise FileNotFoundError("No keys file found (neither encrypted nor plaintext)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m aura.security [encrypt|decrypt]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "encrypt":
        print(encrypt_keys())
    elif cmd == "decrypt":
        content = decrypt_keys()
        print(f"Decrypted ({len(content)} chars):")
        # Only show first/last bits for safety
        print(content[:100] + "..." if len(content) > 100 else content)
    else:
        print(f"Unknown command: {cmd}")
