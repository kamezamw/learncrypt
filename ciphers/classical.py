"""
Classical ciphers for LearnCrypt: Caesar, Vigenere and Playfair.

Every function returns two things:
    1. the result text
    2. a list of "steps" (one dictionary per letter or letter pair)
       that the app shows as a table, so the user can follow the cipher.

Letters keep their case. Spaces, numbers and punctuation are kept as they are
(Caesar and Vigenere) or removed (Playfair, which only works on letters).

record_steps=False skips the step table. The benchmark uses this, because
building a table for 10 MB of text would use a lot of memory.
"""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def shift_letter(letter, shift):
    """Move one letter forward in the alphabet by `shift` places (wraps Z->A)."""
    if not letter.isalpha() or not letter.isascii():
        return letter
    base = ord("A") if letter.isupper() else ord("a")
    return chr((ord(letter) - base + shift) % 26 + base)


def _is_letter(ch):
    return ch.isascii() and ch.isalpha()


# ---------------------------------------------------------------------------
# Caesar cipher
# ---------------------------------------------------------------------------
def caesar(text, shift, decrypt=False, record_steps=True):
    """Encrypt (or decrypt) text with the Caesar cipher."""
    if decrypt:
        shift = -shift
    out = []
    steps = []
    for ch in text:
        new_ch = shift_letter(ch, shift)
        out.append(new_ch)
        if record_steps and _is_letter(ch):
            steps.append({
                "Input letter": ch,
                "Position (A=0)": ALPHABET.index(ch.upper()),
                "Shift": shift,
                "New position": ALPHABET.index(new_ch.upper()),
                "Output letter": new_ch,
            })
    return "".join(out), steps


# ---------------------------------------------------------------------------
# Vigenere cipher
# ---------------------------------------------------------------------------
def vigenere(text, key, decrypt=False, record_steps=True):
    """Encrypt (or decrypt) text with the Vigenere cipher.

    The key letters are used one by one (A=0, B=1, ...). The key only moves
    forward on letters, so spaces and punctuation do not use up key letters.
    """
    key = "".join(k for k in key.upper() if _is_letter(k))
    if not key:
        raise ValueError("The key must contain at least one letter.")

    shifts = [ALPHABET.index(k) for k in key]
    if decrypt:
        shifts = [-s for s in shifts]

    out = []
    steps = []
    k = 0  # position in the key
    for ch in text:
        if _is_letter(ch):
            shift = shifts[k % len(key)]
            new_ch = shift_letter(ch, shift)
            if record_steps:
                steps.append({
                    "Input letter": ch,
                    "Key letter": key[k % len(key)],
                    "Shift": shift,
                    "Output letter": new_ch,
                })
            k += 1
        else:
            new_ch = ch
        out.append(new_ch)
    return "".join(out), steps


# ---------------------------------------------------------------------------
# Playfair cipher
# ---------------------------------------------------------------------------
def playfair_square(key):
    """Build the 5x5 Playfair square from the key (I and J share one cell)."""
    seen = ""
    for ch in key.upper() + ALPHABET:
        if not _is_letter(ch):
            continue
        if ch == "J":
            ch = "I"
        if ch not in seen:
            seen += ch
    return [list(seen[i:i + 5]) for i in range(0, 25, 5)]


def _positions(square):
    """Return a dictionary: letter -> (row, column). Faster than searching."""
    return {square[r][c]: (r, c) for r in range(5) for c in range(5)}


def _clean_letters(text):
    """Upper-case letters only, with J changed to I."""
    return [("I" if c == "J" else c) for c in text.upper() if _is_letter(c)]


def playfair_pairs(text):
    """Split text into letter pairs the way Playfair needs.

    - Only letters are kept, in upper case, and J becomes I.
    - If both letters of a pair are the same, an X is put between them.
    - If one letter is left at the end, an X is added.
    """
    letters = _clean_letters(text)
    pairs = []
    i = 0
    while i < len(letters):
        a = letters[i]
        b = letters[i + 1] if i + 1 < len(letters) else "X"
        if a == b:
            pairs.append(a + "X")
            i += 1
        else:
            pairs.append(a + b)
            i += 2
    return pairs


def playfair(text, key, decrypt=False, record_steps=True):
    """Encrypt (or decrypt) text with the Playfair cipher."""
    square = playfair_square(key)
    pos = _positions(square)
    move = -1 if decrypt else 1
    out = []
    steps = []

    # When decrypting, the text is already in pairs, so just split it.
    if decrypt:
        letters = _clean_letters(text)
        if len(letters) % 2 != 0:
            raise ValueError("Playfair ciphertext must have an even number of letters.")
        pairs = ["".join(letters[i:i + 2]) for i in range(0, len(letters), 2)]
    else:
        pairs = playfair_pairs(text)

    for pair in pairs:
        r1, c1 = pos[pair[0]]
        r2, c2 = pos[pair[1]]
        if r1 == r2:
            rule = "Same row: move along the row"
            res = square[r1][(c1 + move) % 5] + square[r2][(c2 + move) % 5]
        elif c1 == c2:
            rule = "Same column: move along the column"
            res = square[(r1 + move) % 5][c1] + square[(r2 + move) % 5][c2]
        else:
            rule = "Rectangle: swap the columns"
            res = square[r1][c2] + square[r2][c1]
        out.append(res)
        if record_steps:
            steps.append({"Input pair": pair, "Rule used": rule, "Output pair": res})

    return "".join(out), steps
