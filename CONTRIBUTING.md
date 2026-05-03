# Contributing

## Development setup

```bash
git clone https://github.com/brianpelow/weekly-platform-intelligence
cd weekly-platform-intelligence
uv sync
uv run pytest
```

## Running the agent locally

```bash
export OPENROUTER_API_KEY=your_key
uv run python scripts/agent.py
```