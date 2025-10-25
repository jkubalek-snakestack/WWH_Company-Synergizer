# WWH Company Synergizer Monorepo

This monorepo hosts the WWH Company Synergizer platform:

- **Portal** – a Next.js + Tailwind + shadcn/ui frontend served from `apps/portal`.
- **Graph Service** – a Python FastAPI microservice that wraps the synergy engine in `services/graph`.

The repository is managed with Turborepo and pnpm workspaces for JavaScript/TypeScript code while keeping the Python service isolated under its own `pyproject.toml`.

## Prerequisites

- Node.js 20+
- pnpm 8+
- Python 3.11+

## Install dependencies

```bash
pnpm install
```

This installs the portal workspace dependencies and bootstraps Turborepo tooling. Python dependencies are installed separately within `services/graph`.

## Running the Portal

```bash
pnpm dev --filter apps/portal
```

The portal is built with the Next.js App Router, Tailwind CSS, and shadcn-inspired UI primitives. The command above launches the development server on [http://localhost:3000](http://localhost:3000).

## Running the Graph Service

```bash
cd services/graph
pip install -e ".[service]"
uvicorn services.graph.main:app --reload
```

The FastAPI application exposes the `/synergy/analyze` endpoint backed by the synergy engine and template grouping helpers.

## Repository Structure

```
apps/
  portal/           # Next.js frontend (App Router + Tailwind + shadcn/ui)
services/
  graph/            # FastAPI microservice and synergy engine package
package.json        # Turborepo scripts
pnpm-workspace.yaml # Workspace definition
```

## Verification

- ✅ `pnpm dev --filter apps/portal` should start the Next.js development server.
- ✅ `uvicorn services.graph.main:app --reload` should serve the FastAPI API after installing the Python dependencies.
