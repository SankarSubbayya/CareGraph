# Neo4j credentials via GitHub

The app reads **`NEO4J_*` environment variables** only. It does not fetch secrets from GitHub at runtime; you configure them where your environment supports it.

## Why not commit secrets?

Secrets must not be committed. Configure them in GitHub (Actions / Codespaces) or export them locally — the app does not read a `.env` file.

## GitHub Actions (CI)

1. Open the repository on GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. Under **Repository secrets**, add:

| Name | Required | Description |
|------|----------|-------------|
| `NEO4J_URI` | Yes | e.g. `neo4j+s://xxxx.databases.neo4j.io` |
| `NEO4J_USERNAME` | Yes | Aura / DB user |
| `NEO4J_PASSWORD` | Yes | Password |
| `NEO4J_DATABASE` | If not default | Often `neo4j` or your Aura database name |

3. The workflow **Neo4j smoke test** (`.github/workflows/neo4j-smoke.yml`) maps each secret to a **same-named environment variable** on the job (`env:`). The Python app reads those variables via `app.config.Settings` — there is no GitHub API call at runtime.

4. Optional secrets `AURA_INSTANCEID` and `AURA_INSTANCENAME` are passed through in CI if you add them; the graph driver does not require them.

If secrets are missing, the job skips the DB check with a notice (does not fail).

**Fork PRs:** GitHub does not expose repository secrets to workflows from forks, so the smoke test will skip there.

## GitHub Codespaces (optional)

1. **Settings** → **Secrets and variables** → **Codespaces**.
2. Add the same variable names as above.

Codespaces injects them as environment variables in the dev container.

## Local development (outside Codespaces)

`export` the same variable names in your shell before `uv run`, or set them in your IDE’s run/debug configuration. GitHub does not expose repository secret values to a normal clone on your machine.

Optional keys used elsewhere in the app (also env-only): `BLAND_API_KEY`, `ROCKETRIDE_URI`, `ROCKETRIDE_APIKEY`, `GMI_API_KEY`, `GMI_MODEL`.
