"""
Survey analysis for LearnCrypt: System Usability Scale (SUS) and the
before-and-after knowledge check.

The online form has, in this order: consent, the knowledge questions (before),
a link to the app, the same questions again (after), and the 10 SUS statements
answered from 1 (strongly disagree) to 5 (strongly agree).

Export the answers as CSV and rename the columns to:
    pre1 ... pre6, post1 ... post6, sus1 ... sus10
then run:
    python survey.py answers.csv
"""
import sys

import pandas as pd
from scipy.stats import wilcoxon

# Knowledge check: (question, correct answer). Put these in the form twice,
# before and after, each with two or three wrong answers next to the right one.
QUESTIONS = [
    ("What does encryption do to a message?",
     "Turns it into nonsense that only someone with the key can turn back"),
    ("Why can a computer break a Caesar code so quickly?",
     "There are only 25 possible keys to try"),
    ("What does frequency analysis look at?",
     "How often each letter appears"),
    ("With AES, which key unlocks the message?",
     "The same key that locked it"),
    ("With RSA, which key do you share with other people?",
     "The public key"),
    ("What happens to a SHA-256 fingerprint if you change one letter of the message?",
     "It changes completely"),
]

# Curved grading scale for SUS (Sauro and Lewis, 2016, as used in Lewis, 2018).
# The average SUS score is 68.
GRADES = [(84.1, "A+"), (80.8, "A"), (78.9, "A-"), (77.2, "B+"), (74.1, "B"), (72.6, "B-"),
          (71.1, "C+"), (65.0, "C"), (62.7, "C-"), (51.7, "D"), (0, "F")]


def sus_score(answers):
    """answers: the 10 SUS answers (1 to 5). Returns a score from 0 to 100.
    Odd statements are positive (answer - 1), even ones negative (5 - answer)."""
    total = 0
    for i, a in enumerate(answers):
        total += (a - 1) if i % 2 == 0 else (5 - a)
    return total * 2.5


def sus_grade(score):
    for limit, grade in GRADES:
        if score >= limit:
            return grade


def knowledge_score(row, prefix):
    """Number of correct answers in the 'pre' or 'post' columns of one person."""
    return sum(str(row[f"{prefix}{i + 1}"]).strip() == answer
               for i, (_, answer) in enumerate(QUESTIONS))


def score_answers(df):
    """One row per person: knowledge before, after, the gain, and the SUS score."""
    return pd.DataFrame({
        "Before": df.apply(knowledge_score, axis=1, prefix="pre"),
        "After": df.apply(knowledge_score, axis=1, prefix="post"),
        "SUS": df.apply(lambda r: sus_score([int(r[f"sus{i}"]) for i in range(1, 11)]), axis=1),
    }).assign(Gain=lambda t: t["After"] - t["Before"])


if __name__ == "__main__":
    scores = score_answers(pd.read_csv(sys.argv[1]))
    n = len(scores)
    sus_mean = scores["SUS"].mean()
    print(f"Respondents: {n}")
    print(f"SUS: mean {sus_mean:.1f}, median {scores['SUS'].median():.1f}, "
          f"sd {scores['SUS'].std():.1f}, grade {sus_grade(sus_mean)} (average is 68)")
    print(f"Knowledge (out of {len(QUESTIONS)}): before {scores['Before'].mean():.2f}, "
          f"after {scores['After'].mean():.2f}, mean gain {scores['Gain'].mean():.2f}")
    try:
        test = wilcoxon(scores["After"], scores["Before"])
        print(f"Wilcoxon signed-rank test: W = {test.statistic:.1f}, p = {test.pvalue:.4f}")
    except ValueError as err:
        print("Wilcoxon test could not run:", err)
    scores.to_csv("results/survey_scores.csv", index_label="Respondent")
    print("Saved to results/survey_scores.csv")
