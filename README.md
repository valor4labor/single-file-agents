# Single File Agents (SFA)
> Premise: What if we could pack single purpose, powerful AI Agents into a single python file?

## What is this?

A collection of powerful single-file agents built on top of [uv](https://github.com/astral/uv) - the modern Python package installer and resolver. These agents demonstrate precise prompt engineering and GenAI patterns for practical tasks.

## Features

- **Self-contained**: Each agent is a single file with embedded dependencies
- **Modern Python**: Built on uv for fast, reliable dependency management
- **Run From The Cloud**: With uv, you can run these scripts from your server or right from a gist (see my gists commands)
- **Precise Agents**: Carefully crafted prompts for small agents that can do one thing really well

## Agents

### JQ Command Generator (sfa_jq_gemini_v1.py)
An AI-powered assistant that generates precise jq commands for JSON processing

Example usage:
```bash
# Generate and execute a jq command
uv run sfa_jq_gemini_v1.py --exe "Filter scores above 80 from data/mock.json and save to high_scores.json"

# Generate command only
uv run sfa_jq_gemini_v1.py "Filter scores above 80 from data/mock.json and save to high_scores.json"
```

## Requirements

- Python 3.8+
- uv package manager
- GEMINI_API_KEY

## Installation

1. Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone this repository:
```bash
git clone <repository-url>
```

3. Set your Gemini API key (for JQ generator):
```bash
export GEMINI_API_KEY='your-api-key-here'
```

## License

MIT License - feel free to use this code in your own projects.
