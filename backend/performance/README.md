# Performance tests (k6)

This folder contains load tests for the backend API.

## Files

- `k6/quiz_flow_load.js`:
  login + start quiz + get question + submit answer + end quiz.
- `k6/read_api_load.js`:
  login + read endpoints (`/users/me`, history, questions library, leaderboard).

## Requirements

1. Backend must be running on port `8000`.
2. A test user must exist in the database.
3. Set environment variables:
   - `PERF_EMAIL`
   - `PERF_PASSWORD`

## Quick smoke test (PowerShell)

```powershell
docker run --rm -i `
  -v "D:/quiz-llm-app/backend/performance/k6:/scripts" `
  grafana/k6 run `
  -e BASE_URL=http://host.docker.internal:8000 `
  -e PERF_EMAIL=your_user_email `
  -e PERF_PASSWORD=your_user_password `
  --vus 1 --iterations 1 `
  /scripts/quiz_flow_load.js
```

## Read endpoints load test (PowerShell)

```powershell
docker run --rm -i `
  -v "D:/quiz-llm-app/backend/performance/k6:/scripts" `
  grafana/k6 run `
  -e BASE_URL=http://host.docker.internal:8000 `
  -e PERF_EMAIL=your_user_email `
  -e PERF_PASSWORD=your_user_password `
  -e VUS=8 `
  -e DURATION=2m `
  /scripts/read_api_load.js
```

## Quiz flow load test (PowerShell)

```powershell
docker run --rm -i `
  -v "D:/quiz-llm-app/backend/performance/k6:/scripts" `
  grafana/k6 run `
  -e BASE_URL=http://host.docker.internal:8000 `
  -e PERF_EMAIL=your_user_email `
  -e PERF_PASSWORD=your_user_password `
  -e VUS=2 `
  -e DURATION=1m `
  -e QUIZ_QUESTIONS=2 `
  -e QUIZ_DIFFICULTY=medium `
  -e QUIZ_ADAPTIVE=true `
  /scripts/quiz_flow_load.js
```

## Optional: run inside docker compose network

If you want to call backend by service name (`http://backend:8000`), attach k6 container to compose network:

```powershell
docker run --rm -i `
  --network quiz-llm-app_quiz_network `
  -v "D:/quiz-llm-app/backend/performance/k6:/scripts" `
  grafana/k6 run `
  -e BASE_URL=http://backend:8000 `
  -e PERF_EMAIL=your_user_email `
  -e PERF_PASSWORD=your_user_password `
  /scripts/read_api_load.js
```
