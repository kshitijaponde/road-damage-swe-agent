#!/usr/bin/env python3
"""One-command demo: copy the buggy road-damage repo into a fresh git repo and let the agent fix it."""
import shutil
import subprocess
import sys
from pathlib import Path

from agent.llm import ClaudeLLM, LLMError
from agent.orchestrator import Orchestrator

HERE = Path(__file__).parent
WORK = HERE / "workspace" / "road_damage"


def sh(*cmd):
    subprocess.run(cmd, cwd=WORK, check=True, capture_output=True)


if __name__ == "__main__":
    shutil.rmtree(WORK.parent, ignore_errors=True)
    shutil.copytree(HERE / "target_repo", WORK, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    sh("git", "init", "-q")
    sh("git", "config", "user.email", "agent@example.com")
    sh("git", "config", "user.name", "SWE Agent")
    sh("git", "add", "-A")
    sh("git", "commit", "-q", "-m", "Initial road damage detection system (with bugs)")
    try:
        llm = ClaudeLLM()
    except LLMError as e:
        sys.exit(f"error: {e}")
    bug = (HERE / "examples" / "bug_report.txt").read_text()
    r = Orchestrator(WORK, llm, HERE / "agent_runs", auto_approve=True).run(bug)
    print(f"\nResult: success={r.success} integrated={r.integrated}\nReport: {r.run_dir / 'report.md'}")
