"""News and feed sources for Weekly Platform Intelligence."""

from __future__ import annotations

import httpx
import feedparser
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta


@dataclass
class Item:
    """A single news or content item."""
    title: str
    url: str
    source: str
    summary: str = ""
    published: str = ""
    relevance: float = 0.0


FEEDS = [
    ("Gartner Research", "https://www.gartner.com/en/newsroom/rss"),
    ("InfoQ Platform", "https://feed.infoq.com/"),
    ("CISA Advisories", "https://www.cisa.gov/news.xml"),
    ("ACM TechNews", "https://technews.acm.org/rss.xml"),
    ("ThoughtWorks", "https://www.thoughtworks.com/rss/insights.xml"),
    ("Martin Fowler", "https://martinfowler.com/feed.atom"),
]

HACKERNEWS_KEYWORDS = [
    "platform engineering", "agentic", "compliance automation",
    "policy as code", "OPA", "regulated", "SOX", "PCI-DSS",
    "model risk", "AI governance", "machine readable", "LangGraph",
    "backstage", "internal developer platform", "DORA metrics",
]

GITHUB_TOPICS = [
    "platform-engineering", "policy-as-code", "compliance-automation",
    "ai-governance", "backstage", "opa", "langchain", "mlops",
]


def fetch_feeds(max_age_days: int = 7) -> list[Item]:
    """Fetch items from RSS/Atom feeds published in the last N days."""
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

    for source_name, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")[:500]
                published = entry.get("published", "")
                if title and link:
                    items.append(Item(
                        title=title,
                        url=link,
                        source=source_name,
                        summary=summary,
                        published=published,
                    ))
        except Exception:
            continue

    return items


def fetch_hackernews(max_items: int = 30) -> list[Item]:
    """Fetch relevant HackerNews stories via Algolia API."""
    items = []
    try:
        with httpx.Client(timeout=15) as client:
            for keyword in HACKERNEWS_KEYWORDS[:5]:
                r = client.get(
                    "https://hn.algolia.com/api/v1/search",
                    params={
                        "query": keyword,
                        "tags": "story",
                        "numericFilters": f"created_at_i>{int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())}",
                        "hitsPerPage": 5,
                    }
                )
                if r.status_code == 200:
                    for hit in r.json().get("hits", []):
                        title = hit.get("title", "")
                        url = hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                        if title:
                            items.append(Item(
                                title=title,
                                url=url,
                                source="HackerNews",
                                summary=f"HN points: {hit.get('points', 0)}, comments: {hit.get('num_comments', 0)}",
                            ))
    except Exception:
        pass
    return items[:max_items]


def fetch_github_trending(max_items: int = 10) -> list[Item]:
    """Fetch trending GitHub repos for platform engineering topics."""
    items = []
    try:
        with httpx.Client(timeout=15) as client:
            for topic in GITHUB_TOPICS[:4]:
                r = client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": f"topic:{topic} pushed:>2024-01-01",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 3,
                    },
                    headers={"Accept": "application/vnd.github+json"},
                )
                if r.status_code == 200:
                    for repo in r.json().get("items", []):
                        items.append(Item(
                            title=repo.get("full_name", ""),
                            url=repo.get("html_url", ""),
                            source="GitHub Trending",
                            summary=repo.get("description", "")[:300],
                        ))
    except Exception:
        pass
    return items[:max_items]


def gather_all() -> list[Item]:
    """Gather items from all sources."""
    items = []
    items.extend(fetch_feeds())
    items.extend(fetch_hackernews())
    items.extend(fetch_github_trending())
    return items