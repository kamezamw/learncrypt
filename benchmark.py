"""
Performance benchmark for LearnCrypt.

Measures how long each algorithm takes for inputs of different sizes.
Each test is repeated several times and the median (middle) time is kept,
because the median is not pulled up by one slow run.

Run it on its own from the terminal to save results to a CSV file:
    python benchmark.py                 # 1 KB to 1 MB, quick
    python benchmark.py --full          # 1 KB to 10 MB, takes a few minutes
"""
import argparse
import os
import platform
import statistics
import time

import pandas as pd

from ciphers.classical import caesar, playfair, vigenere
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa

from ciphers.modern import (
    AESGCM, OAEP, PBKDF2_ITERATIONS, PSS, derive_key, rsa_generate, sha256_hex,
)

KB = 1024
MB = 1024 * KB
SIZES = {"1 KB": KB, "10 KB": 10 * KB, "100 KB": 100 * KB, "1 MB": MB, "10 MB": 10 * MB}

SAMPLE_SENTENCE = "The quick brown fox jumps over the lazy dog while the zebra eats grass. "


def make_text(size):
    """English-like text of exactly `size` characters (1 character = 1 byte)."""
    repeats = size // len(SAMPLE_SENTENCE) + 1
    return (SAMPLE_SENTENCE * repeats)[:size]


def time_it(func, repeats):
    """Run func() `repeats` times and return the median time in milliseconds."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        func()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times)


def size_tests(text, data, key, nonce, private_key, signature):
    """The algorithms that are timed at every input size.
    RSA keys are loaded once before timing, so only the signing is measured."""
    aes = AESGCM(key)
    public_key = private_key.public_key()
    ciphertext = aes.encrypt(nonce, data, None)
    return {
        "Caesar (pure Python)": lambda: caesar(text, 3, record_steps=False),
        "Vigenere (pure Python)": lambda: vigenere(text, "LEMON", record_steps=False),
        "Playfair (pure Python)": lambda: playfair(text, "playfair example", record_steps=False),
        "AES-256-GCM encrypt": lambda: aes.encrypt(nonce, data, None),
        "AES-256-GCM decrypt": lambda: aes.decrypt(nonce, ciphertext, None),
        "SHA-256 hash": lambda: sha256_hex(data),
        "RSA-2048 sign": lambda: private_key.sign(data, PSS, hashes.SHA256()),
        "RSA-2048 verify": lambda: public_key.verify(signature, data, PSS, hashes.SHA256()),
    }


def run_benchmark(size_labels=("1 KB", "10 KB", "100 KB", "1 MB"), repeats=5, progress=None):
    """Return a table (pandas DataFrame) of median times for each algorithm and size."""
    key = os.urandom(32)
    nonce = os.urandom(12)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rows = []
    total = len(size_labels)
    for i, label in enumerate(size_labels):
        size = SIZES[label]
        text = make_text(size)
        data = text.encode("ascii")
        signature = private_key.sign(data, PSS, hashes.SHA256())
        # Fewer repeats for big inputs on the slow pure-Python ciphers
        for name, func in size_tests(text, data, key, nonce, private_key, signature).items():
            reps = repeats if (size < MB or "pure Python" not in name) else max(1, repeats // 2)
            ms = time_it(func, reps)
            rows.append({"Algorithm": name, "Input size": label, "Bytes": size,
                         "Median time (ms)": round(ms, 4),
                         "Throughput (MB/s)": round((size / MB) / (ms / 1000), 2) if ms > 0 else None})
        if progress:
            progress((i + 1) / total, f"Finished {label}")
    return pd.DataFrame(rows)


def run_fixed_tests(repeats=5):
    """Operations that do not depend on input size."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    message = b"x" * 190
    token = public_key.encrypt(message, OAEP)
    salt = os.urandom(16)
    rows = [
        {"Operation": "RSA-2048 key generation", "Median time (ms)": time_it(rsa_generate, repeats)},
        {"Operation": "RSA-2048 encrypt 190 bytes (OAEP)",
         "Median time (ms)": time_it(lambda: public_key.encrypt(message, OAEP), repeats)},
        {"Operation": "RSA-2048 decrypt 190 bytes (OAEP)",
         "Median time (ms)": time_it(lambda: private_key.decrypt(token, OAEP), repeats)},
        {"Operation": f"PBKDF2 key from password ({PBKDF2_ITERATIONS:,} rounds)",
         "Median time (ms)": time_it(lambda: derive_key("password", salt), repeats)},
    ]
    df = pd.DataFrame(rows)
    df["Median time (ms)"] = df["Median time (ms)"].round(3)
    return df


def machine_info():
    return f"{platform.system()} {platform.release()}, Python {platform.python_version()}, {platform.processor() or platform.machine()}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="include 10 MB")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    labels = list(SIZES) if args.full else list(SIZES)[:4]
    print("Machine:", machine_info())
    results = run_benchmark(labels, args.repeats, progress=lambda p, msg: print(msg))
    fixed = run_fixed_tests(args.repeats)
    os.makedirs("results", exist_ok=True)
    results.to_csv("results/benchmark_sizes.csv", index=False)
    fixed.to_csv("results/benchmark_fixed.csv", index=False)
    print(results.pivot(index="Algorithm", columns="Input size", values="Median time (ms)")[labels])
    print(fixed)
    print("Saved to results/")
