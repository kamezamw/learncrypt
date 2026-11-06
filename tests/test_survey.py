"""Unit tests for the survey scoring (SUS and knowledge check)."""
import pandas as pd

from survey import QUESTIONS, score_answers, sus_grade, sus_score


def test_sus_neutral_answers_give_50():
    assert sus_score([3] * 10) == 50


def test_sus_best_and_worst_answers():
    assert sus_score([5, 1] * 5) == 100
    assert sus_score([1, 5] * 5) == 0


def test_sus_grade_of_average_score():
    assert sus_grade(68) == "C"
    assert sus_grade(90) == "A+"


def test_knowledge_and_gain():
    right = [answer for _, answer in QUESTIONS]
    row = {f"pre{i + 1}": "wrong" for i in range(len(QUESTIONS))}
    row.update({f"post{i + 1}": a for i, a in enumerate(right)})
    row.update({f"sus{i}": 3 for i in range(1, 11)})
    scores = score_answers(pd.DataFrame([row]))
    assert scores.loc[0, "Before"] == 0
    assert scores.loc[0, "After"] == len(QUESTIONS)
    assert scores.loc[0, "Gain"] == len(QUESTIONS)
