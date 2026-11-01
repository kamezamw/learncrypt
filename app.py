"""
LearnCrypt - main Streamlit app.
Start it with:   streamlit run app.py
"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from ciphers import modern
from ciphers.classical import caesar, playfair, playfair_square, vigenere
from ciphers.cryptanalysis import (
    caesar_brute_force, crack_vigenere, guess_key_length, key_length_scores,
    letter_frequencies,
)

st.set_page_config(page_title="LearnCrypt", page_icon="🔐", layout="wide")

PAGES = ["Home", "Classical ciphers", "Modern cryptography", "Cryptanalysis lab", "Performance benchmark"]
page = st.sidebar.radio("Menu", PAGES)
st.sidebar.info("Do not enter real passwords or private messages. Nothing you type is stored.")


def show_steps(steps, title="Show step by step"):
    """Show the step-by-step table under a result."""
    if steps:
        with st.expander(title, expanded=True):
            st.dataframe(pd.DataFrame(steps), use_container_width=True, hide_index=True)


# ===========================================================================
# Home
# ===========================================================================
if page == "Home":
    st.title("LearnCrypt")
    st.write("An interactive tool for learning how encryption works, and how weak ciphers are broken. "
             "Choose a module from the menu on the left.")
    st.markdown(
        "- **Classical ciphers**: Caesar, Vigenère and Playfair, step by step\n"
        "- **Modern cryptography**: AES-256-GCM, RSA and SHA-256, the methods that protect "
        "messaging apps, mobile money and online banking\n"
        "- **Cryptanalysis lab**: break the classical ciphers yourself\n"
        "- **Performance benchmark**: compare how fast each algorithm is"
    )

# ===========================================================================
# Classical ciphers
# ===========================================================================
elif page == "Classical ciphers":
    st.title("Classical ciphers")
    mode = st.radio("What do you want to do?", ["Encrypt", "Decrypt"], horizontal=True)
    decrypt = mode == "Decrypt"
    tab_caesar, tab_vig, tab_play = st.tabs(["Caesar", "Vigenère", "Playfair"])

    with tab_caesar:
        st.caption("Each letter is moved a fixed number of places along the alphabet.")
        text = st.text_area("Text", "Hello World", key="caesar_text")
        shift = st.slider("Shift", 1, 25, 3)
        result, steps = caesar(text, shift, decrypt)
        st.success(f"Result: {result}")
        show_steps(steps)

    with tab_vig:
        st.caption("Each letter is shifted by the matching letter of the key (A=0, B=1, ...).")
        text = st.text_area("Text", "Attack at dawn", key="vig_text")
        key = st.text_input("Key (letters only)", "LEMON", key="vig_key")
        try:
            result, steps = vigenere(text, key, decrypt)
            st.success(f"Result: {result}")
            show_steps(steps)
        except ValueError as err:
            st.error(str(err))

    with tab_play:
        st.caption("Letters are encrypted in pairs using a 5x5 square built from the key. "
                   "J is treated as I, and an X is added between double letters.")
        text = st.text_area("Text", "Hide the gold in the tree stump", key="pf_text")
        key = st.text_input("Key", "playfair example", key="pf_key")
        col_square, col_result = st.columns([1, 2])
        with col_square:
            st.write("Key square")
            st.dataframe(pd.DataFrame(playfair_square(key)), hide_index=True)
        with col_result:
            try:
                result, steps = playfair(text, key, decrypt)
                st.success(f"Result: {result}")
                show_steps(steps)
            except ValueError as err:
                st.error(str(err))

# ===========================================================================
# Modern cryptography
# ===========================================================================
elif page == "Modern cryptography":
    st.title("Modern cryptography")
    tab_aes, tab_rsa, tab_sha, tab_file = st.tabs(
        ["AES-256-GCM", "RSA", "SHA-256 hashing", "File encryption"])

    # ---- AES ----
    with tab_aes:
        st.caption("AES is a symmetric cipher: the same secret key locks and unlocks the data. "
                   "Here the key is made from a password, and GCM mode also detects tampering.")
        mode = st.radio("Mode", ["Encrypt", "Decrypt"], horizontal=True, key="aes_mode")
        password = st.text_input("Password", "practice-password", type="password", key="aes_pw")
        if mode == "Encrypt":
            text = st.text_area("Message", "Meet me at the market at 10", key="aes_text")
            if st.button("Encrypt", key="aes_go"):
                token, steps = modern.aes_encrypt_text(text, password)
                st.success("Encrypted. Copy this ciphertext:")
                st.code(token, wrap_lines=True)
                show_steps(steps, "What happened, step by step")
                st.info("Encrypt the same message again: the ciphertext changes, because the salt "
                        "and nonce are new random values each time.")
        else:
            token = st.text_area("Ciphertext (Base64)", key="aes_token")
            if st.button("Decrypt", key="aes_dec"):
                try:
                    st.success(f"Message: {modern.aes_decrypt_text(token, password)}")
                except ValueError as err:
                    st.error(str(err))
                    st.caption("Try changing one character of the ciphertext or the password: "
                               "GCM refuses to decrypt anything that was changed.")

    # ---- RSA ----
    with tab_rsa:
        st.caption("RSA is asymmetric: the public key locks, only the private key unlocks. "
                   "The private key also makes digital signatures that anyone can check with the public key.")
        if st.button("Generate a new 2048-bit key pair"):
            st.session_state["rsa_keys"] = modern.rsa_generate()
        if "rsa_keys" not in st.session_state:
            st.session_state["rsa_keys"] = modern.rsa_generate()
        private_pem, public_pem = st.session_state["rsa_keys"]
        c1, c2 = st.columns(2)
        with c1:
            st.text_area("Public key (share this)", public_pem, height=200)
        with c2:
            with st.expander("Private key (keep secret)"):
                st.code(private_pem)

        st.subheader("Encrypt and decrypt")
        msg = st.text_input(f"Short message (max {modern.RSA_MAX_MESSAGE} bytes)", "Hello from LearnCrypt")
        try:
            token = modern.rsa_encrypt(msg, public_pem)
            st.write("Encrypted with the public key:")
            st.code(token, wrap_lines=True)
            st.write("Decrypted with the private key:", modern.rsa_decrypt(token, private_pem))
        except ValueError as err:
            st.error(str(err))

        st.subheader("Digital signature")
        doc = st.text_input("Message to sign", "I owe you 100 kwacha")
        signature = modern.rsa_sign(doc, private_pem)
        st.code(signature, wrap_lines=True)
        checked = st.text_input("Message as received (try changing it)", doc)
        if modern.rsa_verify(checked, signature, public_pem):
            st.success("Signature valid: the message is unchanged and came from the key owner.")
        else:
            st.error("Signature NOT valid: the message was changed.")

    # ---- SHA-256 ----
    with tab_sha:
        st.caption("A hash is a fixed-length fingerprint of data. It cannot be reversed, and a tiny change "
                   "in the input changes about half of the output bits (the avalanche effect).")
        t1 = st.text_input("Text 1", "hello")
        t2 = st.text_input("Text 2 (change one letter)", "hellp")
        res = modern.avalanche(t1, t2)
        st.code(f"SHA-256(Text 1) = {res['hash1']}\nSHA-256(Text 2) = {res['hash2']}")
        st.metric("Bits changed out of 256", f"{res['bits_changed']} ({res['percent']:.1f}%)")

    # ---- File ----
    with tab_file:
        st.caption("Encrypt any small file with AES-256-GCM and a password. Files are processed in memory "
                   "and never saved on the server.")
        fmode = st.radio("Mode", ["Encrypt a file", "Decrypt a .lcrypt file"], horizontal=True)
        upload = st.file_uploader("Choose a file (max 5 MB)")
        fpass = st.text_input("Password", type="password", key="file_pw")
        if upload and fpass:
            data = upload.getvalue()
            if len(data) > 5 * 1024 * 1024:
                st.error("Please use a file smaller than 5 MB.")
            elif fmode == "Encrypt a file":
                package, _ = modern.aes_encrypt_bytes(data, fpass)
                st.download_button("Download encrypted file", package, file_name=upload.name + ".lcrypt")
            else:
                try:
                    plain = modern.aes_decrypt_bytes(data, fpass)
                    name = upload.name[:-7] if upload.name.endswith(".lcrypt") else "decrypted_" + upload.name
                    st.download_button("Download decrypted file", plain, file_name=name)
                except ValueError as err:
                    st.error(str(err))

# ===========================================================================
# Cryptanalysis lab
# ===========================================================================
elif page == "Cryptanalysis lab":
    st.title("Cryptanalysis lab")
    st.write("Classical ciphers keep the patterns of the language, so a computer can break them in seconds.")
    tab_bf, tab_freq, tab_vig = st.tabs(["Caesar brute force", "Frequency analysis", "Vigenère cracker"])

    with tab_bf:
        st.caption("There are only 25 possible shifts, so we try them all and score each result "
                   "against normal English letter frequencies (lower score = more like English).")
        default = caesar("Meet me at the old bridge tonight", 7)[0]
        secret = st.text_area("Caesar ciphertext", default, key="bf_text")
        rows = caesar_brute_force(secret)
        st.success(f"Best guess: shift {rows[0]['Shift']} → {rows[0]['Decrypted text']}")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab_freq:
        st.caption("Compare how often each letter appears in your text with normal English.")
        text = st.text_area("Text to analyse", caesar(
            "Letters like E, T and A appear far more often than letters like Q and Z, "
            "and this simple fact is enough to break a substitution cipher.", 4)[0], key="freq_text")
        freq = pd.DataFrame(letter_frequencies(text)).set_index("Letter")
        st.bar_chart(freq[["Text %", "English %"]], stack=False)
        st.caption("In a Caesar cipher the bars have the same shape as English, just moved along.")

    with tab_vig:
        st.caption("Step 1: find the key length with the index of coincidence (IoC). "
                   "Step 2: each column of letters is a Caesar cipher, so frequency analysis finds each key letter. "
                   "Longer ciphertexts (300+ letters) work best.")
        sample = ("Encryption is used every day when people send messages, pay with mobile money or log in to "
                  "online banking. Most people do not see it working, but it protects their data from anyone who "
                  "tries to read it on the way. In the past, simple ciphers such as the Caesar cipher and the "
                  "Vigenere cipher were used by armies and governments to keep their plans secret. These ciphers "
                  "can now be broken in seconds by a computer, because the patterns of the language still show "
                  "through the ciphertext.")
        secret = st.text_area("Vigenère ciphertext", vigenere(sample, "MALAWI")[0], height=150, key="vc_text")
        scores = pd.DataFrame(key_length_scores(secret)).set_index("Key length")
        st.write("Average IoC for each possible key length (English ≈ 0.067, random ≈ 0.038):")
        st.bar_chart(scores)
        guess = guess_key_length(secret)
        length = st.number_input("Key length to use", 1, 12, guess)
        try:
            key, plain = crack_vigenere(secret, int(length))
            st.success(f"Recovered key: {key}")
            st.text_area("Recovered plaintext", plain, height=150)
        except ValueError as err:
            st.error(str(err))

# ===========================================================================
# Performance benchmark
# ===========================================================================
elif page == "Performance benchmark":
    from benchmark import SIZES, machine_info, run_benchmark, run_fixed_tests

    st.title("Performance benchmark")
    st.write("Times each algorithm on inputs of different sizes. Each test is repeated and the median "
             "time is kept. The classical ciphers are written in plain Python for teaching, while AES, "
             "SHA-256 and RSA use the optimised `cryptography` library.")
    sizes = st.multiselect("Input sizes", list(SIZES), default=["1 KB", "10 KB", "100 KB", "1 MB"])
    repeats = st.slider("Repeats per test", 1, 10, 3)
    st.caption("10 MB can take a minute or more on a free server.")
    if st.button("Run benchmark") and sizes:
        sizes = [s for s in SIZES if s in sizes]
        bar = st.progress(0.0, "Starting")
        results = run_benchmark(sizes, repeats, progress=lambda p, msg: bar.progress(p, msg))
        fixed = run_fixed_tests(repeats)
        st.caption(f"Machine: {machine_info()}")

        table = results.pivot(index="Algorithm", columns="Input size", values="Median time (ms)")[sizes]
        st.subheader("Median time (milliseconds)")
        st.dataframe(table, use_container_width=True)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        colours = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
        for name, colour in zip(table.index, colours):
            ax.plot([SIZES[s] for s in sizes], table.loc[name], marker="o", linewidth=2,
                    color=colour, label=name)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Input size (bytes, log scale)")
        ax.set_ylabel("Median time (ms, log scale)")
        ax.grid(True, which="major", alpha=0.3)
        ax.legend(fontsize=8, frameon=False, loc="upper left")
        st.pyplot(fig)

        st.subheader("Fixed-size operations")
        st.dataframe(fixed, use_container_width=True, hide_index=True)
        st.download_button("Download results (CSV)", results.to_csv(index=False), "benchmark_results.csv")
