# LearnCrypt

An interactive web tool for learning cryptography, built with Python and Streamlit
(UU-COM-4005 / COM-4006 final year project).

Modules:

- **Classical ciphers**: Caesar, Vigenère and Playfair with a step-by-step view
- **Modern cryptography**: AES-256-GCM with a password (PBKDF2), RSA-2048 encryption and signatures,
  SHA-256 with the avalanche effect, and file encryption
- **Cryptanalysis lab**: Caesar brute force, frequency analysis, Vigenère key recovery
- **Performance benchmark**: times every algorithm from 1 KB to 10 MB

## Folder layout

```
learncrypt/
├── app.py                     # the Streamlit app (all pages)
├── benchmark.py               # timing tests (also runs on its own)
├── ciphers/
│   ├── classical.py           # Caesar, Vigenère, Playfair (written by hand, for teaching)
│   ├── modern.py              # AES, RSA, SHA-256 (uses the cryptography library)
│   └── cryptanalysis.py       # attacks on the classical ciphers
├── tests/                     # 31 unit tests with known test vectors
├── results/                   # saved benchmark results (CSV)
├── requirements.txt           # Python packages the app needs
└── pytest.ini                 # test settings
```

## Setting up on Linux (one time only)

Open a terminal in the `learncrypt` folder and run these lines one by one:

```bash
# 1. Make a virtual environment (a private box for this project's packages)
python3 -m venv .venv

# 2. Switch it on (do this every time you open a new terminal)
source .venv/bin/activate

# 3. Install the packages
pip install -r requirements.txt
```

If step 1 fails with "ensurepip is not available", run `sudo apt install python3-venv` first.

## Running the app

```bash
source .venv/bin/activate
streamlit run app.py
```

Your browser opens at http://localhost:8501. Press `Ctrl+C` in the terminal to stop it.

## Running the tests

```bash
source .venv/bin/activate
python -m pytest
```

You should see `31 passed`.

## Running the benchmark on your own computer

```bash
source .venv/bin/activate
python benchmark.py --full --repeats 7
```

This takes a few minutes and saves the results in the `results` folder.

## Putting it online (GitHub + Streamlit Community Cloud)

1. Create a free account at https://github.com, click **New repository**, name it `learncrypt`,
   choose **Public**, and click **Create repository**.
2. On the new repository page click **uploading an existing file**. Drag in everything inside the
   `learncrypt` folder **except** the `.venv` folder, then click **Commit changes**.
   (Check that `app.py`, `requirements.txt` and the `ciphers` folder are there.)
3. Go to https://share.streamlit.io, sign in with GitHub, click **Create app**, choose the
   `learncrypt` repository, branch `main`, main file `app.py`, and click **Deploy**.
4. After a few minutes you get a link like `https://<something>.streamlit.app`. Open it on your
   phone and laptop to check every page works. This is the [APP LINK] for the survey.
