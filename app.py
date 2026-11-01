"""
LearnCrypt - main Streamlit app.
Start it with:   streamlit run app.py

Every module follows the same three steps:
    Step 1  Learn  - a short lesson in plain language
    Step 2  Check  - two or three questions; all must be right to continue
    Step 3  Try    - the hands-on activity (only opens after Step 2)
The lesson words and questions live in learn_content.py.
"""
import html
import re

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import learn_content as lc
from ciphers import modern
from ciphers.classical import ALPHABET, caesar, playfair, playfair_square, vigenere
from ciphers.cryptanalysis import (
    caesar_brute_force, crack_vigenere, guess_key_length, key_length_scores,
    letter_frequencies,
)

st.set_page_config(page_title="LearnCrypt", page_icon="🔐", layout="centered")

# ---------------------------------------------------------------------------
# Look and feel: soft cards, larger text, no "developer" clutter
# ---------------------------------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 17px; }
.block-container { padding-top: 2rem; max-width: 820px; }
h1 { font-weight: 700; }
.lc-card { background: #ffffff; border: 1px solid #e6e2d8; border-radius: 14px;
           padding: 16px 20px; margin: 0 0 12px 0; }
.lc-card h4 { margin: 0 0 4px 0; font-size: 1.05rem; }
.lc-card .lc-sub { color: #6b6a65; font-size: 0.85rem; margin-bottom: 6px; }
.lc-step { display: inline-block; background: #e8eefb; color: #2f57ad; border-radius: 999px;
           padding: 2px 12px; font-size: 0.8rem; font-weight: 600; margin: 18px 0 4px 0; }
.lc-result { background: #eef6ee; border: 1px solid #cfe3cf; border-radius: 12px;
             padding: 14px 18px; font-size: 1.15rem; margin: 8px 0 12px 0; word-break: break-word; }
.lc-result .lc-label { display: block; font-size: 0.8rem; color: #4d6b4d; margin-bottom: 2px; }
.lc-chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 6px 0 10px 0; }
.lc-chip { background: #ffffff; border: 1px solid #e6e2d8; border-radius: 10px; padding: 4px 10px;
           font-size: 0.95rem; }
.lc-chip b { color: #2f57ad; }
.lc-alpha { border-collapse: collapse; margin: 6px 0 10px 0; font-size: 0.85rem; }
.lc-alpha td { border: 1px solid #e6e2d8; width: 26px; text-align: center; padding: 3px 0; background: #fff; }
.lc-alpha tr:first-child td { color: #6b6a65; }
.lc-alpha tr:last-child td { font-weight: 600; color: #2f57ad; }
.lc-alpha td.lc-hit { background: #fff4d6; }
.lc-grid { border-collapse: collapse; margin: 4px 0 12px 0; }
.lc-grid td { border: 1px solid #e6e2d8; width: 40px; height: 40px; text-align: center;
              font-weight: 600; background: #fff; }
.lc-word { display: flex; gap: 12px; align-items: flex-start; }
.lc-word .lc-icon { font-size: 1.6rem; line-height: 1.2; }
.lc-locked { background: #f2f0ea; border: 1px dashed #cfcabd; border-radius: 12px; padding: 14px 18px;
             color: #5d5b55; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Progress and navigation
# ---------------------------------------------------------------------------
PAGES = ["Welcome"] + [name for name, _ in lc.MODULES] + ["Words to know"]
MODULE_IDS = {name: f"m{i + 1}" for i, (name, _) in enumerate(lc.MODULES)}

if "passed" not in st.session_state:
    st.session_state.passed = set()
if "page" not in st.session_state:
    st.session_state.page = "Welcome"


def go(page_name):
    """Button callback: move to another page."""
    st.session_state.page = page_name


def page_label(name):
    """Sidebar label with a tick for finished modules and a lock for locked ones."""
    mid = MODULE_IDS.get(name)
    if mid is None:
        return name
    if mid in st.session_state.passed:
        return f"✅ {name}"
    if mid != "m1" and "m1" not in st.session_state.passed:
        return f"🔒 {name}"
    return name


with st.sidebar:
    st.markdown("### 🔐 LearnCrypt")
    st.caption("Learn how secret messages work, one step at a time.")
    st.radio("Your learning path", PAGES, key="page", format_func=page_label)
    done = len(st.session_state.passed)
    st.progress(done / len(lc.MODULES), text=f"{done} of {len(lc.MODULES)} parts completed")
    st.caption("Please do not type real passwords or private messages. Nothing you type is saved.")


# ---------------------------------------------------------------------------
# Small helpers for drawing friendly pieces
# ---------------------------------------------------------------------------
def inline_md(text):
    """Turn **bold** and *italic* in lesson text into HTML, so it can sit inside a card."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)


def card(title, body, sub=None, icon=None):
    """A soft white box with a title and a short text."""
    head = f"{icon} {html.escape(title)}" if icon else html.escape(title)
    sub_html = f"<div class='lc-sub'>{html.escape(sub)}</div>" if sub else ""
    st.markdown(f"<div class='lc-card'><h4>{head}</h4>{sub_html}<div>{inline_md(body)}</div></div>",
                unsafe_allow_html=True)


def step(label):
    st.markdown(f"<span class='lc-step'>{label}</span>", unsafe_allow_html=True)


def result_box(label, text):
    st.markdown(f"<div class='lc-result'><span class='lc-label'>{html.escape(label)}</span>"
                f"{html.escape(text) or '&nbsp;'}</div>", unsafe_allow_html=True)


def chips(items, limit=18):
    """Show a row of small 'before → after' cards."""
    shown = items[:limit]
    more = f"<span class='lc-chip'>… and {len(items) - limit} more</span>" if len(items) > limit else ""
    inner = "".join(f"<span class='lc-chip'>{c}</span>" for c in shown)
    st.markdown(f"<div class='lc-chips'>{inner}{more}</div>", unsafe_allow_html=True)


def alphabet_strip(shift, used_letters=""):
    """Two rows: the normal alphabet and where each letter moves to."""
    used = {c.upper() for c in used_letters if c.isascii() and c.isalpha()}
    top = "".join(f"<td class='{'lc-hit' if a in used else ''}'>{a}</td>" for a in ALPHABET)
    bottom = "".join(
        f"<td class='{'lc-hit' if a in used else ''}'>{ALPHABET[(i + shift) % 26]}</td>"
        for i, a in enumerate(ALPHABET))
    st.markdown(f"<div style='overflow-x:auto'><table class='lc-alpha'><tr>{top}</tr><tr>{bottom}</tr></table></div>",
                unsafe_allow_html=True)


def quiz(mid, questions):
    """Step 2: questions that must all be answered correctly. Returns True when passed."""
    step("Step 2 · Check your understanding")
    if mid in st.session_state.passed:
        st.success("Well done, you passed this check. The activity below is open.")
        return True

    st.write("Answer these questions to open the activity. You can try as many times as you like.")
    with st.form(f"quiz_{mid}"):
        answers = []
        for i, item in enumerate(questions):
            answers.append(st.radio(f"**{i + 1}. {item['q']}**", item["options"], index=None, key=f"{mid}_q{i}"))
        submitted = st.form_submit_button("Check my answers", type="primary")

    if submitted:
        if any(a is None for a in answers):
            st.warning("Please answer every question first.")
            return False
        all_right = True
        for i, (item, given) in enumerate(zip(questions, answers)):
            if item["options"].index(given) == item["answer"]:
                st.markdown(f"✅ **Question {i + 1}:** correct. {item['explain']}")
            else:
                all_right = False
                st.markdown(f"❌ **Question {i + 1}:** not quite. Hint: {item['explain']}")
        if all_right:
            st.session_state.passed.add(mid)
            st.balloons()
            st.success("All correct! The activity is now open below.")
            return True
        st.info("Read the hints, change your answers and press the button again.")
    return False


def locked_try():
    step("Step 3 · Try it yourself")
    st.markdown("<div class='lc-locked'>🔒 The hands-on activity opens when all the answers above are correct.</div>",
                unsafe_allow_html=True)


def next_button(current_index):
    """Button to move on to the next part."""
    if current_index + 1 < len(lc.MODULES):
        nxt = lc.MODULES[current_index + 1][0]
        st.divider()
        st.button(f"Next: {nxt} →", on_click=go, args=(nxt,), type="primary")


def needs_intro():
    """Parts 2-5 open only after part 1."""
    if "m1" in st.session_state.passed:
        return False
    st.markdown("<div class='lc-locked'>🔒 Please finish <b>Part 1: What is cryptography?</b> first. "
                "It takes about five minutes and explains the words used in the rest of the course.</div>",
                unsafe_allow_html=True)
    st.button("Go to Part 1", on_click=go, args=(lc.MODULES[0][0],), type="primary")
    return True


page = st.session_state.page

# ===========================================================================
# Welcome
# ===========================================================================
if page == "Welcome":
    st.title("Welcome to LearnCrypt")
    st.markdown("#### Discover how your messages, payments and passwords are kept secret, no experience needed.")
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Learn", "A short lesson in everyday language.", icon="📖")
    with c2:
        card("Check", "Two or three quick questions.", icon="✔️")
    with c3:
        card("Try", "Lock, unlock and even break codes yourself.", icon="🧩")
    st.subheader("Your learning path")
    for i, (name, desc) in enumerate(lc.MODULES):
        mid = f"m{i + 1}"
        status = "✅ Completed" if mid in st.session_state.passed else ("Start here" if i == 0 else "")
        card(name, desc, sub=status or None)
    st.button("Start Part 1 →", on_click=go, args=(lc.MODULES[0][0],), type="primary")
    st.caption("About 20 to 30 minutes in total. Your progress is kept while this page stays open.")

# ===========================================================================
# Part 1: What is cryptography?
# ===========================================================================
elif page == lc.MODULES[0][0]:
    st.title("What is cryptography?")
    step("Step 1 · Learn")
    st.markdown(lc.INTRO_LESSON)
    st.markdown("##### Three words you will see everywhere")
    for icon, word, meaning in lc.INTRO_WORDS:
        st.markdown(f"<div class='lc-card lc-word'><div class='lc-icon'>{icon}</div>"
                    f"<div><b>{word}</b><br>{inline_md(meaning)}</div></div>", unsafe_allow_html=True)
    st.markdown(lc.INTRO_LESSON_2)
    if quiz("m1", lc.INTRO_QUIZ):
        step("Step 3 · Try it yourself")
        st.write("Type a short message and watch it get locked with a very simple key: *move every letter 3 places*.")
        msg = st.text_input("Your message", "Meet me at 10")
        locked, _ = caesar(msg, 3)
        result_box("📝 Your message", msg)
        result_box("🔒 Locked message (what an outsider would see)", locked)
        result_box("🔓 Unlocked again with the key", caesar(locked, 3, decrypt=True)[0])
        st.write("This simple code is easy to break, as you will see in Part 3. Modern codes are far stronger.")
        next_button(0)
    else:
        locked_try()

# ===========================================================================
# Part 2: Secret codes from history
# ===========================================================================
elif page == lc.MODULES[1][0]:
    st.title("Secret codes from history")
    if not needs_intro():
        step("Step 1 · Learn")
        st.markdown(lc.CLASSICAL_LESSON)
        for title, age, body in lc.CLASSICAL_CARDS:
            card(title, body, sub=age)
        st.write("Here is the Caesar code with a move of 3. The top row is the normal alphabet, "
                 "the bottom row shows what each letter becomes:")
        alphabet_strip(3)

        if quiz("m2", lc.CLASSICAL_QUIZ):
            step("Step 3 · Try it yourself")
            mode = st.radio("What would you like to do?", ["Lock a message", "Unlock a message"], horizontal=True)
            decrypt = mode == "Unlock a message"
            tab_c, tab_v, tab_p = st.tabs(["Caesar", "Vigenère", "Playfair"])

            with tab_c:
                text = st.text_area("Message", "Hello World", key="c_text", height=80)
                shift = st.slider("Key: how many places to move each letter", 1, 25, 3)
                result, steps = caesar(text, shift, decrypt)
                result_box("Result", result)
                st.write("How each letter changed:")
                alphabet_strip(shift if not decrypt else -shift, text)
                chips([f"<b>{html.escape(s['Input letter'])}</b> → {html.escape(s['Output letter'])}" for s in steps])

            with tab_v:
                text = st.text_area("Message", "Attack at dawn", key="v_text", height=80)
                key = st.text_input("Key: a keyword (letters only)", "LEMON", key="v_key")
                try:
                    result, steps = vigenere(text, key, decrypt)
                    result_box("Result", result)
                    st.write("Each letter moves by the matching letter of the keyword (A = 0, B = 1, C = 2 …):")
                    chips([f"<b>{html.escape(s['Input letter'])}</b> + {s['Key letter']} ({abs(s['Shift'])}) → "
                           f"{html.escape(s['Output letter'])}" for s in steps])
                except ValueError as err:
                    st.error(str(err))

            with tab_p:
                text = st.text_area("Message", "Hide the gold in the tree stump", key="p_text", height=80)
                key = st.text_input("Key: a keyword", "playfair example", key="p_key")
                square = playfair_square(key)
                st.write("The 5 × 5 letter grid made from your keyword (I and J share a square):")
                rows = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in square)
                st.markdown(f"<table class='lc-grid'>{rows}</table>", unsafe_allow_html=True)
                try:
                    result, steps = playfair(text, key, decrypt)
                    result_box("Result", result)
                    st.write("Letters are taken two at a time. The rule used for each pair:")
                    plain_rule = {
                        "Same row: move along the row": "same row, so each letter takes its neighbour",
                        "Same column: move along the column": "same column, so each letter takes the one below or above",
                        "Rectangle: swap the columns": "different row and column, so they swap corners",
                    }
                    chips([f"<b>{s['Input pair']}</b> → {s['Output pair']} <span style='color:#6b6a65'>"
                           f"({plain_rule[s['Rule used']]})</span>" for s in steps], limit=8)
                except ValueError as err:
                    st.error(str(err))
            next_button(1)
        else:
            locked_try()

# ===========================================================================
# Part 3: How old codes are broken
# ===========================================================================
elif page == lc.MODULES[2][0]:
    st.title("How old codes are broken")
    if not needs_intro():
        step("Step 1 · Learn")
        st.markdown(lc.BREAKING_LESSON)
        for title, body in lc.BREAKING_CARDS:
            card(title, body)
        st.markdown(lc.BREAKING_LESSON_2)

        if quiz("m3", lc.BREAKING_QUIZ):
            step("Step 3 · Try it yourself: you are the code breaker")
            tab_bf, tab_freq, tab_vig = st.tabs(["Try every key", "Count the letters", "Break Vigenère"])

            with tab_bf:
                st.write("Paste a Caesar-locked message. The computer tries all 25 keys and picks the one "
                         "that looks most like real English.")
                secret = st.text_area("Locked message", caesar("Meet me at the old bridge tonight", 7)[0], key="bf")
                rows = caesar_brute_force(secret)
                result_box(f"Best guess (key = move {rows[0]['Shift']})", rows[0]["Decrypted text"])
                st.write("The next best guesses look like nonsense, which is how the computer knows:")
                chips([f"<b>move {r['Shift']}</b>: {html.escape(r['Decrypted text'][:30])}" for r in rows[1:6]], limit=5)
                with st.expander("See all 25 tries"):
                    table = pd.DataFrame(rows).rename(columns={
                        "Shift": "Key tried", "Score (chi-squared)": "Difference from English (lower is better)",
                        "Decrypted text": "Result"})
                    st.dataframe(table, hide_index=True, use_container_width=True)

            with tab_freq:
                st.write("Compare how often each letter appears in a locked message with normal English. "
                         "In a Caesar code the pattern is the same, just moved along.")
                text = st.text_area("Text to count", caesar(
                    "Letters like E, T and A appear far more often than letters like Q and Z, "
                    "and this simple fact is enough to break an old code.", 4)[0], key="freq")
                freq = pd.DataFrame(letter_frequencies(text)).set_index("Letter")
                freq = freq.rename(columns={"Text %": "Your text (%)", "English %": "Normal English (%)"})
                st.bar_chart(freq[["Your text (%)", "Normal English (%)"]], stack=False, color=["#3b6fd8", "#c9c6bd"])

            with tab_vig:
                st.write("The 'unbreakable' code. The computer works in two steps.")
                sample = ("Encryption is used every day when people send messages, pay with mobile money or log in to "
                          "online banking. Most people do not see it working, but it protects their data from anyone who "
                          "tries to read it on the way. In the past, simple codes such as the Caesar code and the "
                          "Vigenere code were used by armies and governments to keep their plans secret. These codes "
                          "can now be broken in seconds by a computer, because the patterns of the language still show "
                          "through the locked message.")
                secret = st.text_area("Vigenère-locked message (long messages work best)",
                                      vigenere(sample, "MALAWI")[0], height=150, key="vc")
                st.markdown("**Step 1: guess the length of the keyword.** The right length makes the letters "
                            "look most like English (the tallest bar).")
                scores = pd.DataFrame(key_length_scores(secret)).rename(
                    columns={"Key length": "Keyword length", "Average IoC": "How English-like"}).set_index("Keyword length")
                st.bar_chart(scores, color="#3b6fd8")
                length = st.number_input("Keyword length to use", 1, 12, guess_key_length(secret))
                st.markdown("**Step 2: break each letter of the keyword like a Caesar code.**")
                try:
                    key, plain = crack_vigenere(secret, int(length))
                    result_box("Keyword found", key)
                    st.text_area("Message recovered", plain, height=150)
                except ValueError as err:
                    st.error(str(err))
            next_button(2)
        else:
            locked_try()

# ===========================================================================
# Part 4: How your phone keeps secrets
# ===========================================================================
elif page == lc.MODULES[3][0]:
    st.title("How your phone keeps secrets")
    if not needs_intro():
        step("Step 1 · Learn")
        st.markdown(lc.MODERN_LESSON)
        for icon, title, body in lc.MODERN_CARDS:
            card(title, body, icon=icon)

        if quiz("m4", lc.MODERN_QUIZ):
            step("Step 3 · Try it yourself")
            tab_aes, tab_rsa, tab_sha, tab_file = st.tabs(
                ["🔐 Password lock (AES)", "📮 Public padlock (RSA)", "🧬 Fingerprint (SHA-256)", "📁 Lock a file"])

            with tab_aes:
                st.write("Lock a message with a password. Only someone with the same password can open it. "
                         "A long password is much harder to guess than a short one.")
                mode = st.radio("What would you like to do?", ["Lock", "Unlock"], horizontal=True, key="aes_mode")
                password = st.text_input("Password (practice only)", "practice-password", type="password", key="aes_pw")
                if mode == "Lock":
                    text = st.text_area("Message", "Meet me at the market at 10", key="aes_text", height=80)
                    if st.button("🔐 Lock it", type="primary"):
                        token, steps = modern.aes_encrypt_text(text, password)
                        st.write("Your locked message. Copy it with the button on the right, then try unlocking it:")
                        st.code(token, language=None, wrap_lines=True)
                        st.info("Press **Lock it** again: the locked message changes every time, even for the same "
                                "words, because fresh random values are mixed in. This stops people spotting repeats.")
                        with st.expander("What happened behind the scenes (technical)"):
                            st.dataframe(pd.DataFrame(steps), hide_index=True, use_container_width=True)
                else:
                    token = st.text_area("Paste the locked message here", key="aes_token")
                    if st.button("🔓 Unlock it", type="primary"):
                        try:
                            result_box("Unlocked message", modern.aes_decrypt_text(token, password))
                        except ValueError:
                            st.error("Could not unlock. Either the password is wrong, or the locked message was "
                                     "changed. AES notices even one changed character and refuses to open.")

            with tab_rsa:
                st.write("Your browser has made you an **open padlock** (public key) and its matching "
                         "**private key**. Anyone can lock a note with your padlock, but only your private key opens it.")
                if "rsa_keys" not in st.session_state:
                    st.session_state["rsa_keys"] = modern.rsa_generate()
                private_pem, public_pem = st.session_state["rsa_keys"]
                st.markdown("**1. A friend locks a note with your open padlock**")
                note = st.text_input(f"Their note (up to {modern.RSA_MAX_MESSAGE} letters)", "Your parcel is at the post office")
                try:
                    token = modern.rsa_encrypt(note, public_pem)
                    result_box("🔒 What travels over the internet", token[:90] + "…")
                    st.markdown("**2. You open it with your private key**")
                    result_box("🔓 You read", modern.rsa_decrypt(token, private_pem))
                except ValueError as err:
                    st.error(str(err))
                st.markdown("**3. Signing: a digital wax seal**")
                st.write("You can also seal a message with your private key. Anyone can check the seal with your "
                         "public key. If even one word is changed, the seal breaks.")
                doc = st.text_input("Message you sign", "I owe you 100 kwacha")
                signature = modern.rsa_sign(doc, private_pem)
                checked = st.text_input("Message as it arrives (try changing 100 to 900)", doc)
                if modern.rsa_verify(checked, signature, public_pem):
                    st.success("✅ Seal is intact: the message really came from you and was not changed.")
                else:
                    st.error("❌ Seal is broken: this message was changed after it was signed.")
                with st.expander("See the keys (technical)"):
                    st.button("Make a new key pair", on_click=lambda: st.session_state.update(rsa_keys=modern.rsa_generate()))
                    st.text_area("Public key (the open padlock)", public_pem, height=150)
                    st.text_area("Private key (never share this)", private_pem, height=150)

            with tab_sha:
                st.write("Change just one letter in the second box and compare the two fingerprints.")
                t1 = st.text_input("First message", "hello")
                t2 = st.text_input("Second message", "hellp")
                res = modern.avalanche(t1, t2)
                result_box("🧬 Fingerprint of the first message", res["hash1"])
                result_box("🧬 Fingerprint of the second message", res["hash2"])
                st.metric("Parts of the fingerprint that changed",
                          f"{res['bits_changed']} out of 256 ({res['percent']:.0f}%)")
                st.caption("About half changing is exactly what a good fingerprint should do. "
                           "It means you cannot learn anything about the message from its fingerprint.")

            with tab_file:
                st.write("Lock any small file (a photo or a document) with a password, then unlock it again. "
                         "The file is handled in memory and is not saved anywhere.")
                fmode = st.radio("What would you like to do?", ["Lock a file", "Unlock a .lcrypt file"], horizontal=True)
                upload = st.file_uploader("Choose a file (up to 5 MB)")
                fpass = st.text_input("Password", type="password", key="file_pw")
                if upload and fpass:
                    data = upload.getvalue()
                    if len(data) > 5 * 1024 * 1024:
                        st.error("Please choose a file smaller than 5 MB.")
                    elif fmode == "Lock a file":
                        package, _ = modern.aes_encrypt_bytes(data, fpass)
                        st.download_button("⬇️ Download the locked file", package, file_name=upload.name + ".lcrypt")
                    else:
                        try:
                            plain = modern.aes_decrypt_bytes(data, fpass)
                            name = upload.name[:-7] if upload.name.endswith(".lcrypt") else "unlocked_" + upload.name
                            st.download_button("⬇️ Download the unlocked file", plain, file_name=name)
                        except ValueError:
                            st.error("Could not unlock: wrong password, or the file is not a LearnCrypt locked file.")
            next_button(3)
        else:
            locked_try()

# ===========================================================================
# Part 5: How fast is it?
# ===========================================================================
elif page == lc.MODULES[4][0]:
    from benchmark import SIZES, machine_info, run_benchmark, run_fixed_tests

    st.title("How fast is it?")
    if not needs_intro():
        step("Step 1 · Learn")
        st.markdown(lc.SPEED_LESSON)
        if quiz("m5", lc.SPEED_QUIZ):
            step("Step 3 · Try it yourself: the race")
            st.write("Each method locks the same text, about 30 pages long (100 KB). Which finishes first?")
            if st.button("🏁 Start the race", type="primary"):
                with st.spinner("Racing…"):
                    res = run_benchmark(["100 KB"], repeats=3)
                res = res[~res["Algorithm"].str.contains("decrypt|verify")].copy()
                friendly = {
                    "Caesar (pure Python)": "Caesar (old code)",
                    "Vigenere (pure Python)": "Vigenère (old code)",
                    "Playfair (pure Python)": "Playfair (old code)",
                    "AES-256-GCM encrypt": "AES (modern lock)",
                    "SHA-256 hash": "SHA-256 (fingerprint)",
                    "RSA-2048 sign": "RSA (signature)",
                }
                res["Name"] = res["Algorithm"].map(friendly)
                res = res.sort_values("Median time (ms)")
                fastest = res.iloc[0]
                slowest = res.iloc[-1]
                ratio = slowest["Median time (ms)"] / fastest["Median time (ms)"]
                result_box("Result", f"{fastest['Name']} won. It was about {ratio:,.0f} times faster than {slowest['Name']}.")
                # Simple race bars: the longest bar is the slowest method
                longest = slowest["Median time (ms)"]
                bars = ""
                for _, r in res.iterrows():
                    width = max(0.4, r["Median time (ms)"] / longest * 100)
                    colour = "#3b6fd8" if "old code" not in r["Name"] else "#c9c6bd"
                    bars += (f"<div style='margin:6px 0'><div style='font-size:0.9rem'>{html.escape(r['Name'])} "
                             f"<span style='color:#6b6a65'>· {r['Median time (ms)']:.3f} thousandths of a second</span></div>"
                             f"<div style='background:{colour};height:14px;border-radius:7px;width:{width:.1f}%'></div></div>")
                st.markdown(f"<div class='lc-card'>{bars}</div>", unsafe_allow_html=True)
                st.caption("Blue = modern methods, grey = old codes. The blue bars are so short they are hard "
                           "to see. That is the point!")

            with st.expander("Detailed benchmark for the project report (technical)"):
                sizes = st.multiselect("Input sizes", list(SIZES), default=["1 KB", "10 KB", "100 KB", "1 MB"])
                repeats = st.slider("Repeats per test", 1, 10, 3)
                if st.button("Run detailed benchmark") and sizes:
                    sizes = [s for s in SIZES if s in sizes]
                    bar = st.progress(0.0, "Starting")
                    results = run_benchmark(sizes, repeats, progress=lambda p, msg: bar.progress(p, msg))
                    fixed = run_fixed_tests(repeats)
                    st.caption(f"Machine: {machine_info()}")
                    table = results.pivot(index="Algorithm", columns="Input size", values="Median time (ms)")[sizes]
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
                    st.dataframe(fixed, use_container_width=True, hide_index=True)
                    st.download_button("Download results (CSV)", results.to_csv(index=False), "benchmark_results.csv")

            if len(st.session_state.passed) == len(lc.MODULES):
                st.divider()
                st.success("🎉 You have completed every part of LearnCrypt. Thank you for learning with us!")
        else:
            locked_try()

# ===========================================================================
# Glossary
# ===========================================================================
elif page == "Words to know":
    st.title("Words to know")
    st.write("Short, plain explanations of the words used in LearnCrypt.")
    for word, meaning in lc.GLOSSARY:
        st.markdown(f"<div class='lc-card'><b>{html.escape(word)}</b><br>{html.escape(meaning)}</div>",
                    unsafe_allow_html=True)
