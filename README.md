# reasoning-graph instance 0

This repository is the lab and first dataset for **reasoning-graph**: an
experiment in turning recurring reasoning into typed, confidence-weighted,
inspectable graph relationships. Its supported proof today is intentionally
narrow: it can recommend Claude Code tools and workflows, traverse authored
agent-design rules, and expose when the graph has no support for an answer.

It is not a general-purpose reasoning engine or an autonomous learner. The
larger generalized engine lives separately at `/root/projects/reasoning_graph`;
this repository supplies one instance and preserves its research history.

## Five-minute verification

The supported query surface is deterministic and offline:

```sh
python3 p2_fixture_runner.py
python3 query.py --compose-for "fix a bug found via search" --json
python3 query.py --can-it "access the internet" --json
```

Run all instance repair tests with:

```sh
python3 -m unittest discover -s tests -v
```

The canonical engine consumes [`instance/instance.json`](instance/instance.json).
All descriptor paths are relative to this repository; the engine, instance data,
rules, frontier log, observations, and compatibility adapter therefore remain a
portable two-repository interface instead of depending on one machine's paths.

With `/root/projects/reasoning_graph` available locally:

```sh
PYTHONPATH=/root/projects/reasoning_graph \
  python3 -m reasoning_graph.cli schema integrity \
  --instance instance/instance.json --json
```

## Repair the instance database

`kgs/reasoning-graph.db` is immutable input to the repair. The migration creates
`data/derived/reasoning-graph.clean.db` and a reviewable JSON manifest; it never
overwrites the original.

```sh
python3 scripts/repair_instance_db.py
```

The migration recovers 21 workflow concepts from the tool source records,
normalizes workflow relationships to `workflow -> tool`, and merges three exact
typed relationship duplicates while retaining every original claim as evidence.
It validates SQLite integrity and referential integrity before publishing the
derived file.

## Data policy

- `kgs/reasoning-graph.db` is the focused source instance and may be versioned.
- `data/derived/*.db` and database backups are generated artifacts and ignored.
- `data/derived/reasoning-graph.clean.manifest.json` is the audit receipt.
- `systems/eco-system/` remains a large nested legacy checkout and is excluded
  from this repository's Git boundary; it is not part of the supported product.
- No migration deletes or rewrites the original database.

See `CODEBASE-AUDIT-2026-08-29.md` for the pre-repair health baseline.

