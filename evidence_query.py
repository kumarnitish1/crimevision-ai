
import json
from pathlib import Path

REPORT_FILE = Path("fusion_report.json")


def load_report():
    if not REPORT_FILE.exists():
        raise FileNotFoundError(
            "fusion_report.json not found. Run fusion_analysis.py first."
        )

    with REPORT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def answer_query(question, report):
    question = question.lower().strip()

    if not question:
        return "Please enter a question."

    if any(word in question for word in ["source", "available evidence"]):
        sources = report.get("evidence_sources", {})
        available = [
            name for name, status in sources.items()
            if status == "loaded"
        ]
        return "Available evidence sources: " + (
            ", ".join(available) if available else "None"
        )

    if any(word in question for word in ["uncertain", "unverified", "limitation"]):
        findings = report.get("findings", [])
        uncertain = [
            item for item in findings
            if item.get("uncertainty")
            or item.get("verification_status") != "verified"
        ]

        if not uncertain:
            return "No matching uncertain findings were recorded."

        return "\n".join(
            f"- [{item.get('source', 'unknown')}] "
            f"{item.get('observation', item.get('text', 'No description'))}"
            for item in uncertain
        )

    if any(word in question for word in ["object", "objects", "weapon", "people", "person"]):
        findings = report.get("findings", [])
        results = []

        for item in findings:
            if item.get("source") == "video":
                objects = item.get("objects", [])
                people = item.get("people", [])
                if objects or people:
                    results.append(
                        f"At {item.get('timestamp_seconds')} seconds: "
                        f"people={people}; objects={objects}"
                    )
            elif item.get("source") == "image":
                results.append(item.get("text", ""))

        return "\n".join(results) if results else "No matching observations were recorded."

    
    if "timeline" in question or "happen" in question or "event" in question:
        timeline = [
            item for item in report.get("unified_timeline", [])
            if item.get("timestamp_seconds") is not None
        ]

        return "\n".join(
            f"- {item['timestamp_seconds']} seconds: "
            f"{item.get('observation', 'No observation')} "
            f"[source: {item.get('source', 'unknown')}]"
            for item in timeline
        ) or "No timestamped timeline events were recorded."



if __name__ == "__main__":
    try:
        evidence = load_report()
        print("CRIMEVISION AI - EVIDENCE QUERY")
        print("Ask about sources, objects, people, uncertainty, or the timeline.")
        print("Type 'exit' to quit.")

        while True:
            question = input("\nYour question: ").strip()

            if question.lower() in {"exit", "quit"}:
                break

            print("\nAnswer:")
            print(answer_query(question, evidence))

    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        print("Could not load evidence report:", error)
