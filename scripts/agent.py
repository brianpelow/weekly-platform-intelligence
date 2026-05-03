"""Weekly Platform Intelligence agent -- runs every Monday."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent


def run() -> None:
    from wpi.sources import gather_all
    from wpi.brief import score_items, generate_brief
    from wpi.publisher import get_issue_number, publish_discussion

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    today = date.today()

    print(f"[agent] Weekly Platform Intelligence - {today.isoformat()}")
    print(f"[agent] AI: {'enabled' if api_key else 'template mode'}")

    print("[agent] Gathering sources...")
    items = gather_all()
    print(f"[agent] Gathered {len(items)} items")

    print("[agent] Scoring for relevance...")
    scored = score_items(items, api_key)
    top = [i for i in scored if i.relevance > 0.2][:12]
    print(f"[agent] {len(top)} relevant items selected")

    issue_number = get_issue_number(github_token) if github_token else 1

    print(f"[agent] Generating Issue #{issue_number}...")
    brief = generate_brief(scored, api_key, issue_number)

    out_dir = REPO_ROOT / "archive"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{today.isoformat()}-issue-{issue_number:03d}.md"
    out_file.write_text(brief)
    print(f"[agent] Saved to {out_file}")

    if github_token:
        print("[agent] Publishing to GitHub Discussions...")
        published = publish_discussion(brief, issue_number, github_token)
        if not published:
            print("[agent] Discussion publish failed - brief saved to archive")
    else:
        print("[agent] No GITHUB_TOKEN - skipping discussion publish")

    print("[agent] Done.")
    print("\n--- BRIEF PREVIEW ---")
    print(brief[:500] + "..." if len(brief) > 500 else brief)


if __name__ == "__main__":
    run()