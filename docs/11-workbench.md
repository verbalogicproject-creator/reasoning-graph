# Local Workbench

The workbench is a local FastAPI inspection surface for one declared instance.
It is a maintainer tool, not a hosted product and not a general GraphRAG UI.

## Run

```sh
pip install -e '.[workbench]'
npm install
npm run build
reasoning-graph-workbench --instance instances/claude_code_tools/instance.json
```

It binds only to `127.0.0.1:8765`. Open that local address in a browser.

## What it shows

- graph integrity and database hash;
- deterministic resolve output, including the returned path and per-edge provenance;
- frontier-call-log entries and frontier metrics;
- staged candidate files;
- an append-only observation ledger.

The path renderer displays returned graph relationships only. It deliberately
does not expose model chain-of-thought or present confidence as probability.
The bundled static assets use Primer CSS for the local developer-tool baseline
and Cytoscape.js for returned-path layout; neither is loaded from a CDN.

## Lifecycle guard
Every POST endpoint requires `application/json`, a per-process CSRF token,
a loopback `Host`, and a same-origin `Origin` when the browser supplies one.
The bundled UI obtains the token from `GET /api/session` and sends it in the
`X-CSRF-Token` header. Cross-origin and simple form-style requests fail before
they can mutate a ledger or graph.

Typed confirmation establishes an explicit action in this local operator UI;
it is not authenticated human identity. Do not expose the workbench as a service.


`POST /api/actions/freeze` and `POST /api/actions/retire` fail unless the JSON
body contains the literal boolean `"approve": true`. Freeze also requires the
exact typed confirmation `FREEZE <filename>` and accepts only an existing `.md`
filename directly inside the instance's declared `staged_dir`; absolute paths
and traversal are rejected. Retire additionally requires the exact typed
confirmation `RETIRE RULES`. Ordinary inspection, candidate verification, and
UI navigation cannot infer approval; callers must send every explicit value.

Observation writes only append JSONL and never open the graph database for
writing. Freeze/retire retain the engine's transaction and provenance controls.

## API summary

- `GET /api/session` (per-process CSRF bootstrap; never persist the token)
- `GET /api/overview`, `/api/integrity`, `/api/gaps`, `/api/frontier`, `/api/candidates`
- `GET /api/resolve?text=...` or `?start=...&end=...`
- `GET|POST /api/observations`
- `POST /api/actions/freeze` and `/api/actions/retire` (explicit human gate)
- `POST /api/actions/verify` (read-only staged-candidate verification)

Run `pytest -q tests/test_workbench.py` for the local contract checks.
