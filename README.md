# LearnCrypt

An interactive web tool for learning cryptography, built with Python and Streamlit.

Every tool opens straight away. A short plain-language explanation sits in a
"How it works" box on each page for anyone who wants the idea behind it.

Pages:

- **Home**: a quick-lock box, links to the four tools and a glossary
- **Classic ciphers**: Caesar, Vigenère and Playfair with a step-by-step view,
  and a "Try to break it" button that sends your message to the lab
- **Modern crypto**: AES-256-GCM with a password (PBKDF2), RSA-2048 encryption and signatures,
  SHA-256 with the avalanche effect, and file encryption
- **Code-breaking lab**: Caesar brute force, frequency analysis, Vigenère key recovery
- **Speed test**: a quick race, plus a detailed benchmark of every algorithm from 1 KB to 10 MB

To show a survey button in the sidebar, paste the survey link into `SURVEY_URL` at the top of `app.py`.

## Folder layout

```
learncrypt/
├── app.py                     # the Streamlit app (home page and four tools)
├── learn_content.py           # "How it works" text and glossary
├── .streamlit/config.toml     # colours and look of the app
├── benchmark.py               # timing tests (also runs on its own)
├── survey.py                  # SUS and before/after knowledge check scoring
├── ciphers/
│   ├── classical.py           # Caesar, Vigenère, Playfair (written by hand, for teaching)
│   ├── modern.py              # AES, RSA, SHA-256 (uses the cryptography library)
│   └── cryptanalysis.py       # attacks on the classical ciphers
├── tests/                     # 35 unit tests with known test vectors
├── results/                   # saved benchmark and survey results (CSV)
├── requirements.txt           # Python packages the app needs
└── pytest.ini                 # test settings
```

## Setting up on Linux (one time only)

Open a terminal in the `learncrypt` folder and run these lines one by one:

```bash
# 1. Make a virtual environment (a private box for this project's packages)
python3 -m venv venv

# 2. Switch it on (do this every time you open a new terminal)
source venv/bin/activate

# 3. Install the packages
pip install -r requirements.txt
```

If step 1 fails with "ensurepip is not available", run `sudo apt install python3-venv` first.

## Running the app

```bash
source venv/bin/activate
streamlit run app.py
```

Your browser opens at http://localhost:8501.

## Running the tests

```bash
source venv/bin/activate
python -m pytest
```

You should see `35 passed`.

## Running the benchmark on your own computer

```bash
source venv/bin/activate
python benchmark.py --full --repeats 7
```

This takes a few minutes and saves the results in the `results` folder.


## Analysing the survey

The online form asks, in this order: consent, six knowledge questions (before),
a link to the app, the same six questions (after), and the 10 SUS statements (1 to 5).
The questions and their right answers are listed in `QUESTIONS` in `survey.py`.

Export the answers as CSV, rename the columns to `pre1`–`pre6`, `post1`–`post6` and
`sus1`–`sus10`, then run:

```bash
source venv/bin/activate
python survey.py answers.csv
```

It prints the SUS mean, median and grade (average is 68), the knowledge score before and
after with a Wilcoxon signed-rank test, and saves one row per person to `results/survey_scores.csv`.
