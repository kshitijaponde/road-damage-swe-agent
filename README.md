# Autonomous Software Engineer Agent - Road Damage Detection edition

An AI system that acts as an autonomous software engineer: it understands a codebase, fixes bugs, validates
its own fixes in a sandbox with targeted and regression tests, and safely integrates approved changes.

The codebase it works on (`target_repo/`) is the **Road Damage Detection and Severity Assessment** system
(RDD2022 India subset): detects potholes, longitudinal / transverse / alligator cracks with bounding boxes
and grades each Low / Medium / High. Two realistic bugs are seeded in it for the agent to find and fix.

## Layout

```
agent/            the agent system (LLM layer, repo ingest, patcher, sandbox, agents, orchestrator, report)
target_repo/      road damage system: dataset conversion, YOLO detector, severity, pipeline, tests
  road_damage/    classes.py dataset.py severity.py detector.py pipeline.py
  train.py predict.py   real training / inference entry points (need `pip install ultralytics pillow`)
examples/         bug reports
agent_tests/      tests for the agent itself (scripted LLM, no API key needed)
docs/             architecture + workflow diagrams (Mermaid) and requirement traceability
cli.py demo.py    entry points
```

## Quick start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python demo.py                      # copies target_repo to workspace/, agent fixes both bugs and commits on a branch
```

Own repo:

```bash
python cli.py --repo path/to/repo --bug-file bug.txt [--error-log trace.txt] [--auto-approve]
              [--sandbox docker] [--max-attempts 3] [--model claude-sonnet-5]
```

Outputs land in `agent_runs/run_<timestamp>/`: `report.md` (full debugging journey), `fix.patch`,
`commit_message.txt`, `PR_DESCRIPTION.md`, `trace.json`.

Verify the agent machinery without an API key: `python -m pytest agent_tests -q`

## The seeded bugs

1. `road_damage/dataset.py::voc_to_yolo` normalises the y-centre by image **width** instead of height (only visible on non-square images).
2. `road_damage/severity.py::_area_ratio` multiplies width by width instead of width by height, so tall narrow potholes are under-graded.

`cd target_repo && python -m pytest` shows 2 failures / 13 passes before the fix.

## Safety design

- Fixes run in a throw-away copy of the repo; the real repo is only touched after validation and approval.
- The sandbox environment is scrubbed (API keys are not passed to the code under test), with a timeout.
  Subprocess mode is isolation from side effects, not a security boundary; use `--sandbox docker` (`Dockerfile.sandbox`, `--network none`) for untrusted code.
- The agent cannot edit existing tests (they are the specification); it may only add new regression tests.
- Edits must match exactly once; paths cannot escape the repo.
- A fix is accepted only if the previously failing tests pass AND every test that passed before still passes.
- Integration requires reviewer approval plus human confirmation (or `--auto-approve`), refuses a dirty git tree, and commits on a new `agent/fix-*` branch.

## Running the road damage system itself

```bash
cd target_repo && pip install -r requirements.txt
python train.py --rdd-root /path/to/RDD2022/India --epochs 50
python predict.py some_road.jpg          # JSON with type, box, severity + annotated image in predictions/
```

Severity is rule-based (box area ratio for potholes and alligator cracks; extent across the frame for linear cracks); thresholds are in `severity.py` and should be calibrated on real data.
