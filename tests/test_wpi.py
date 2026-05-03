"""Tests for Weekly Platform Intelligence."""

from wpi.sources import Item
from wpi.brief import _keyword_score
from wpi.brief import _template_brief, PORTFOLIO_SPOTLIGHT


def make_item(title: str, source: str = "Test", relevance: float = 0.8) -> Item:
    return Item(title=title, url="https://example.com", source=source, summary="Test summary", relevance=relevance)


def test_keyword_score_returns_sorted() -> None:
    items = [
        Item(title="Platform engineering trends", url="https://x.com", source="InfoQ", summary=""),
        Item(title="Celebrity news today", url="https://y.com", source="TMZ", summary=""),
        Item(title="OPA policy as code compliance automation", url="https://z.com", source="CNCF", summary=""),
    ]
    scored = _keyword_score(items)
    assert scored[0].relevance >= scored[1].relevance >= scored[2].relevance


def test_keyword_score_platform_engineering_scores_high() -> None:
    items = [
        Item(title="Platform engineering DORA metrics SOX compliance", url="https://x.com", source="Test", summary="OPA policy governance regulated"),
    ]
    scored = _keyword_score(items)
    assert scored[0].relevance > 0.1


def test_keyword_score_irrelevant_scores_low() -> None:
    items = [
        Item(title="Best pizza recipes for summer", url="https://x.com", source="Food", summary="Tomato cheese basil"),
    ]
    scored = _keyword_score(items)
    assert scored[0].relevance < 0.2


def test_template_brief_contains_issue_number() -> None:
    items = [make_item("Platform engineering news")]
    brief = _template_brief(items, issue_num=5, week_num=20, today=__import__("datetime").date(2026, 5, 19), spotlight=PORTFOLIO_SPOTLIGHT[0])
    assert "Issue #5" in brief
    assert "Week 20" in brief


def test_template_brief_contains_spotlight() -> None:
    items = [make_item("Test item")]
    brief = _template_brief(items, issue_num=1, week_num=1, today=__import__("datetime").date(2026, 1, 6), spotlight=PORTFOLIO_SPOTLIGHT[0])
    assert "orbit-platform" in brief


def test_template_brief_contains_footer() -> None:
    items = [make_item("Test item")]
    brief = _template_brief(items, issue_num=1, week_num=1, today=__import__("datetime").date(2026, 1, 6), spotlight=PORTFOLIO_SPOTLIGHT[0])
    assert "Follow this repo" in brief


def test_portfolio_spotlight_rotates() -> None:
    assert len(PORTFOLIO_SPOTLIGHT) >= 6
    names = [s[0] for s in PORTFOLIO_SPOTLIGHT]
    assert "orbit-platform" in names
    assert "ai-governance-framework" in names


def test_item_defaults() -> None:
    item = Item(title="Test", url="https://x.com", source="Test")
    assert item.relevance == 0.0
    assert item.summary == ""