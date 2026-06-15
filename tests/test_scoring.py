"""Scoring is pure and deterministic, so it gets the most exact assertions."""

from app.services.scoring import score_mention


def _score(text: str, brand: str = "Yolando", aliases=None):
    return score_mention(
        brand=brand,
        aliases=aliases or [],
        prompt="q",
        model="mock",
        text=text,
        latency_ms=1,
        cached=False,
    )


def test_not_mentioned_scores_zero():
    r = _score("Here are some options: BrightRank, Beacon, EchoMetrics.")
    assert r.mentioned is False
    assert r.recommended is False
    assert r.rank is None
    assert r.score == 0.0
    assert r.excerpt is None


def test_ranked_first_is_full_score():
    text = "1. Yolando\n2. BrightRank\n3. Beacon"
    r = _score(text)
    assert r.mentioned is True
    assert r.rank == 1
    assert r.recommended is True  # listed => recommended
    assert r.score == 1.0  # 0.4 + 0.3 + 0.3


def test_ranked_third_scores_less_than_first():
    r1 = _score("1. Yolando\n2. A\n3. B")
    r3 = _score("1. A\n2. B\n3. Yolando")
    assert r3.rank == 3
    assert r3.score < r1.score


def test_prose_mention_without_recommendation():
    r = _score("Some people have heard of Yolando in passing.")
    assert r.mentioned is True
    assert r.rank is None
    assert r.recommended is False
    assert r.score == 0.4
    assert r.excerpt is not None


def test_prose_recommendation_keyword():
    r = _score("Honestly, I'd recommend Yolando for that use case.")
    assert r.mentioned is True
    assert r.recommended is True
    assert r.score == 0.7  # 0.4 + 0.3, no rank


def test_alias_is_matched():
    r = _score("Try YolandoAI for this.", brand="Yolando", aliases=["YolandoAI"])
    assert r.mentioned is True


def test_case_insensitive():
    assert _score("we like YOLANDO here").mentioned is True


def test_score_never_exceeds_one():
    r = _score("1. Yolando — the best, top, leading, recommended pick")
    assert r.score <= 1.0
