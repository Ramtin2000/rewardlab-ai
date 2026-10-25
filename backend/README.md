# RewardLab backend

The Python side: the simulated support environment, agent, rewards, training, and the API the web UI reads from.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt -e .   # exact versions (recommended)
# or: pip install -e ".[dev,api,tracing]"
pytest
uvicorn rewardlab.api.app:app --reload   # http://localhost:8000
```

**Local model (needed from Phase 2 on).** Install Ollama, keep the app running, then from the repo root:

```bash
ollama pull qwen3:4b-instruct
ollama create rewardlab-qwen3-4b -f backend/ollama/Modelfile   # caps context at 8k so it fits in RAM
```

**Run episodes** (writes `../runs/<run-id>/trajectories.jsonl`):

```bash
python -m rewardlab.agent.run --run-id baseline-qwen3-4b --episodes 20
```

| Path | What |
|---|---|
| `rewardlab/env/` | `SupportEnv` state machine, world generation, the 5 tools |
| `rewardlab/agent/` | Agent loop (`loop.py`), system prompt, tool schemas, model client + Langfuse (`llm.py`), batch runner (`run.py`) |
| `rewardlab/rewards/` | Reward functions and the independent verifier |
| `rewardlab/eval/` | Fixed eval seeds and metrics |
| `rewardlab/train/` | GRPO training |
| `rewardlab/api/` | FastAPI app: serves `runs/` and the playground |
| `rewardlab/schemas.py` | Trajectory/run data shapes. Mirrors `../web/src/lib/types.ts` |
| `rewardlab/trajectory.py` | Turns env steps into logged `Turn`s |
| `tests/` | Pytest suite |

Core deps: the OpenAI SDK (also talks to Ollama) and python-dotenv. Extras: `dev` (tests), `api` (FastAPI), `tracing` (Langfuse, optional). Change dependencies in `pyproject.toml`, then regenerate `requirements.lock.txt` (instructions at its top).

The API reads results from the repo-root `runs/` folder (override with `REWARDLAB_RUNS_DIR`).
