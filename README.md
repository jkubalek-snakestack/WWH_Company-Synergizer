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

## Repository Layout

- `src/synergizer/` – core package (models, storage, analysis, reporting, CLI).
- `data/` – sample profiles and template configuration (JSON).
- `docs/` – architectural overview and future roadmap.
- `tests/` – automated tests for the synergy engine.

## Vision

See [`docs/system_overview.md`](docs/system_overview.md) for the holistic platform concept, including UI recommendations and AI augmentation pathways.
