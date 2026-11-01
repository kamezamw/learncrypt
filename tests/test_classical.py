"""
Unit tests for the classical ciphers, using known test vectors.
Run them with:   python -m pytest
"""
from ciphers.classical import caesar, vigenere, playfair, playfair_square


# ---- Caesar ---------------------------------------------------------------
def test_caesar_encrypt_known_vector():
    # Classic example: HELLO with shift 3 gives KHOOR
    assert caesar("HELLO", 3)[0] == "KHOOR"


def test_caesar_keeps_case_and_spaces():
    assert caesar("Hello, World!", 3)[0] == "Khoor, Zruog!"


def test_caesar_wraps_around():
    assert caesar("XYZ", 3)[0] == "ABC"


def test_caesar_decrypt_reverses_encrypt():
    secret, _ = caesar("Attack at dawn", 7)
    assert caesar(secret, 7, decrypt=True)[0] == "Attack at dawn"


# ---- Vigenere -------------------------------------------------------------
def test_vigenere_known_vector():
    # Textbook example: ATTACKATDAWN with key LEMON gives LXFOPVEFRNHR
    assert vigenere("ATTACKATDAWN", "LEMON")[0] == "LXFOPVEFRNHR"


def test_vigenere_decrypt_reverses_encrypt():
    secret, _ = vigenere("Meet me at noon", "KEY")
    assert vigenere(secret, "KEY", decrypt=True)[0] == "Meet me at noon"


def test_vigenere_empty_key_rejected():
    try:
        vigenere("HELLO", "123")
        assert False, "Expected an error for a key with no letters"
    except ValueError:
        pass


# ---- Playfair -------------------------------------------------------------
def test_playfair_square_first_row():
    square = playfair_square("playfair example")
    assert square[0] == ["P", "L", "A", "Y", "F"]


def test_playfair_known_vector():
    # Well-known example with key "playfair example"
    result, _ = playfair("Hide the gold in the tree stump", "playfair example")
    assert result == "BMODZBXDNABEKUDMUIXMMOUVIF"


def test_playfair_decrypt_gives_padded_plaintext():
    result, _ = playfair("BMODZBXDNABEKUDMUIXMMOUVIF", "playfair example", decrypt=True)
    assert result == "HIDETHEGOLDINTHETREXESTUMP"
