"""Unit tests for the cryptanalysis lab."""
from ciphers.classical import caesar, vigenere
from ciphers.cryptanalysis import (
    caesar_brute_force, crack_vigenere, guess_key_length, index_of_coincidence,
    letter_frequencies, only_letters,
)

# A plain English sample text written for these tests.
SAMPLE = (
    "Encryption is used every day when people send messages, pay with mobile money "
    "or log in to online banking. Most people do not see it working, but it protects "
    "their data from anyone who tries to read it on the way. In the past, simple "
    "ciphers such as the Caesar cipher and the Vigenere cipher were used by armies and "
    "governments to keep their plans secret. These ciphers can now be broken in seconds "
    "by a computer, because the patterns of the language still show through the "
    "ciphertext. Letters like E, T and A appear far more often than letters like Q and Z, "
    "and this simple fact is enough to recover the key. Modern ciphers such as AES were "
    "designed so that the ciphertext looks completely random, which is why they are "
    "still safe to use today when the key is long and kept secret."
)


def test_caesar_brute_force_finds_shift():
    secret, _ = caesar(SAMPLE, 11)
    best = caesar_brute_force(secret)[0]
    assert best["Shift"] == 11
    assert best["Decrypted text"].startswith("Encryption")


def test_caesar_brute_force_short_text():
    secret, _ = caesar("Meet me at the old bridge tonight", 5)
    assert caesar_brute_force(secret)[0]["Shift"] == 5


def test_frequency_table_has_26_rows_and_sums_to_100():
    rows = letter_frequencies(SAMPLE)
    assert len(rows) == 26
    assert abs(sum(r["Text %"] for r in rows) - 100) < 0.5


def test_ioc_of_english_is_higher_than_random():
    english_ioc = index_of_coincidence(only_letters(SAMPLE))
    assert english_ioc > 0.06


def test_vigenere_key_length_found():
    secret, _ = vigenere(SAMPLE, "LEMON")
    assert guess_key_length(secret) == 5


def test_vigenere_cracked():
    secret, _ = vigenere(SAMPLE, "LEMON")
    key, plain = crack_vigenere(secret)
    assert key == "LEMON"
    assert plain == SAMPLE


def test_vigenere_cracked_longer_key():
    secret, _ = vigenere(SAMPLE, "MALAWI")
    key, _ = crack_vigenere(secret)
    assert key == "MALAWI"
