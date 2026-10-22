
import json
from pathlib import Path


def build_timeline(results_path="frame_results.json"):
    path = Path(results_path)

    if not path.exists():
        raise FileNotFoundError(
            f"{results_path} not found. Run video_analysis.py first."
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    timeline = []

    for frame in data.get("frames", []):
        timeline.append({
            "timestamp_seconds": frame["timestamp_seconds"],
            "frame_path": frame["frame_path"],
            "event": "Not analyzed yet",
            "analysis_status": "pending"
        })

    return {
        "video": data.get("video", "unknown"),
        "duration_seconds": data.get("duration_seconds"),
        "timeline": timeline,
        "crime_type": "Not classified",
        "classification_status": "pending",
        "note": (
            "Events and crime classification require successful "
            "AI analysis. No crime is inferred from missing data."
        )
    }


if __name__ == "__main__":
    result = build_timeline()

    with open("timeline.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print(json.dumps(result, indent=2))
    print("\nSaved timeline.json")
