# AI Analytics Studio

A locally-runnable AI-powered analytics tool. Upload datasets, ask questions
in natural language, and get real, computed (not hallucinated) insights,
interactive visualizations, and downloadable PDF reports.

## Status

🚧 Under active development. Current milestone: project scaffolding.

## Architecture (high level)

- **Backend**: FastAPI (Python), SQLite (local-first), LangGraph for agent
  orchestration, sandboxed code execution for grounded analysis.
- **Frontend**: (separate — not included in this scaffold).

## Running locally (backend)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/health` to confirm it's running, and
`http://localhost:8000/docs` for the interactive API docs.

## Project structure

```
backend/
├── app/
│   ├── api/v1/       # route definitions (thin — no business logic here)
│   ├── core/         # config, settings
│   ├── models/       # SQLAlchemy DB models
│   ├── schemas/      # Pydantic request/response contracts
│   ├── services/     # business logic
│   ├── agents/       # AI agents (planner, analyst, visualizer...)
│   ├── sandbox/       # isolated code execution
│   ├── db/            # DB session setup
│   └── main.py         # app entrypoint
├── storage/             # local file storage (gitignored)
└── tests/
```
