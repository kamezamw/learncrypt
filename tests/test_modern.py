"""Unit tests for the modern cryptography module."""
import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ciphers.modern import (
    aes_decrypt_bytes, aes_decrypt_text, aes_encrypt_bytes, aes_encrypt_text,
    avalanche, rsa_decrypt, rsa_encrypt, rsa_generate, rsa_sign, rsa_verify,
    sha256_hex,
)

FAST = 1_000  # fewer PBKDF2 rounds so the tests run quickly


# ---- Known test vectors ---------------------------------------------------
def test_sha256_known_vector():
    # FIPS 180 example: SHA-256("abc")
    assert sha256_hex("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_sha256_empty_string():
    assert sha256_hex("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_aes256_fips197_known_vector():
    # FIPS 197 Appendix C.3: AES-256 single block with the example key
    key = bytes(range(32))
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    assert enc.update(plaintext).hex() == "8ea2b7ca516745bfeafc49904b496089"


# ---- AES-256-GCM ----------------------------------------------------------
def test_aes_roundtrip_bytes():
    package, steps = aes_encrypt_bytes(b"secret data", "pass123", FAST)
    assert aes_decrypt_bytes(package, "pass123", FAST) == b"secret data"
    assert len(steps) == 5


def test_aes_wrong_password_fails():
    package, _ = aes_encrypt_bytes(b"secret data", "right", FAST)
    with pytest.raises(ValueError):
        aes_decrypt_bytes(package, "wrong", FAST)


def test_aes_tampered_data_fails():
    package, _ = aes_encrypt_bytes(b"secret data", "pw", FAST)
    changed = package[:-1] + bytes([package[-1] ^ 1])
    with pytest.raises(ValueError):
        aes_decrypt_bytes(changed, "pw", FAST)


def test_aes_same_text_gives_different_ciphertext():
    a, _ = aes_encrypt_bytes(b"hello", "pw", FAST)
    b, _ = aes_encrypt_bytes(b"hello", "pw", FAST)
    assert a != b  # random salt and nonce


def test_aes_text_roundtrip_default_settings():
    token, _ = aes_encrypt_text("Mwaswera bwanji?", "pw")
    assert aes_decrypt_text(token, "pw") == "Mwaswera bwanji?"


# ---- RSA ------------------------------------------------------------------
@pytest.fixture(scope="module")
def keys():
    return rsa_generate()


def test_rsa_encrypt_decrypt(keys):
    private_pem, public_pem = keys
    assert rsa_decrypt(rsa_encrypt("hello RSA", public_pem), private_pem) == "hello RSA"


def test_rsa_message_too_long(keys):
    with pytest.raises(ValueError):
        rsa_encrypt("x" * 191, keys[1])


def test_rsa_signature_valid(keys):
    private_pem, public_pem = keys
    sig = rsa_sign("I owe you 100 kwacha", private_pem)
    assert rsa_verify("I owe you 100 kwacha", sig, public_pem)


def test_rsa_signature_detects_change(keys):
    private_pem, public_pem = keys
    sig = rsa_sign("I owe you 100 kwacha", private_pem)
    assert not rsa_verify("I owe you 900 kwacha", sig, public_pem)


def test_rsa_wrong_key_cannot_decrypt(keys):
    other_private, _ = rsa_generate()
    token = rsa_encrypt("hello", keys[1])
    with pytest.raises(ValueError):
        rsa_decrypt(token, other_private)


# ---- Avalanche ------------------------------------------------------------
def test_avalanche_one_letter_changes_many_bits():
    result = avalanche("hello", "hellp")
    assert 80 < result["bits_changed"] < 176  # about half of 256 bits
