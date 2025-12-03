import argparse
import json
import os

from .repo_parser import parse_project
from .env_manager import plan_environment
from .runner import build_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--output", default="report.json")
    args = parser.parse_args()
    root = os.path.abspath(args.path)
    spec, result = parse_project(root)
    plan = plan_environment(spec)
    run = build_run(spec, plan)
    out = {
        "project": spec.__dict__,
        "parse": {
            "files_found": result.files_found,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
        },
        "plan": plan.__dict__,
        "run": run,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(args.output)


if __name__ == "__main__":
    main()

