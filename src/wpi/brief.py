"""Brief generator — filters, scores, and synthesizes items into a weekly executive brief."""

from __future__ import annotations

import os
from datetime import date
from wpi.sources import Item


PORTFOLIO_SPOTLIGHT = [
    ("orbit-platform", "Production Services Control Plane with OPA policy engine", "https://github.com/brianpelow/orbit-platform"),
    ("cab-automation", "Change Advisory Board automation for regulated financial services", "https://github.com/brianpelow/cab-automation"),
    ("mcp-compliance-grc", "SOC2/ISO27001/PCI-DSS control mapping via MCP", "https://github.com/brianpelow/mcp-compliance-grc"),
    ("IncidentPilot", "LangGraph multi-agent incident response", "https://github.com/brianpelow/IncidentPilot"),
    ("platform-maturity-model", "5-level platform maturity framework with automated evidence", "https://github.com/brianpelow/platform-maturity-model"),
    ("ai-governance-framework", "The replay imperative: AI governance for regulated industries", "https://github.com/brianpelow/ai-governance-framework"),
    ("engineering-operating-model", "Engineering org design for the agentic era", "https://github.com/brianpelow/engineering-operating-model"),
    ("platform-engineering-thesis", "Platform first: why AI winners are built on standard engineering", "https://github.com/brianpelow/platform-engineering-thesis"),
]


def score_items(items: list[Item], api_key: str) -> list[Item]:
    """Score items for relevance using LLM. Falls back to keyword scoring."""
    if api_key:
        return _llm_score(items, api_key)
    return _keyword_score(items)


def _keyword_score(items: list[Item]) -> list[Item]:
    """Simple keyword-based relevance scoring."""
    keywords = [
        "platform engineering", "agentic", "compliance", "governance",
        "regulated", "fintech", "SOX", "PCI", "OPA", "policy", "DORA",
        "AI", "LLM", "model risk", "audit", "control", "backstage",
        "developer experience", "SRE", "observability", "deployment",
    ]
    for item in items:
        text = (item.title + " " + item.summary).lower()
        score = sum(1 for kw in keywords if kw.lower() in text)
        item.relevance = score / len(keywords)
    return sorted(items, key=lambda x: x.relevance, reverse=True)


def _llm_score(items: list[Item], api_key: str) -> list[Item]:
    """Use LLM to score items for relevance."""
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        titles = "\n".join(f"{i}. {item.title} ({item.source})" for i, item in enumerate(items[:40]))
        prompt = f"""You are filtering news items for a weekly brief targeting engineering leaders in regulated financial services and manufacturing.

Score each item 0-10 for relevance to: platform engineering, agentic AI, compliance automation, AI governance, regulated industry technology, developer productivity, SRE/observability.

Items:
{titles}

Respond with ONLY a comma-separated list of scores in order, e.g.: 8,3,7,2,9,1,6,4,8,2"""

        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        scores_text = response.choices[0].message.content.strip()
        scores = [float(s.strip()) / 10 for s in scores_text.split(",")]
        for i, item in enumerate(items[:len(scores)]):
            item.relevance = scores[i]
        return sorted(items, key=lambda x: x.relevance, reverse=True)
    except Exception:
        return _keyword_score(items)


def generate_brief(items: list[Item], api_key: str, issue_number: int) -> str:
    """Generate the weekly brief markdown."""
    top_items = [i for i in items if i.relevance > 0.3][:10]
    today = date.today()
    week_num = today.isocalendar()[1]
    spotlight = PORTFOLIO_SPOTLIGHT[(issue_number - 1) % len(PORTFOLIO_SPOTLIGHT)]

    if api_key:
        return _llm_brief(top_items, api_key, issue_number, week_num, today, spotlight)
    return _template_brief(top_items, issue_number, week_num, today, spotlight)


def _llm_brief(items: list[Item], api_key: str, issue_num: int, week_num: int, today, spotlight: tuple) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        item_list = "\n".join(f"- {item.title} ({item.source}): {item.summary[:200]}" for item in items)
        prompt = f"""You are writing the Weekly Platform Intelligence brief #{ issue_num} for Week {week_num} of {today.year}.

Your audience: engineering leaders in regulated financial services and manufacturing who care about platform engineering, agentic AI, compliance automation, and AI governance.

Your voice: direct, executive, technically credible. No fluff. The lens is always: what does this mean for platform engineering in regulated industries?

Source items this week:
{item_list}

Write a brief with this exact structure:

## This Week in Platform Engineering

**Week {week_num} · {today.strftime('%B %d, %Y')} · Issue #{issue_num}**

[2-3 sentence opening that names the dominant theme of the week and why it matters for regulated industries]

### [Theme 1 headline]
[2-3 sentences on the first major theme, referencing 2-3 specific items, with implications for regulated engineering orgs]

### [Theme 2 headline]
[2-3 sentences on the second theme]

### [Theme 3 headline]
[2-3 sentences on the third theme]

### The number that matters
[One specific data point, statistic, or finding from this week worth remembering]

### From the portfolio
This week's spotlight: [{spotlight[0]}]({spotlight[2]}) — {spotlight[1]}.

---
*Weekly Platform Intelligence is published every Monday. Follow this repo to receive it. All views are Brian Pelow's own.*"""

        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception:
        return _template_brief(items, issue_num, week_num, today, spotlight)


def _template_brief(items: list[Item], issue_num: int, week_num: int, today, spotlight: tuple) -> str:
    top = items[:6]
    themes = [
        ("Platform Engineering in Motion", top[:2]),
        ("AI Governance and Compliance", top[2:4]),
        ("Agentic Systems and Developer Productivity", top[4:6]),
    ]

    lines = [
        f"## This Week in Platform Engineering",
        f"",
        f"**Week {week_num} · {today.strftime('%B %d, %Y')} · Issue #{issue_num}**",
        f"",
        f"The intersection of platform engineering, agentic AI, and regulated industry compliance continued to generate signal this week. Here is what engineering leaders need to know.",
        f"",
    ]

    for theme_title, theme_items in themes:
        lines.append(f"### {theme_title}")
        for item in theme_items:
            lines.append(f"- [{item.title}]({item.url}) ({item.source})")
        lines.append("")

    lines.extend([
        f"### From the portfolio",
        f"This week's spotlight: [{spotlight[0]}]({spotlight[2]}) -- {spotlight[1]}.",
        f"",
        f"---",
        f"*Weekly Platform Intelligence is published every Monday. Follow this repo to receive it. All views are Brian Pelow's own.*",
    ])

    return "\n".join(lines)