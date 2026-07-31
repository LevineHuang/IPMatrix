from ipmatrix.pipeline.storage import PipelineStorage


def review_run(storage: PipelineStorage, topic_id: str, run_id: str) -> dict:
    analysis = storage.read_stage(topic_id, run_id, "analysis")
    review = {
        "topic_id": topic_id,
        "run_id": run_id,
        "status": "reviewed",
        "dry_run": True,
        "artifact_ids": analysis.get("artifact_ids", []),
        "checks": [
            {
                "name": "dry-run-review",
                "status": "passed",
                "note": "MVP only marks generated artifacts as reviewed after local inspection gate.",
            }
        ],
    }
    storage.write_stage(topic_id, run_id, "review", review)
    storage.update_run_status(topic_id, run_id, "reviewed")
    return review
