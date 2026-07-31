import json
from pathlib import Path

from ipmatrix.pipeline.storage import PipelineStorage


def publish_run_dry(project_root: Path, storage: PipelineStorage, topic_id: str, run_id: str) -> dict:
    review = storage.read_stage(topic_id, run_id, "review")
    if review.get("status") != "reviewed":
        raise ValueError("Only reviewed artifacts can be published")

    result = {
        "topic_id": topic_id,
        "run_id": run_id,
        "status": "sent_to_wechat",
        "target": "wechat",
        "dry_run": True,
        "artifact_ids": review.get("artifact_ids", []),
        "results": [
            {
                "artifact_id": artifact_id,
                "sent": False,
                "draft_url": "",
                "media_id": "",
                "message": "dry-run: no request was sent to WeChat",
            }
            for artifact_id in review.get("artifact_ids", [])
        ],
    }
    output_path = project_root / "outputs" / "wechat" / topic_id / run_id / "publish-results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    storage.write_stage(topic_id, run_id, "publish", result)
    storage.update_run_status(topic_id, run_id, "sent_to_wechat")
    return result
