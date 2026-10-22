
import cv2
import os
import json


def extract_frames(video_path, output_dir="extracted_frames",
                   every_seconds=1, max_frames=30):
    """Extract one video frame per second and save it as an image."""

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Could not open video. Check its format.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0 or total_frames <= 0:
        cap.release()
        raise ValueError("Could not read video FPS or frame count.")

    duration = total_frames / fps
    interval = max(1, round(fps * every_seconds))

    results = []
    frame_index = 0

    while len(results) < max_frames:
        success, frame = cap.read()

        if not success:
            break

        if frame_index % interval == 0:
            timestamp = round(frame_index / fps, 2)

            height, width = frame.shape[:2]
            if width > 640:
                new_height = int(height * 640 / width)
                frame = cv2.resize(frame, (640, new_height))

            filename = f"frame_{timestamp:06.2f}.jpg"
            filepath = os.path.join(output_dir, filename)

            saved = cv2.imwrite(filepath, frame)

            if saved:
                results.append({
                    "timestamp_seconds": timestamp,
                    "frame_path": filepath
                })

        frame_index += 1

    cap.release()

    return {
        "video": os.path.basename(video_path),
        "fps": round(fps, 2),
        "duration_seconds": round(duration, 2),
        "frames_extracted": len(results),
        "frames": results
    }


if __name__ == "__main__":
    try:
        result = extract_frames("scene.mp4")

        print("=== VIDEO FRAME EXTRACTION ===")
        print(json.dumps(result, indent=2))

        with open("frame_results.json", "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        print("\nSaved results to frame_results.json")

    except (FileNotFoundError, ValueError, OSError) as error:
        print("Error:", error)
