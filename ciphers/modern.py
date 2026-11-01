"""
Modern cryptography for LearnCrypt: AES-256-GCM, RSA and SHA-256.

All the real cryptography is done by the well-tested Python `cryptography`
library. This file only joins the library calls together and records the
steps so the app can explain them. We never write our own AES or RSA code,
because home-made versions of these algorithms are easy to get wrong.
"""
import base64
import hashlib
import os

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Settings ------------------------------------------------------------------
PBKDF2_ITERATIONS = 600_000   # OWASP (2023) suggestion for PBKDF2-HMAC-SHA256
SALT_SIZE = 16                # bytes
NONCE_SIZE = 12               # bytes, the standard size for AES-GCM
KEY_SIZE = 32                 # bytes = 256 bits


def b64(data):
    """Bytes -> readable Base64 text."""
    return base64.b64encode(data).decode("ascii")


def unb64(text):
    """Base64 text -> bytes."""
    return base64.b64decode(text.strip().encode("ascii"))


# ---------------------------------------------------------------------------
# AES-256-GCM with a password
# ---------------------------------------------------------------------------
def derive_key(password, salt, iterations=PBKDF2_ITERATIONS):
    """Turn a password into a 256-bit AES key using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=KEY_SIZE,
                     salt=salt, iterations=iterations)
    return kdf.derive(password.encode("utf-8"))


def aes_encrypt_bytes(data, password, iterations=PBKDF2_ITERATIONS):
    """Encrypt bytes. Returns one package: salt + nonce + ciphertext(+tag)."""
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt, iterations)
    ciphertext = AESGCM(key).encrypt(nonce, data, None)  # tag is added at the end
    package = salt + nonce + ciphertext
    steps = [
        {"Step": "1. Make a random salt", "Value (Base64)": b64(salt),
         "Why": "So the same password gives a different key each time"},
        {"Step": f"2. Derive the key (PBKDF2, {iterations:,} rounds)", "Value (Base64)": b64(key),
         "Why": "Turns the password into a 256-bit key and slows down guessing"},
        {"Step": "3. Make a random nonce", "Value (Base64)": b64(nonce),
         "Why": "Must never repeat with the same key"},
        {"Step": "4. Encrypt with AES-256-GCM", "Value (Base64)": b64(ciphertext[:-16]),
         "Why": "The scrambled data"},
        {"Step": "5. Authentication tag", "Value (Base64)": b64(ciphertext[-16:]),
         "Why": "Detects any change to the ciphertext"},
    ]
    return package, steps


def aes_decrypt_bytes(package, password, iterations=PBKDF2_ITERATIONS):
    """Decrypt a package made by aes_encrypt_bytes.

    Raises ValueError if the password is wrong or the data was changed.
    """
    if len(package) < SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("The encrypted data is too short to be valid.")
    salt = package[:SALT_SIZE]
    nonce = package[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = package[SALT_SIZE + NONCE_SIZE:]
    key = derive_key(password, salt, iterations)
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise ValueError("Decryption failed: wrong password, or the data was changed.")


def aes_encrypt_text(text, password):
    """Encrypt text and return Base64 text that can be copied."""
    package, steps = aes_encrypt_bytes(text.encode("utf-8"), password)
    return b64(package), steps


def aes_decrypt_text(token, password):
    """Decrypt Base64 text made by aes_encrypt_text."""
    try:
        package = unb64(token)
    except Exception:
        raise ValueError("This is not valid Base64 ciphertext.")
    return aes_decrypt_bytes(package, password).decode("utf-8")


# ---------------------------------------------------------------------------
# RSA (2048-bit): encryption with OAEP, signatures with PSS
# ---------------------------------------------------------------------------
OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)
RSA_MAX_MESSAGE = 190  # bytes: the most RSA-2048 with OAEP-SHA256 can encrypt


def rsa_generate(key_size=2048):
    """Make a new RSA key pair. Returns (private_pem, public_pem) as text."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return private_pem, public_pem


def _load_private(pem):
    return serialization.load_pem_private_key(pem.encode("ascii"), password=None)


def _load_public(pem):
    return serialization.load_pem_public_key(pem.encode("ascii"))


def rsa_encrypt(message, public_pem):
    """Encrypt a short message with the PUBLIC key."""
    data = message.encode("utf-8")
    if len(data) > RSA_MAX_MESSAGE:
        raise ValueError(f"RSA-2048 can only encrypt up to {RSA_MAX_MESSAGE} bytes. "
                         "Real systems use RSA to protect an AES key, and AES for the message.")
    return b64(_load_public(public_pem).encrypt(data, OAEP))


def rsa_decrypt(token, private_pem):
    """Decrypt with the PRIVATE key."""
    try:
        return _load_private(private_pem).decrypt(unb64(token), OAEP).decode("utf-8")
    except Exception:
        raise ValueError("Decryption failed: wrong private key or damaged ciphertext.")


def rsa_sign_bytes(data, private_pem):
    """Sign data with the PRIVATE key. Returns the signature in Base64."""
    return b64(_load_private(private_pem).sign(data, PSS, hashes.SHA256()))


def rsa_verify_bytes(data, signature_b64, public_pem):
    """Check a signature with the PUBLIC key. Returns True or False."""
    try:
        _load_public(public_pem).verify(unb64(signature_b64), data, PSS, hashes.SHA256())
        return True
    except (InvalidSignature, ValueError):
        return False


def rsa_sign(message, private_pem):
    return rsa_sign_bytes(message.encode("utf-8"), private_pem)


def rsa_verify(message, signature_b64, public_pem):
    return rsa_verify_bytes(message.encode("utf-8"), signature_b64, public_pem)


# ---------------------------------------------------------------------------
# SHA-256 and the avalanche effect
# ---------------------------------------------------------------------------
def sha256_hex(data):
    """SHA-256 hash of text or bytes, as 64 hex characters."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def bits_different(hex1, hex2):
    """Count how many of the 256 bits differ between two hashes."""
    return bin(int(hex1, 16) ^ int(hex2, 16)).count("1")


def avalanche(text1, text2):
    """Compare the hashes of two texts. Returns a summary dictionary."""
    h1, h2 = sha256_hex(text1), sha256_hex(text2)
    diff = bits_different(h1, h2)
    return {"hash1": h1, "hash2": h2, "bits_changed": diff, "percent": diff / 256 * 100}
