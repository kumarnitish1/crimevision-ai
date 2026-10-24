
import json
import re
from pathlib import Path

from google.genai import types
from gemini_helper import generate


INPUT_FILE = Path("frame_results.json")
OUTPUT_FILE = Path("timeline.json")
BATCH_SIZE = 3
MAX_BATCH_ATTEMPTS = 2


def parse_json(text):
    """Convert a Gemini JSON response into Python data."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Recover a JSON array or object if extra text was returned.
        start_array = text.find("[")
        end_array = text.rfind("]")
        if start_array != -1 and end_array > start_array:
            return json.loads(text[start_array:end_array + 1])

        start_object = text.find("{")
        end_object = text.rfind("}")
        if start_object != -1 and end_object > start_object:
            return json.loads(text[start_object:end_object + 1])

        raise ValueError("Gemini did not return valid JSON.")
    
import time


def analyze_batch_with_retry(batch):
    """Retry a failed batch once, without changing successful results."""
    last_error = None

    for attempt in range(MAX_BATCH_ATTEMPTS):
        try:
            return analyze_frame_batch(batch)
        except Exception as error:
            last_error = error

            if attempt < MAX_BATCH_ATTEMPTS - 1:
                print("Batch failed. Retrying once in 5 seconds...")
                time.sleep(5)

    raise RuntimeError(
        f"Batch failed after {MAX_BATCH_ATTEMPTS} attempts: {last_error}"
    )



def analyze_frame_batch(frames):
    """Analyze a small batch of extracted video frames."""
    contents = []

    for frame in frames:
        image_path = Path(frame["frame_path"])

        if not image_path.exists():
            raise FileNotFoundError(f"Frame not found: {image_path}")

        contents.append(
            f"Frame timestamp: {frame['timestamp_seconds']} seconds."
        )

        contents.append(
            types.Part.from_bytes(
                data=image_path.read_bytes(),
                mime_type="image/jpeg"
            )
        )

    contents.append("""
You are assisting with forensic video review.

Analyze each supplied frame separately. Return ONLY a JSON array.
For each frame, provide:
- timestamp_seconds: copy the exact timestamp supplied
- people: a list of clearly visible people or visible characteristics
- objects: a list of notable visible objects
- action: the action clearly visible in this frame
- uncertainty: details that cannot be determined from this frame

Do not invent movement between frames. A single image cannot establish
what happened before or after it. Do not infer that an object is a weapon
unless its appearance clearly supports that description. Do not conclude
that a crime occurred merely because a scene looks suspicious.

Use short, factual descriptions. If something is not visible, say so.
""")

    response = generate(contents)
    result = parse_json(response)

    if not isinstance(result, list):
        raise ValueError("Expected a JSON array of frame descriptions.")

    return result


def classify_scene(events):
    """Produce a cautious summary based only on analyzed frame descriptions."""
    prompt = """
You are assisting with forensic video review.

Use ONLY the frame descriptions supplied below.

Return ONLY a JSON object with these fields:
- scene_summary: a short factual summary
- activity_category: one of
  "ordinary activity", "possible theft", "possible assault",
  "possible vandalism", "other activity", "unclear"
- confidence: "low", "medium", or "high"
- supporting_observations: a list of observations supporting the category
- limitations: a list of missing information or alternative explanations

Do not treat a possible crime as a confirmed crime. Do not invent events
between sampled frames. If evidence is insufficient, choose "unclear"
and use low confidence. A video classification is not a legal conclusion.

Frame descriptions:
""" + json.dumps(events, ensure_ascii=False)

    return parse_json(generate(prompt))


def build_timeline():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "frame_results.json not found. Run video_analysis.py first."
        )

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    frames = data.get("frames", [])

    if not frames:
        raise ValueError("No extracted frames found in frame_results.json.")

    timeline = [
        {
            "timestamp_seconds": frame["timestamp_seconds"],
            "frame_path": frame["frame_path"],
            "event": None,
            "people": [],
            "objects": [],
            "uncertainty": "Not analyzed yet",
            "analysis_status": "pending"
        }
        for frame in frames
    ]

    result = {
        "video": data.get("video", "unknown"),
        "duration_seconds": data.get("duration_seconds"),
        "timeline": timeline,
        "classification": {
            "status": "pending",
            "result": None
        }
    }

    # Save the initial state before making any API calls.
    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    successful_events = []

    for start in range(0, len(frames), BATCH_SIZE):
        batch = frames[start:start + BATCH_SIZE]
        print(
            f"Analyzing frames {start + 1} to "
            f"{start + len(batch)} of {len(frames)}..."
        )

        try:
            descriptions = analyze_batch_with_retry(batch)

            # Match model responses to the requested timestamps.
            by_timestamp = {
                round(float(item["timestamp_seconds"]), 2): item
                for item in descriptions
                if isinstance(item, dict)
                and "timestamp_seconds" in item
            }

            for frame in batch:
                timestamp = round(
                    float(frame["timestamp_seconds"]), 2
                )
                index = frames.index(frame)
                description = by_timestamp.get(timestamp)

                if description is None:
                    timeline[index]["analysis_status"] = "failed"
                    timeline[index]["uncertainty"] = (
                        "No matching description returned for this frame."
                    )
                    continue

                timeline[index].update({
                    "event": description.get(
                        "action", "Action not described"
                    ),
                    "people": description.get("people", []),
                    "objects": description.get("objects", []),
                    "uncertainty": description.get(
                        "uncertainty", "Not specified"
                    ),
                    "analysis_status": "completed"
                })

                successful_events.append({
                    "timestamp_seconds": timestamp,
                    "event": timeline[index]["event"],
                    "people": timeline[index]["people"],
                    "objects": timeline[index]["objects"],
                    "uncertainty": timeline[index]["uncertainty"]
                })

        except Exception as error:
            print(f"Batch failed: {error}")

            for frame in batch:
                index = frames.index(frame)
                timeline[index]["analysis_status"] = "failed"
                timeline[index]["uncertainty"] = (
                    "AI analysis failed; see terminal output."
                )

        # Save progress after every batch, including failed batches.
        OUTPUT_FILE.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    if successful_events:
        try:
            print("Generating scene summary and classification...")
            result["classification"]["result"] = classify_scene(
                successful_events
            )
            result["classification"]["status"] = "completed"

        except Exception as error:
            print(f"Classification failed: {error}")
            result["classification"]["status"] = "failed"
    else:
        result["classification"]["status"] = "skipped"

    result["analysis_summary"] = {
        "frames_total": len(frames),
        "frames_analyzed": sum(
            item["analysis_status"] == "completed"
            for item in timeline
        ),
        "frames_failed": sum(
            item["analysis_status"] == "failed"
            for item in timeline
        )
    }

    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return result


if __name__ == "__main__":
    try:
        final_result = build_timeline()
        print("\n=== VIDEO TIMELINE ===")
        print(json.dumps(final_result, indent=2, ensure_ascii=False))
        print(f"\nResults saved to {OUTPUT_FILE}")

    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"Error: {error}")
