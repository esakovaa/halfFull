from __future__ import annotations

import json
from pathlib import Path


ROOT = Path("/Users/annaesakova/aipm/halfFull")
JSON_PATH = ROOT / "assessment_quiz/nhanes_combined_question_flow.json"
OUT_PATH = ROOT / "assessment_quiz/nhanes_combined_question_flow_visualization.md"


TYPE_HELP = {
    "number": "Numeric input",
    "single_select": "Single choice",
    "multi_select": "Multiple choice",
    "multi_select_with_count": "Multiple choice + medication count",
    "grouped_numeric": "Grouped numeric / mixed entry",
    "grouped_demographic": "Grouped demographic entry",
    "grouped_single_select": "Grouped select response",
    "grouped_time_and_duration": "Grouped time + duration entry",
    "grouped_branching": "Grouped branching follow-up",
    "grouped_activity": "Grouped activity and frequency entry",
    "grouped_work": "Grouped work-pattern entry",
}


def format_options(question: dict) -> list[str]:
    options = question.get("options", [])
    lines: list[str] = []
    if not options:
        lines.append("- Explicit options in JSON: none")
        lines.append(f"- Expected answer format: {TYPE_HELP.get(question['type'], question['type'])}")
        return lines

    lines.append("- Answer options:")
    for option in options:
        if isinstance(option, str):
            lines.append(f"  - `{option}`")
        else:
            label = option.get("label", "")
            maps_to = option.get("maps_to", "")
            lines.append(f"  - `{label}` -> `{maps_to}`")
    return lines


def main() -> None:
    data = json.loads(JSON_PATH.read_text())

    lines: list[str] = []
    lines.append("# NHANES Combined Question Flow Visualization")
    lines.append("")
    lines.append(f"Version: `{data['metadata']['version']}`")
    lines.append("")
    lines.append("## Conditions covered")
    lines.append("")
    for condition in data["metadata"]["conditions_covered"]:
        lines.append(f"- {condition}")
    lines.append("")

    lines.append("## High-level flow")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart TD")
    prev = None
    for idx, group in enumerate(data["question_groups"], start=1):
        node = f"G{idx}"
        label = f"{idx}. {group['title']}"
        lines.append(f'    {node}["{label}"]')
        if prev:
            lines.append(f"    {prev} --> {node}")
        prev = node
    lines.append("```")
    lines.append("")

    lines.append("## Detailed structure")
    lines.append("")
    for idx, group in enumerate(data["question_groups"], start=1):
        lines.append(f"### {idx}. {group['title']} (`{group['id']}`)")
        lines.append("")
        for qidx, question in enumerate(group["questions"], start=1):
            lines.append(f"#### {idx}.{qidx} {question['id']}")
            lines.append("")
            lines.append(f"- Text: {question['text']}")
            lines.append(f"- Type: `{question['type']}` ({TYPE_HELP.get(question['type'], question['type'])})")
            if "conditions" in question:
                lines.append(f"- Used for: {', '.join(question['conditions'])}")
            if "show_if" in question:
                lines.append(f"- Show if: `{json.dumps(question['show_if'])}`")
            if "maps_to" in question:
                lines.append(f"- Maps to: `{', '.join(question['maps_to'])}`")
            if "derives" in question:
                lines.append(f"- Derives: `{', '.join(question['derives'])}`")
            lines.extend(format_options(question))
            lines.append("")

    lines.append("## Derived / lab-only features kept outside the interactive quiz")
    lines.append("")
    for feature in data.get("derived_or_lab_features", []):
        lines.append(f"- `{feature}`")
    lines.append("")

    OUT_PATH.write_text("\n".join(lines))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
