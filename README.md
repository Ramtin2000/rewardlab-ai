# RewardLab

A small lab for studying **reward hacking** in tool-using LLM agents.

One agent resolves customer-support tickets over multiple turns using 5 tools. We train it with reinforcement fine-tuning (GRPO) against different reward functions, and an independent verifier measures whether the task was actually done. A web UI shows experiments, trajectories and a playground.

## Setup

**Backend (environment, training, API)**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt -e .
pytest
```

API keys go in the repo-root `.env` (copy `.env.example`).

**Web UI**

```bash
cd web
npm install
npm run dev            # http://localhost:3000 on mock data
```

**Connect the UI to the backend**

```bash
cd backend && uvicorn rewardlab.api.app:app --reload           # port 8000
echo "REWARDLAB_API_URL=http://localhost:8000" > web/.env.local  # then restart npm run dev
```

## Layout

```
backend/    Python: environment, agent, rewards, training, API (see backend/README.md)
web/        Next.js UI (see web/README.md)
runs/       trajectories, checkpoints, plots, shared by both (gitignored)
prd/        private notes (gitignored)
```

Results the API reads: `runs/<run_id>/run.json` and `runs/<run_id>/trajectories.jsonl`, in the shapes defined in `backend/rewardlab/schemas.py`.
