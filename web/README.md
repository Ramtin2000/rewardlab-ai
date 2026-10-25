# RewardLab web

Next.js + TypeScript + Tailwind + shadcn/ui + Recharts.

```bash
npm install
npm run dev          # http://localhost:3000, mock fixtures
```

To use the live backend, start the API from `backend/` (`uvicorn rewardlab.api.app:app --reload`) and set `REWARDLAB_API_URL=http://localhost:8000` in `web/.env.local`.

## Where things live

| Path | What |
|---|---|
| `src/lib/types.ts` | The data contract. Mirrors `backend/rewardlab/schemas.py`. |
| `src/lib/data.ts` | The only data access layer: fixtures or API, chosen by `REWARDLAB_API_URL`. |
| `src/lib/fixtures.ts` | Mock runs, trajectories and a scripted playground. |
| `src/app/` | Pages: overview, experiments, trajectories, playground. |
| `src/components/` | Shared UI: metric chart, trajectory timeline, status badges. |

Run colors (`--run-*` in `globals.css`) are validated for color-blind safety in light and dark. Color always means "which run"; status colors are reserved for verifier/hack state and always come with an icon and label.
