#!/usr/bin/env python3
"""CLI:  python cli.py --repo target_repo --bug-file examples/bug_report.txt [--auto-approve]"""
import argparse
import sys
from pathlib import Path

from agent.llm import ClaudeLLM, LLMError
from agent.orchestrator import Orchestrator


def main() -> int:
    ap = argparse.ArgumentParser(description="Autonomous bug-fixing agent")
    ap.add_argument("--repo", required=True, help="path to the source code repository")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--bug", help="bug description text")
    g.add_argument("--bug-file", help="file containing the bug description")
    ap.add_argument("--error-log", help="file with error log / stack trace (optional; failing tests are auto-captured)")
    ap.add_argument("--out", default="agent_runs", help="where run artifacts are written")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--sandbox", choices=["subprocess", "docker"], default="subprocess")
    ap.add_argument("--docker-image", default="rdd-agent-sandbox")
    ap.add_argument("--model", help="Claude model (default: $AGENT_MODEL or claude-sonnet-5)")
    ap.add_argument("--auto-approve", action="store_true", help="apply validated patch without asking")
    a = ap.parse_args()

    bug = a.bug or Path(a.bug_file).read_text()
    log = Path(a.error_log).read_text() if a.error_log else None
    try:
        llm = ClaudeLLM(a.model)
    except LLMError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    result = Orchestrator(a.repo, llm, a.out, a.max_attempts, a.sandbox, docker_image=a.docker_image,
                          auto_approve=a.auto_approve).run(bug, log)
    print(f"\n{'SUCCESS' if result.success else 'FAILED'} | attempts={result.attempts} | "
          f"integrated={result.integrated} | artifacts: {result.run_dir}")
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
