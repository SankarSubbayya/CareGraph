# Public Demo Deployment

This project can be shared as a public demo without doing a full production hardening pass.

## Recommended setup

- Host the app on Render using `render.yaml`
- Use Neo4j Aura for the database
- Configure RocketRide, Bland AI, and GMI through environment variables
- Set `BASE_URL` to the final public URL
- Seed demo data after the first deploy

## Minimum environment variables

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `BASE_URL`

Optional but recommended for the full demo:

- `ROCKETRIDE_URI`
- `ROCKETRIDE_APIKEY`
- `BLAND_API_KEY`
- `GMI_API_KEY`

## Optional demo protection

If you want to keep the demo public but avoid anonymous writes and call triggers, set:

- `DEMO_USERNAME`
- `DEMO_PASSWORD`

When both are set, the app uses browser basic auth for all routes except:

- `/`
- `/dashboard`
- `/health`
- `/static/*`
- `/api/voice/webhook`

This lets webhook callbacks keep working while protecting the interactive API and dashboard data operations.

## Render deploy flow

1. Push the repo to GitHub.
2. Create a new Render Blueprint or Web Service from the repo.
3. Add the required environment variables.
4. Set `BASE_URL` to the Render URL after the first deploy.
5. Seed demo data.
6. If desired, attach a custom domain like `caregraph.app`.

## Health check

The app exposes `GET /health` for platform health checks.
