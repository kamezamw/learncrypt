"""
LearnCrypt - main Streamlit app.
Start it with:   streamlit run app.py

Every part of the course has three steps:
    1. Learn - a short lesson in plain language
    2. Check - a few questions; all must be right to continue
    3. Try   - the activity, which opens only after step 2
Lesson text and questions are in learn_content.py.
"""
import html
import random
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

st.set_page_config(page_title="LearnCrypt", layout="centered")

# Colours used by the page (kept here so they are easy to change)
INK = "#23211d"
MUTED = "#6f6a60"
ACCENT = "#2f5d4e"      # deep green, used for buttons, links and the modern methods
OLD = "#b9b2a3"         # warm grey, used for the old codes
RULE = "#e2dccf"

st.markdown(f"""
<style>
html, body, [class*="css"] {{ font-size: 17px; }}
.block-container {{ padding-top: 2.2rem; max-width: 780px; }}
h1, h2, h3, h4, h5 {{ font-family: Georgia, "Times New Roman", serif !important; font-weight: 600 !important;
                     color: {INK}; letter-spacing: 0 !important; }}
.lc-box {{ border: 1px solid {RULE}; border-radius: 6px; padding: 14px 18px; margin: 0 0 12px 0; background: #fffdf8; }}
.lc-box h4 {{ margin: 0 0 6px 0; font-size: 1.05rem; }}
.lc-box .lc-sub {{ color: {MUTED}; font-size: 0.85rem; margin: -2px 0 6px 0; }}
.lc-step {{ border-top: 1px solid {RULE}; margin: 28px 0 8px 0; padding-top: 10px; color: {MUTED};
           font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase; }}
.lc-result {{ border-left: 3px solid {ACCENT}; background: #f4f1e8; padding: 10px 14px; margin: 8px 0 12px 0;
             font-size: 1.1rem; word-break: break-word; }}
.lc-result span {{ display: block; font-size: 0.8rem; color: {MUTED}; margin-bottom: 2px; }}
.lc-pairs {{ font-size: 0.95rem; line-height: 1.9; margin: 4px 0 12px 0; }}
.lc-pairs span {{ display: inline-block; margin-right: 16px; }}
.lc-pairs b {{ color: {ACCENT}; }}
.lc-alpha {{ border-collapse: collapse; margin: 6px 0 12px 0; font-size: 0.85rem; }}
.lc-alpha td {{ border: 1px solid {RULE}; width: 26px; text-align: center; padding: 3px 0; background: #fffdf8; }}
.lc-alpha tr:first-child td {{ color: {MUTED}; }}
.lc-alpha tr:last-child td {{ font-weight: 600; color: {INK}; }}
.lc-alpha td.hit {{ background: #f6e7c1; }}
.lc-grid {{ border-collapse: collapse; margin: 4px 0 12px 0; }}
.lc-grid td {{ border: 1px solid {RULE}; width: 38px; height: 38px; text-align: center; font-weight: 600;
              background: #fffdf8; }}
.lc-locked {{ border: 1px dashed #cfc8b8; border-radius: 6px; padding: 12px 16px; color: {MUTED}; }}
.lc-feedback {{ border-left: 3px solid {RULE}; padding: 2px 0 2px 12px; margin: 6px 0; }}
.lc-feedback.right {{ border-color: {ACCENT}; }}
.lc-feedback.wrong {{ border-color: #b5654a; }}
</style>
""", unsafe_allow_html=True)

# Progress and navigation
PAGES = ["Introduction"] + [name for name, _ in lc.MODULES] + ["Words to know"]
MODULE_IDS = {name: f"m{i + 1}" for i, (name, _) in enumerate(lc.MODULES)}

if "passed" not in st.session_state:
    st.session_state.passed = set()
if "page" not in st.session_state:
    st.session_state.page = "Introduction"


def go(page_name):
    st.session_state.page = page_name


def page_label(name):
    """Sidebar label: a tick for finished parts, '(locked)' for parts not open yet."""
    mid = MODULE_IDS.get(name)
    if mid in st.session_state.passed:
        return f"{name}  ✓"
    if mid and mid != "m1" and "m1" not in st.session_state.passed:
        return f"{name}  (locked)"
    return name


with st.sidebar:
    st.markdown("### LearnCrypt")
    st.caption("A short course on how secret messages work.")
    st.radio("Contents", PAGES, key="page", format_func=page_label)
    done = len(st.session_state.passed)
    st.progress(done / len(lc.MODULES), text=f"{done} of {len(lc.MODULES)} parts finished")
    st.caption("Please do not type real passwords or private messages. Nothing you type is saved.")


# Helpers for the page parts
def inline_md(text):
    """Turn **bold** and *italic* into HTML so lesson text can sit inside a box."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)


def box(title, body, sub=None):
    sub_html = f"<div class='lc-sub'>{html.escape(sub)}</div>" if sub else ""
    st.markdown(f"<div class='lc-box'><h4>{html.escape(title)}</h4>{sub_html}<div>{inline_md(body)}</div></div>",
                unsafe_allow_html=True)


def step(number, label):
    st.markdown(f"<div class='lc-step'>Step {number} of 3 &nbsp;|&nbsp; {label}</div>", unsafe_allow_html=True)


def result(label, text):
    st.markdown(f"<div class='lc-result'><span>{html.escape(label)}</span>{html.escape(text) or '&nbsp;'}</div>",
                unsafe_allow_html=True)


def pairs(items, limit=18):
    """A line of 'before → after' pairs, e.g. H → K."""
    shown = "".join(f"<span>{p}</span>" for p in items[:limit])
    more = f"<span>and {len(items) - limit} more</span>" if len(items) > limit else ""
    st.markdown(f"<div class='lc-pairs'>{shown}{more}</div>", unsafe_allow_html=True)


def alphabet_strip(shift, used_letters=""):
    """Top row: the normal alphabet. Bottom row: what each letter becomes."""
    used = {c.upper() for c in used_letters if c.isascii() and c.isalpha()}
    top = "".join(f"<td class='{'hit' if a in used else ''}'>{a}</td>" for a in ALPHABET)
    bottom = "".join(f"<td class='{'hit' if a in used else ''}'>{ALPHABET[(i + shift) % 26]}</td>"
                     for i, a in enumerate(ALPHABET))
    st.markdown(f"<div style='overflow-x:auto'><table class='lc-alpha'><tr>{top}</tr><tr>{bottom}</tr></table></div>",
                unsafe_allow_html=True)


def quiz(mid, questions):
    """Step 2. Returns True once every answer has been right."""
    step(2, "Check your understanding")
    if mid in st.session_state.passed:
        st.markdown("You have answered these questions correctly, so the activity below is open.")
        return True

    st.markdown("Answer the questions to open the activity. You can try again as many times as you need.")
    with st.form(f"quiz_{mid}"):
        answers = [st.radio(f"**{i + 1}. {item['q']}**", item["options"], index=None, key=f"{mid}_q{i}")
                   for i, item in enumerate(questions)]
        submitted = st.form_submit_button("Check my answers", type="primary")

    if not submitted:
        return False
    if any(a is None for a in answers):
        st.warning("Please answer every question first.")
        return False

    all_right = True
    for i, (item, given) in enumerate(zip(questions, answers)):
        right = item["options"].index(given) == item["answer"]
        all_right = all_right and right
        verdict = "Correct." if right else "Not yet. Hint:"
        st.markdown(f"<div class='lc-feedback {'right' if right else 'wrong'}'><b>Question {i + 1}.</b> "
                    f"{verdict} {html.escape(item['explain'])}</div>", unsafe_allow_html=True)
    if all_right:
        st.session_state.passed.add(mid)
        st.success("All answers are correct. The activity is now open below.")
        return True
    st.info("Change the answers marked 'Not yet' and press the button again.")
    return False


def locked_activity():
    step(3, "Try it yourself")
    st.markdown("<div class='lc-locked'>The activity opens when all the answers above are correct.</div>",
                unsafe_allow_html=True)


def next_part(current_index):
    if current_index + 1 < len(lc.MODULES):
        nxt = lc.MODULES[current_index + 1][0]
        st.divider()
        st.button(f"Continue to {nxt}", on_click=go, args=(nxt,), type="primary")


def needs_part_one():
    """Parts 2 to 5 open only after Part 1."""
    if "m1" in st.session_state.passed:
        return False
    st.markdown("<div class='lc-locked'>Please finish <b>Part 1: What is cryptography?</b> first. It takes about "
                "five minutes and explains the words used in the rest of the course.</div>", unsafe_allow_html=True)
    st.write("")
    st.button("Go to Part 1", on_click=go, args=(lc.MODULES[0][0],), type="primary")
    return True


page = st.session_state.page

# Introduction page
if page == "Introduction":
    st.title("LearnCrypt")
    st.markdown("##### How your messages, payments and passwords are kept secret, explained for everyone.")
    st.markdown(
        "This is a short course in five parts. No computer or maths background is needed. "
        "Each part begins with a short lesson. You then answer two or three questions, and when they are "
        "right, an activity opens where you can lock and unlock messages, or even break old codes yourself.")
    st.markdown("#### Contents")
    for i, (name, desc) in enumerate(lc.MODULES):
        status = "  (finished)" if f"m{i + 1}" in st.session_state.passed else ""
        st.markdown(f"**{name}**{status}  \n<span style='color:{MUTED}'>{html.escape(desc)}</span>",
                    unsafe_allow_html=True)
    st.write("")
    st.button("Begin with Part 1", on_click=go, args=(lc.MODULES[0][0],), type="primary")
    st.caption("The whole course takes about 20 to 30 minutes. Progress is kept while this page stays open.")

# Part 1: What is cryptography?
elif page == lc.MODULES[0][0]:
    st.title("What is cryptography?")
    step(1, "Learn")
    st.markdown(lc.INTRO_LESSON)
    st.markdown("#### Three words used throughout")
    for word, meaning in lc.INTRO_WORDS:
        box(word, meaning)
    st.markdown(lc.INTRO_LESSON_2)
    if quiz("m1", lc.INTRO_QUIZ):
        step(3, "Try it yourself")
        st.markdown("Type a short message and see it locked with a very simple key: *move every letter 3 places*.")
        msg = st.text_input("Your message", "Meet me at 10")
        locked, _ = caesar(msg, 3)
        result("Your message", msg)
        result("Locked message (what an outsider would see)", locked)
        result("Unlocked again with the key", caesar(locked, 3, decrypt=True)[0])
        st.markdown("This simple code is easy to break, as Part 3 will show. Modern codes are much stronger.")
        next_part(0)
    else:
        locked_activity()

# Part 2: Secret codes from history
elif page == lc.MODULES[1][0]:
    st.title("Secret codes from history")
    if not needs_part_one():
        step(1, "Learn")
        st.markdown(lc.CLASSICAL_LESSON)
        for title, age, body in lc.CLASSICAL_CARDS:
            box(title, body, sub=age)
        st.markdown("The Caesar code with a move of 3. The top row is the normal alphabet and the bottom row "
                    "shows what each letter becomes:")
        alphabet_strip(3)

        if quiz("m2", lc.CLASSICAL_QUIZ):
            step(3, "Try it yourself")
            mode = st.radio("What would you like to do?", ["Lock a message", "Unlock a message"], horizontal=True)
            decrypt = mode == "Unlock a message"
            tab_c, tab_v, tab_p = st.tabs(["Caesar", "Vigenère", "Playfair"])

            with tab_c:
                text = st.text_area("Message", "Hello World", key="c_text", height=80)
                shift = st.slider("Key: how many places each letter moves", 1, 25, 3)
                out, steps = caesar(text, shift, decrypt)
                result("Result", out)
                st.markdown("Letters in your message are shaded:")
                alphabet_strip(-shift if decrypt else shift, text)
                pairs([f"<b>{html.escape(s['Input letter'])}</b> → {html.escape(s['Output letter'])}" for s in steps])

            with tab_v:
                text = st.text_area("Message", "Attack at dawn", key="v_text", height=80)
                key = st.text_input("Key: a keyword (letters only)", "LEMON", key="v_key")
                try:
                    out, steps = vigenere(text, key, decrypt)
                    result("Result", out)
                    st.markdown("Each letter moves by the matching letter of the keyword (A = 0, B = 1, C = 2 and so on):")
                    pairs([f"<b>{html.escape(s['Input letter'])}</b> + {s['Key letter']} ({abs(s['Shift'])}) → "
                           f"{html.escape(s['Output letter'])}" for s in steps])
                except ValueError as err:
                    st.error(str(err))

            with tab_p:
                text = st.text_area("Message", "Hide the gold in the tree stump", key="p_text", height=80)
                key = st.text_input("Key: a keyword", "playfair example", key="p_key")
                st.markdown("The 5 × 5 letter grid made from your keyword (I and J share a square):")
                rows = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
                               for row in playfair_square(key))
                st.markdown(f"<table class='lc-grid'>{rows}</table>", unsafe_allow_html=True)
                try:
                    out, steps = playfair(text, key, decrypt)
                    result("Result", out)
                    st.markdown("Letters are taken two at a time. How each pair was changed:")
                    plain_rule = {
                        "Same row: move along the row": "same row, each letter takes its neighbour",
                        "Same column: move along the column": "same column, each letter takes the one below",
                        "Rectangle: swap the columns": "different row and column, they swap corners",
                    }
                    pairs([f"<b>{s['Input pair']}</b> → {s['Output pair']} "
                           f"<span style='color:{MUTED}'>({plain_rule[s['Rule used']]})</span>" for s in steps], limit=8)
                except ValueError as err:
                    st.error(str(err))
            next_part(1)
        else:
            locked_activity()

# Part 3: How old codes are broken
elif page == lc.MODULES[2][0]:
    st.title("How old codes are broken")
    if not needs_part_one():
        step(1, "Learn")
        st.markdown(lc.BREAKING_LESSON)
        for title, body in lc.BREAKING_CARDS:
            box(title, body)
        st.markdown(lc.BREAKING_LESSON_2)

        if quiz("m3", lc.BREAKING_QUIZ):
            step(3, "Try it yourself: you are the code breaker")
            tab_bf, tab_freq, tab_vig = st.tabs(["Try every key", "Count the letters", "Break Vigenère"])

            with tab_bf:
                # A secret message for the learner to break: a sentence locked with a random key
                def new_mystery():
                    st.session_state.bf = caesar(random.choice(lc.MYSTERY_MESSAGES), random.randint(1, 25))[0]

                if "bf" not in st.session_state:
                    new_mystery()
                st.markdown("The box below holds a secret message that was intercepted. It was locked with a "
                            "Caesar code, but nobody told us the key. The computer tries all 25 keys and picks the "
                            "one that looks most like real English.")
                st.button("Give me a different secret message", on_click=new_mystery)
                secret = st.text_area("Intercepted message", key="bf")
                st.caption("You can also break your own: lock a message in Part 2 (Caesar tab), copy the result "
                           "and paste it in the box above.")
                rows = caesar_brute_force(secret)
                result(f"Best guess, using key {rows[0]['Shift']}", rows[0]["Decrypted text"])
                st.markdown("The next best tries look like nonsense, which is how the computer can tell:")
                pairs([f"<b>key {r['Shift']}</b>: {html.escape(r['Decrypted text'][:30])}" for r in rows[1:5]], limit=4)
                with st.expander("See all 25 tries"):
                    table = pd.DataFrame(rows).rename(columns={
                        "Shift": "Key tried", "Score (chi-squared)": "Difference from English (lower is better)",
                        "Decrypted text": "Result"})
                    st.dataframe(table, hide_index=True, use_container_width=True)

            with tab_freq:
                st.markdown("The box already holds a locked message, and you can replace it with any text. "
                            "The chart compares how often each letter appears in it with normal English. "
                            "In a Caesar code the pattern is the same, just moved along.")
                text = st.text_area("Text to count", caesar(
                    "Letters like E, T and A appear far more often than letters like Q and Z, "
                    "and this simple fact is enough to break an old code.", 4)[0], key="freq")
                freq = pd.DataFrame(letter_frequencies(text)).set_index("Letter")
                freq = freq.rename(columns={"Text %": "Your text (%)", "English %": "Normal English (%)"})
                st.bar_chart(freq[["Your text (%)", "Normal English (%)"]], stack=False, color=[ACCENT, OLD])

            with tab_vig:
                st.markdown("The box holds a long message locked with a Vigenère keyword that we do not know. "
                            "The computer breaks it in two steps.")
                sample = ("Encryption is used every day when people send messages, pay with mobile money or log in to "
                          "online banking. Most people do not see it working, but it protects their data from anyone "
                          "who tries to read it on the way. In the past, simple codes such as the Caesar code and the "
                          "Vigenere code were used by armies and governments to keep their plans secret. These codes "
                          "can now be broken in seconds by a computer, because the patterns of the language still "
                          "show through the locked message.")
                secret = st.text_area("Locked message (long messages work best)", vigenere(sample, "MALAWI")[0],
                                      height=150, key="vc")
                st.markdown("**Step A: guess the length of the keyword.** The right length makes the letters look "
                            "most like English, so it has the tallest bar.")
                scores = pd.DataFrame(key_length_scores(secret)).rename(
                    columns={"Key length": "Keyword length", "Average IoC": "How English-like"}).set_index("Keyword length")
                st.bar_chart(scores, color=ACCENT)
                length = st.number_input("Keyword length to use", 1, 12, guess_key_length(secret))
                st.markdown("**Step B: break each letter of the keyword like a Caesar code.**")
                try:
                    key, plain = crack_vigenere(secret, int(length))
                    result("Keyword found", key)
                    st.text_area("Message recovered", plain, height=150)
                except ValueError as err:
                    st.error(str(err))
            next_part(2)
        else:
            locked_activity()

# Part 4: How your phone keeps secrets
elif page == lc.MODULES[3][0]:
    st.title("How your phone keeps secrets")
    if not needs_part_one():
        step(1, "Learn")
        st.markdown(lc.MODERN_LESSON)
        for title, body in lc.MODERN_CARDS:
            box(title, body)

        if quiz("m4", lc.MODERN_QUIZ):
            step(3, "Try it yourself")
            tab_aes, tab_rsa, tab_sha, tab_file = st.tabs(
                ["Password lock (AES)", "Public padlock (RSA)", "Fingerprint (SHA-256)", "Lock a file"])

            with tab_aes:
                st.markdown("Lock a message with a password. Only someone with the same password can open it. "
                            "A long password is much harder to guess than a short one.")
                mode = st.radio("What would you like to do?", ["Lock", "Unlock"], horizontal=True, key="aes_mode")
                password = st.text_input("Password (practice only)", "practice-password", type="password", key="aes_pw")
                if mode == "Lock":
                    text = st.text_area("Message", "Meet me at the market at 10", key="aes_text", height=80)
                    if st.button("Lock the message", type="primary"):
                        token, aes_steps = modern.aes_encrypt_text(text, password)
                        st.markdown("Your locked message. Copy it with the small button on the right, choose "
                                    "**Unlock** above and paste it in:")
                        st.code(token, language=None, wrap_lines=True)
                        st.info("Press the button again and the locked message changes, even for the same words. "
                                "Fresh random values are mixed in each time, so nobody can spot repeated messages.")
                        with st.expander("What happened behind the scenes (technical)"):
                            st.dataframe(pd.DataFrame(aes_steps), hide_index=True, use_container_width=True)
                else:
                    token = st.text_area("Paste the locked message here", key="aes_token")
                    if st.button("Unlock the message", type="primary"):
                        try:
                            result("Unlocked message", modern.aes_decrypt_text(token, password))
                        except ValueError:
                            st.error("Could not unlock. Either the password is wrong, or the locked message was "
                                     "changed. AES notices even one changed character and refuses to open.")

            with tab_rsa:
                st.markdown("LearnCrypt has made you an **open padlock** (public key) and its matching "
                            "**private key**. Anyone can lock a note with your padlock, but only your private key "
                            "opens it.")
                if "rsa_keys" not in st.session_state:
                    st.session_state["rsa_keys"] = modern.rsa_generate()
                private_pem, public_pem = st.session_state["rsa_keys"]
                st.markdown("**1. A friend locks a note with your open padlock**")
                note = st.text_input(f"Their note (up to {modern.RSA_MAX_MESSAGE} letters)",
                                     "Your parcel is at the post office")
                try:
                    token = modern.rsa_encrypt(note, public_pem)
                    result("What travels over the internet (shortened)", token[:90] + "...")
                    st.markdown("**2. You open it with your private key**")
                    result("What you read", modern.rsa_decrypt(token, private_pem))
                except ValueError as err:
                    st.error(str(err))
                st.markdown("**3. Signing, like a wax seal**")
                st.markdown("You can also seal a message with your private key. Anyone can check the seal with "
                            "your public key. If one word is changed, the seal no longer matches.")
                doc = st.text_input("Message you sign", "I owe you 100 kwacha")
                signature = modern.rsa_sign(doc, private_pem)
                checked = st.text_input("Message as it arrives (try changing 100 to 900)", doc)
                if modern.rsa_verify(checked, signature, public_pem):
                    st.success("The seal matches: the message came from you and was not changed.")
                else:
                    st.error("The seal does not match: this message was changed after it was signed.")
                with st.expander("See the keys (technical)"):
                    st.button("Make a new key pair",
                              on_click=lambda: st.session_state.update(rsa_keys=modern.rsa_generate()))
                    st.text_area("Public key (the open padlock)", public_pem, height=150)
                    st.text_area("Private key (never share this)", private_pem, height=150)

            with tab_sha:
                st.markdown("Change just one letter in the second box and compare the two fingerprints.")
                t1 = st.text_input("First message", "hello")
                t2 = st.text_input("Second message", "hellp")
                res = modern.avalanche(t1, t2)
                result("Fingerprint of the first message", res["hash1"])
                result("Fingerprint of the second message", res["hash2"])
                st.metric("Parts of the fingerprint that changed",
                          f"{res['bits_changed']} out of 256 ({res['percent']:.0f}%)")
                st.caption("A good fingerprint changes about half of its parts for any small change, so it gives "
                           "away nothing about the message.")

            with tab_file:
                st.markdown("Lock a small file, such as a photo or a document, with a password, then unlock it "
                            "again. The file is handled in memory and is not saved anywhere.")
                fmode = st.radio("What would you like to do?", ["Lock a file", "Unlock a .lcrypt file"], horizontal=True)
                upload = st.file_uploader("Choose a file (up to 5 MB)")
                fpass = st.text_input("Password", type="password", key="file_pw")
                if upload and fpass:
                    data = upload.getvalue()
                    if len(data) > 5 * 1024 * 1024:
                        st.error("Please choose a file smaller than 5 MB.")
                    elif fmode == "Lock a file":
                        package, _ = modern.aes_encrypt_bytes(data, fpass)
                        st.download_button("Download the locked file", package, file_name=upload.name + ".lcrypt")
                    else:
                        try:
                            plain = modern.aes_decrypt_bytes(data, fpass)
                            name = upload.name[:-7] if upload.name.endswith(".lcrypt") else "unlocked_" + upload.name
                            st.download_button("Download the unlocked file", plain, file_name=name)
                        except ValueError:
                            st.error("Could not unlock: wrong password, or the file is not a LearnCrypt locked file.")
            next_part(3)
        else:
            locked_activity()

# Part 5: How fast is it?
elif page == lc.MODULES[4][0]:
    from benchmark import SIZES, machine_info, run_benchmark, run_fixed_tests

    st.title("How fast is it?")
    if not needs_part_one():
        step(1, "Learn")
        st.markdown(lc.SPEED_LESSON)
        if quiz("m5", lc.SPEED_QUIZ):
            step(3, "Try it yourself: a race")
            st.markdown("Each method locks the same text, about 30 pages long (100 KB). Which finishes first?")
            if st.button("Start the race", type="primary"):
                with st.spinner("Racing..."):
                    res = run_benchmark(["100 KB"], repeats=3)
                friendly = {
                    "Caesar (pure Python)": "Caesar (old code)",
                    "Vigenere (pure Python)": "Vigenère (old code)",
                    "Playfair (pure Python)": "Playfair (old code)",
                    "AES-256-GCM encrypt": "AES (modern lock)",
                    "SHA-256 hash": "SHA-256 (fingerprint)",
                    "RSA-2048 sign": "RSA (signature)",
                }
                res = res[res["Algorithm"].isin(friendly)].copy()
                res["Name"] = res["Algorithm"].map(friendly)
                res = res.sort_values("Median time (ms)")
                fastest, slowest = res.iloc[0], res.iloc[-1]
                ratio = slowest["Median time (ms)"] / fastest["Median time (ms)"]
                result("Result", f"{fastest['Name']} finished first, about {ratio:,.0f} times faster than "
                                 f"{slowest['Name']}.")
                bars = ""
                for _, r in res.iterrows():
                    width = max(0.4, r["Median time (ms)"] / slowest["Median time (ms)"] * 100)
                    colour = OLD if "old code" in r["Name"] else ACCENT
                    bars += (f"<div style='margin:8px 0'><div style='font-size:0.9rem'>{html.escape(r['Name'])}, "
                             f"<span style='color:{MUTED}'>{r['Median time (ms)']:.3f} thousandths of a second</span></div>"
                             f"<div style='background:{colour};height:12px;width:{width:.1f}%'></div></div>")
                st.markdown(f"<div class='lc-box'>{bars}</div>", unsafe_allow_html=True)
                st.caption("Green bars are the modern methods and grey bars the old codes. Some green bars are "
                           "so short they are hard to see.")

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
                    for name in table.index:
                        old = "pure Python" in name
                        ax.plot([SIZES[s] for s in sizes], table.loc[name], marker="o", linewidth=1.5,
                                color=OLD if old else ACCENT, linestyle="--" if old else "-", label=name)
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
                st.success("You have finished all five parts of LearnCrypt. Thank you for taking the course.")
        else:
            locked_activity()

# Glossary
elif page == "Words to know":
    st.title("Words to know")
    st.markdown("Plain explanations of the words used in LearnCrypt.")
    for word, meaning in lc.GLOSSARY:
        box(word, meaning)
