
import json
from pathlib import Path
from datetime import datetime, timezone

VIDEO_FILE = Path("timeline.json")
IMAGE_FILE = Path("image_results.txt")
AUDIO_FILE = Path("audio_results.txt")
OUTPUT_FILE = Path("fusion_report.json")


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_text_evidence(path, source):
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


def validate_cross_modal(video_findings, image_evidence, audio_evidence):
    """
    Perform conservative checks using the evidence currently available.
    Text-only image/audio reports without timestamps or structured entities
    cannot establish reliable cross-modal corroboration.
    """
    corroborated = []
    conflicts = []
    checks = []

    sources = {
        "video": bool(video_findings),
        "image": image_evidence is not None,
        "audio": audio_evidence is not None
    }

    available_count = sum(sources.values())

    checks.append({
        "check": "source_availability",
        "sources": sources,
        "result": (
            "multiple_sources_available"
            if available_count > 1
            else "insufficient_sources_for_cross_modal_check"
        )
    })

    # Image/audio results are currently unstructured text without timestamps.
    # Avoid treating missing details as proof of a contradiction.
    checks.append({
        "check": "timestamp_alignment",
        "result": "not_possible_for_all_sources",
        "reason": (
            "Image and audio reports do not currently provide timestamps "
            "that can be reliably aligned with video events."
        )
    })

    checks.append({
        "check": "entity_matching",
        "result": "not_performed",
        "reason": (
            "Image and audio findings are not yet represented as structured "
            "people, objects, and actions for reliable entity matching."
        )
    })

    if available_count > 1:
        status = "partial_checks_only"
    else:
        status = "insufficient_evidence"

    return {
        "status": status,
        "corroborated_findings": corroborated,
        "conflicts": conflicts,
        "checks": checks,
        "note": (
            "Source availability is not corroboration. No agreement or "
            "conflict is asserted without a reliable, comparable observation."
        )
    }


def fuse_evidence():
    if not VIDEO_FILE.exists():
        raise FileNotFoundError(
            "timeline.json is missing. Run timeline_builder.py first."
        )

    video_data = load_json(VIDEO_FILE)
    findings = []
    unified_timeline = []

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

    unified_timeline.sort(
        key=lambda item: (
            item["timestamp_seconds"] is None,
            item["timestamp_seconds"]
            if item["timestamp_seconds"] is not None
            else 0
        )
    )

    video_classification = video_data.get("classification", {})
    validation = validate_cross_modal(
        [item for item in findings if item["source"] == "video"],
        image_evidence,
        audio_evidence
    )

    report = {
        "project": "CrimeVision AI",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "video": video_data.get("video", "unknown"),
        "duration_seconds": video_data.get("duration_seconds"),
        "evidence_sources": {
            "video": "loaded",
            "image": "loaded" if image_evidence else "not supplied",
            "audio": "loaded" if audio_evidence else "not supplied"
        },
        "unified_timeline": unified_timeline,
        "findings": findings,
        "video_classification": video_classification,
        "cross_modal_validation": validation,
        "limitations": [
            "Video observations describe sampled frames, not every moment.",
            "Image and audio results have no timestamps unless supplied.",
            "Image and audio findings are currently stored as unstructured text.",
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
        print("Timeline entries:", len(result["unified_timeline"]))
        print("Evidence sources:", result["evidence_sources"])
        print(
            "Cross-modal validation:",
            result["cross_modal_validation"]["status"]
        )
        print("Saved report:", OUTPUT_FILE)

    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        print("Fusion failed:", error)
