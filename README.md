# WWH Company Synergizer

AI-driven synergy intelligence environment for WWH and partner companies.

## Features

- **Rich company profiling** powered by structured dataclasses capturing capabilities, needs, assets, and goals.
- **Graph-based knowledge backbone** using an in-memory directed multigraph to map plugin points and plugs across the ecosystem.
- **Opportunity discovery engine** that surfaces bilateral and triad collaboration concepts with prioritization.
- **Template & tiering system** for fast onboarding and curated cohort analysis.
- **Reporting toolkit** generating executive summaries and detailed opportunity narratives.

## Getting Started

1. Use Python 3.11 or newer in a virtual environment.
2. Run the synergy explorer against the sample dataset:
   ```bash
   python -m synergizer.cli data/sample_profiles.json --templates data/templates.json
   ```
3. Review the generated synergy report in your terminal.
4. Replace the sample data with real company profiles to tailor recommendations.

### Converting narratives into company profiles

You can transform prose descriptions of companies into structured profiles by supplying
the narrative text to the CLI alongside an OpenAI model name:

```bash
python -m synergizer.cli data/sample_profiles.json \
  --templates data/templates.json \
  --narrative notes/acme.txt \
  --openai-model gpt-4o-mini
```

Each `--narrative` flag should point to a text file containing the company story. The CLI
will call the selected model (respecting the `OPENAI_API_KEY` environment variable or the
`--openai-api-key` flag) and merge the generated profile with the rest of your dataset
before running the synergy analysis.

Install the optional LLM dependencies with:

```bash
pip install -e ".[llm]"
```

### Run the FastAPI synergy service

Expose the engine over HTTP by installing the service extras and launching the FastAPI app:

```bash
pip install -e ".[service]"
uvicorn synergizer.api:app --reload
```

Send a request with your company payloads to receive matches and opportunities:

```bash
curl -X POST http://127.0.0.1:8000/synergy/analyze \
  -H "Content-Type: application/json" \
  -d @data/sample_profiles.json
```

The JSON payload can use either a `profiles` array or the `companies` array shipped in the sample dataset. The response includes the computed opportunities, individual matches, and optional tier groupings when template bundles are supplied.

## Repository Layout

- `src/synergizer/` – core package (models, storage, analysis, reporting, CLI).
- `data/` – sample profiles and template configuration (JSON).
- `docs/` – architectural overview and future roadmap.
- `tests/` – automated tests for the synergy engine.

## Vision

See [`docs/system_overview.md`](docs/system_overview.md) for the holistic platform concept, including UI recommendations and AI augmentation pathways.
