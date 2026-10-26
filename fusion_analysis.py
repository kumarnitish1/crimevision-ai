
import json
from pathlib import Path
from datetime import datetime, timezone


VIDEO_FILE = Path("timeline.json")
IMAGE_FILE = Path("image_results.txt")
AUDIO_FILE = Path("audio_results.txt")
OUTPUT_FILE = Path("fusion_report.json")


def load_json(path):
    """Load a JSON file and return its contents."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_text_evidence(path, source):
    """Load optional text results from image or audio analysis."""
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8").strip()

    if not text:
        return None

    return {
        "source": source,
        "text": text,
        "timestamp_seconds": None,
        "verification_status": "unverified"
    }


def fuse_evidence():
    if not VIDEO_FILE.exists():
        raise FileNotFoundError(
            "timeline.json is missing. Run timeline_builder.py first."
        )

    video_data = load_json(VIDEO_FILE)

    findings = []
    unified_timeline = []

    # Include video findings with their timestamps.
    for event in video_data.get("timeline", []):
        if event.get("analysis_status") != "completed":
            continue

        finding = {
            "source": "video",
            "timestamp_seconds": event.get("timestamp_seconds"),
            "observation": event.get("event"),
            "people": event.get("people", []),
            "objects": event.get("objects", []),
            "uncertainty": event.get("uncertainty"),
            "verification_status": "single_source_observation"
        }

        findings.append(finding)
        unified_timeline.append({
            "timestamp_seconds": event.get("timestamp_seconds"),
            "source": "video",
            "observation": event.get("event"),
            "verification_status": "single_source_observation"
        })

    # Add image analysis, if a saved result is available.
    image_evidence = load_text_evidence(IMAGE_FILE, "image")
    if image_evidence:
        findings.append(image_evidence)
        unified_timeline.append({
            "timestamp_seconds": None,
            "source": "image",
            "observation": image_evidence["text"],
            "verification_status": "unverified",
            "note": "No timestamp supplied by the image analysis."
        })

    # Add audio analysis, if a saved result is available.
    audio_evidence = load_text_evidence(AUDIO_FILE, "audio")
    if audio_evidence:
        findings.append(audio_evidence)
        unified_timeline.append({
            "timestamp_seconds": None,
            "source": "audio",
            "observation": audio_evidence["text"],
            "verification_status": "unverified",
            "note": "No timestamp supplied by the audio analysis."
        })

    # Sort timestamped events first. Untimed evidence follows them.
    unified_timeline.sort(
        key=lambda item: (
            item["timestamp_seconds"] is None,
            item["timestamp_seconds"]
            if item["timestamp_seconds"] is not None
            else 0
        )
    )

    video_classification = video_data.get("classification", {})

    report = {
        "project": "CrimeVision AI",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "video": video_data.get("video", "unknown"),
        "duration_seconds": video_data.get("duration_seconds"),
        "evidence_sources": {
            "video": "loaded" if VIDEO_FILE.exists() else "missing",
            "image": "loaded" if image_evidence else "not supplied",
            "audio": "loaded" if audio_evidence else "not supplied"
        },
        "unified_timeline": unified_timeline,
        "findings": findings,
        "video_classification": video_classification,
        "cross_modal_validation": {
            "status": "not_performed",
            "corroborated_findings": [],
            "conflicts": [],
            "note": (
                "Combining sources does not automatically establish "
                "corroboration. Cross-modal matching requires explicit "
                "comparison of entities, timestamps, and source reliability."
            )
        },
        "limitations": [
            "Video observations describe sampled frames, not every moment.",
            "Image and audio results have no timestamps unless supplied.",
            "A model-generated classification is not proof that a crime occurred.",
            "Missing evidence must not be treated as evidence of absence."
        ]
    }

    OUTPUT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return report


if __name__ == "__main__":
    try:
        result = fuse_evidence()

        print("=== CRIMEVISION AI: EVIDENCE FUSION ===")
        print("Video:", result["video"])
        print("Timeline events:", len(result["unified_timeline"]))
        print("Evidence sources:", result["evidence_sources"])
        print(
            "Video classification status:",
            result["video_classification"].get("status", "unknown")
        )
        print("Cross-modal validation: not performed")
        print("Saved report:", OUTPUT_FILE)

    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        print("Fusion failed:", error)
