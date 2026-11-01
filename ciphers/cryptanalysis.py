"""
Cryptanalysis lab for LearnCrypt: attacks that break the classical ciphers.

1. Caesar brute force   - try all 25 shifts and score each one
2. Frequency analysis   - count letters and compare with normal English
3. Vigenere cracker     - find the key length with the index of coincidence,
                          then find each key letter with frequency analysis

The scoring uses the chi-squared statistic: the lower the score, the more
the letters look like normal English.
"""
from ciphers.classical import ALPHABET, caesar, vigenere

# Typical letter frequencies in English text, in percent.
# Source: Lewand, R. E. (2000). Cryptological Mathematics. Mathematical Association of America.
ENGLISH_FREQ = {
    "A": 8.167, "B": 1.492, "C": 2.782, "D": 4.253, "E": 12.702, "F": 2.228,
    "G": 2.015, "H": 6.094, "I": 6.966, "J": 0.153, "K": 0.772, "L": 4.025,
    "M": 2.406, "N": 6.749, "O": 7.507, "P": 1.929, "Q": 0.095, "R": 5.987,
    "S": 6.327, "T": 9.056, "U": 2.758, "V": 0.978, "W": 2.360, "X": 0.150,
    "Y": 1.974, "Z": 0.074,
}
ENGLISH_IOC = 0.0667   # index of coincidence of normal English
RANDOM_IOC = 1 / 26    # about 0.0385 for random letters


def only_letters(text):
    return [c for c in text.upper() if c.isascii() and c.isalpha()]


# ---------------------------------------------------------------------------
# Frequency analysis
# ---------------------------------------------------------------------------
def letter_counts(text):
    counts = {letter: 0 for letter in ALPHABET}
    for c in only_letters(text):
        counts[c] += 1
    return counts


def letter_frequencies(text):
    """Return a list of rows: letter, count, percent in text, percent in English."""
    counts = letter_counts(text)
    total = sum(counts.values()) or 1
    return [{"Letter": L, "Count": counts[L],
             "Text %": round(counts[L] / total * 100, 2),
             "English %": ENGLISH_FREQ[L]} for L in ALPHABET]


def chi_squared(text):
    """How far the letters are from English (lower = more like English)."""
    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return float("inf")
    score = 0.0
    for L in ALPHABET:
        expected = ENGLISH_FREQ[L] / 100 * total
        score += (counts[L] - expected) ** 2 / expected
    return score


# ---------------------------------------------------------------------------
# Caesar brute force
# ---------------------------------------------------------------------------
def caesar_brute_force(ciphertext):
    """Try every shift 1-25. Returns rows sorted with the best guess first."""
    rows = []
    for shift in range(1, 26):
        plain, _ = caesar(ciphertext, shift, decrypt=True, record_steps=False)
        rows.append({"Shift": shift, "Score (chi-squared)": round(chi_squared(plain), 1),
                     "Decrypted text": plain[:80]})
    return sorted(rows, key=lambda r: r["Score (chi-squared)"])


# ---------------------------------------------------------------------------
# Vigenere cracker
# ---------------------------------------------------------------------------
def index_of_coincidence(letters):
    """Chance that two letters picked at random from the text are the same."""
    n = len(letters)
    if n < 2:
        return 0.0
    counts = {}
    for c in letters:
        counts[c] = counts.get(c, 0) + 1
    return sum(f * (f - 1) for f in counts.values()) / (n * (n - 1))


def key_length_scores(ciphertext, max_length=12):
    """For each possible key length, split the text into columns and average
    the index of coincidence. The right length gives values close to English."""
    letters = only_letters(ciphertext)
    rows = []
    for length in range(1, max_length + 1):
        columns = [letters[i::length] for i in range(length)]
        avg = sum(index_of_coincidence(col) for col in columns) / length
        rows.append({"Key length": length, "Average IoC": round(avg, 4)})
    return rows


def guess_key_length(ciphertext, max_length=12, threshold=0.06):
    """Pick the smallest key length whose average IoC looks like English.
    (Multiples of the real length also score well, so we take the smallest.)"""
    rows = key_length_scores(ciphertext, max_length)
    for row in rows:
        if row["Average IoC"] >= threshold:
            return row["Key length"]
    return max(rows, key=lambda r: r["Average IoC"])["Key length"]


def crack_vigenere(ciphertext, key_length=None, max_length=12):
    """Recover the key and the plaintext. Each column of the ciphertext is a
    Caesar cipher, so the best shift for each column gives one key letter."""
    if key_length is None:
        key_length = guess_key_length(ciphertext, max_length)
    letters = only_letters(ciphertext)
    if len(letters) < key_length * 5:
        raise ValueError("The text is too short to crack. Use a longer ciphertext.")
    key = ""
    for i in range(key_length):
        column = "".join(letters[i::key_length])
        best = min(range(26), key=lambda s: chi_squared(
            caesar(column, s, decrypt=True, record_steps=False)[0]))
        key += ALPHABET[best]
    plaintext, _ = vigenere(ciphertext, key, decrypt=True, record_steps=False)
    return key, plaintext
