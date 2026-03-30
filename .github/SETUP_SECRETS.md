# Neo4j credentials via GitHub

The app reads **`NEO4J_*` environment variables** only. It does not fetch secrets from GitHub at runtime; you configure them where your environment supports it.

## Why not a shared `.env` in the repo?

Secrets must not be committed. Use one of the options below.

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

Codespaces injects them as environment variables in the dev container, so contributors do not need a local `.env` file when working in the browser.

## Local development

Set variables in your shell, use a **gitignored** `.env` file (copy from `.env.example`), or use your OS keychain / secret manager. GitHub does not expose repository secret values to clone checkouts on your machine.
