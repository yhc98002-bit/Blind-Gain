from fractions import Fraction

from src.eval.scorer_accounting import strict_gain_decomposition


def test_strict_gain_equals_answer_gain_plus_format_component_exactly() -> None:
    before = [
        {"acc_final": True, "acc_strict": False},
        {"acc_final": False, "acc_strict": False},
        {"acc_final": False, "acc_strict": False},
    ]
    after = [
        {"acc_final": True, "acc_strict": True},
        {"acc_final": True, "acc_strict": False},
        {"acc_final": False, "acc_strict": False},
    ]

    decomposition = strict_gain_decomposition(before, after)

    assert decomposition == {
        "StrictGain": Fraction(1, 3),
        "AnswerGain": Fraction(1, 3),
        "G_format": Fraction(0, 1),
    }
    assert decomposition["StrictGain"] == (
        decomposition["AnswerGain"] + decomposition["G_format"]
    )
