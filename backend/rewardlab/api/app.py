"""HTTP API for the web UI.

Run with (from backend/):  uvicorn rewardlab.api.app:app --reload
Then set REWARDLAB_API_URL=http://localhost:8000 in web/.env.local.

Reads results from the runs directory, one folder per run:
    runs/<run_id>/run.json             -> Run
    runs/<run_id>/trajectories.jsonl   -> one Trajectory per line
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError

from rewardlab.api import playground
from rewardlab.paths import RUNS_DIR
from rewardlab.rewards.score import score
from rewardlab.schemas import PlaygroundModel, PlaygroundRequest, Run, Trajectory, TrajectorySummary

app = FastAPI(title="RewardLab API")


def _runs() -> list[Run]:
    return [Run.model_validate_json(p.read_text()) for p in sorted(RUNS_DIR.glob("*/run.json"))]


def _trajectories() -> list[Trajectory]:
    out = []
    for path in sorted(RUNS_DIR.glob("*/trajectories.jsonl")):
        out += [Trajectory.model_validate_json(line) for line in path.read_text().splitlines() if line.strip()]
    return out


@app.get("/health")
def health() -> dict:
    return {"ok": True, "runs_dir": str(RUNS_DIR)}


@app.get("/runs")
def list_runs() -> list[Run]:
    return _runs()


@app.get("/trajectories")
def list_trajectories(
    run_id: str | None = None,
    scenario: str | None = None,
    verifier: str | None = None,  # "passed" | "failed"
    hack: bool | None = None,
) -> list[TrajectorySummary]:
    rows = _trajectories()
    if run_id:
        rows = [t for t in rows if t.run_id == run_id]
    if scenario:
        rows = [t for t in rows if t.scenario == scenario]
    if verifier:
        rows = [t for t in rows if t.verifier and t.verifier.passed == (verifier == "passed")]
    if hack is not None:
        rows = [t for t in rows if t.is_hack == hack]
    return [TrajectorySummary.of(t) for t in rows]


@app.get("/trajectories/{episode_id}")
def get_trajectory(episode_id: str) -> Trajectory:
    for t in _trajectories():
        if t.episode_id == episode_id:
            return t
    raise HTTPException(404, f"trajectory {episode_id} not found")


@app.get("/playground/models")
def playground_models() -> list[PlaygroundModel]:
    return playground.models()


@app.post("/playground/run")
def playground_run(req: PlaygroundRequest) -> Trajectory:
    try:
        return score(playground.run_episode(req))
    except KeyError:
        raise HTTPException(400, f"unknown model {req.model}")
    except APIConnectionError:
        raise HTTPException(503, "Could not reach the model server. Is Ollama running?")
