"""Prize calculations shared by answer handling and database repair."""

PRIZES = (
    100,
    200,
    300,
    500,
    1000,
    2000,
    4000,
    8000,
    16000,
    32000,
    64000,
    125000,
    250000,
    500000,
    1000000,
)


def prize_for_correct_answers(correct_answers: int) -> int:
    """Return the highest prize already earned after this many correct answers."""
    if correct_answers <= 0:
        return 0
    return PRIZES[min(correct_answers, len(PRIZES)) - 1]
