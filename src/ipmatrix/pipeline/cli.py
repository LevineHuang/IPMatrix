import argparse
import json
from datetime import date
from pathlib import Path

from ipmatrix.pipeline.analysis import analyze_run_dry
from ipmatrix.pipeline.config import load_topic_config
from ipmatrix.pipeline.discovery import ArxivClient, discover_candidates
from ipmatrix.pipeline.publishing import publish_run_dry
from ipmatrix.pipeline.review import review_run
from ipmatrix.pipeline.selection import build_selection_html
from ipmatrix.pipeline.storage import PipelineStorage


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    scan = subcommands.add_parser("scan", help="Create a run and fetch arXiv candidates.")
    scan.add_argument("topic_id")
    scan.add_argument("--from-file", help="Use saved arXiv Atom XML instead of network fetch.")
    scan.add_argument("--today", help="Override run date in YYYY-MM-DD format.")

    select = subcommands.add_parser("select", help="Build local HTML selection page.")
    select.add_argument("topic_id")
    select.add_argument("run_id")

    analyze = subcommands.add_parser("analyze", help="Generate dry-run Markdown artifacts.")
    analyze.add_argument("topic_id")
    analyze.add_argument("run_id")

    review = subcommands.add_parser("review", help="Mark dry-run artifacts as reviewed.")
    review.add_argument("topic_id")
    review.add_argument("run_id")

    publish = subcommands.add_parser("publish", help="Write dry-run WeChat publish result.")
    publish.add_argument("topic_id")
    publish.add_argument("run_id")

    status = subcommands.add_parser("status", help="Show run status.")
    status.add_argument("topic_id")
    status.add_argument("run_id")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    storage = PipelineStorage(root)

    if args.command == "scan":
        topic = load_topic_config(root, args.topic_id)
        run_date = date.fromisoformat(args.today) if args.today else date.today()
        run = storage.create_run(topic, today=run_date)
        atom_text = Path(args.from_file).read_text(encoding="utf-8") if args.from_file else ArxivClient().fetch(topic)
        candidates = discover_candidates(topic, atom_text, today=run_date, limit=topic.max_candidates)
        storage.write_stage(topic.id, run["id"], "candidates", candidates)
        storage.update_run_status(topic.id, run["id"], "candidates_ready")
        print(json.dumps({"run_id": run["id"], "candidates": len(candidates)}, ensure_ascii=False))
        return 0

    if args.command == "select":
        candidates = storage.read_stage(args.topic_id, args.run_id, "candidates")
        output = storage.run_dir(args.topic_id, args.run_id) / "selection.html"
        build_selection_html(args.topic_id, args.run_id, candidates, output)
        if not (storage.run_dir(args.topic_id, args.run_id) / "selection.json").exists():
            selection = {
                "topic_id": args.topic_id,
                "run_id": args.run_id,
                "selected_paper_ids": [candidate["paper_id"] for candidate in candidates],
                "excluded_paper_ids": [],
                "generated_by": "cli-default-select-all",
            }
            storage.write_stage(args.topic_id, args.run_id, "selection", selection)
        storage.update_run_status(args.topic_id, args.run_id, "selected")
        print(json.dumps({"selection_page": str(output)}, ensure_ascii=False))
        return 0

    if args.command == "analyze":
        topic = load_topic_config(root, args.topic_id)
        result = analyze_run_dry(root, storage, topic, args.run_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "review":
        result = review_run(storage, args.topic_id, args.run_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "publish":
        result = publish_run_dry(root, storage, args.topic_id, args.run_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "status":
        result = storage.read_stage(args.topic_id, args.run_id, "run")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
