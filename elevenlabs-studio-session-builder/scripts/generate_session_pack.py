#!/usr/bin/env python3
"""Generate an ElevenLabs Studio-ready production pack from a session brief."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

DAY0_DEFAULTS = {
    "phase_name": "Phase 1 - Regulate",
    "day_number": "Day 0",
    "session_title": "Arrival",
    "subtitle": "Meet your current state",
    "session_purpose": "Create safety before regulation begins",
    "total_target_duration_minutes": "12-15",
    "number_of_states": 4,
    "state_names": ["Landing", "Noticing", "Softening", "Settling"],
    "state_intentions": [
        "I am here",
        "This is what is present",
        "I do not need to change it yet",
        "Something in me can rest",
    ],
    "voice_style": "calm, spacious, slow, grounded, emotionally safe",
    "pause_style": "long pauses, mostly 8-12 seconds, occasional 15 seconds",
    "music_style": "ambient, spacious, low movement, warm, regulation-first, no percussion",
    "breath_method": "natural breath only, no counting",
    "transition_goal": "prepare the user for Day 1 regulation without creating pressure",
    "output_format": "mp3 and wav",
}

REQUIRED_FIELDS = [
    "phase_name",
    "day_number",
    "session_title",
    "subtitle",
    "session_purpose",
    "total_target_duration_minutes",
    "number_of_states",
    "state_names",
    "state_intentions",
    "voice_style",
    "pause_style",
    "music_style",
    "breath_method",
    "transition_goal",
    "output_format",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to input JSON or YAML brief")
    parser.add_argument(
        "--output-root",
        default="outputs",
        help="Root output directory (default: outputs under skill directory)",
    )
    return parser.parse_args()


def load_input(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yml", ".yaml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise SystemExit("PyYAML is required for YAML input. Install with: pip install pyyaml") from exc
        return yaml.safe_load(text)
    raise SystemExit("Input file must be .json, .yml, or .yaml")


def to_slug(day_number: str, session_title: str) -> str:
    raw = f"{day_number}-{session_title}".lower().strip()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    return raw.strip("-")


def parse_duration_range(value: Any) -> tuple[float, float]:
    if isinstance(value, (int, float)):
        return float(value), float(value)
    if isinstance(value, str):
        m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$", value)
        if m:
            return float(m.group(1)), float(m.group(2))
        n = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", value)
        if n:
            v = float(n.group(1))
            return v, v
    raise ValueError(f"Could not parse duration target: {value!r}")


def validate_and_fill(data: dict[str, Any]) -> dict[str, Any]:
    merged = dict(DAY0_DEFAULTS)
    merged.update({k: v for k, v in data.items() if v is not None})

    missing = [k for k in REQUIRED_FIELDS if k not in merged]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    if len(merged["state_names"]) != merged["number_of_states"]:
        raise ValueError("number_of_states must match length of state_names")
    if len(merged["state_intentions"]) != merged["number_of_states"]:
        raise ValueError("number_of_states must match length of state_intentions")

    return merged


def fmt_ts(seconds: float) -> str:
    total = int(round(seconds))
    mm, ss = divmod(total, 60)
    return f"{mm:02d}:{ss:02d}"


def word_count(text: str) -> int:
    no_tags = re.sub(r"<break time=\"\d+s\"\s*/>", " ", text)
    tokens = re.findall(r"[A-Za-z0-9']+", no_tags)
    return len(tokens)


def pause_total_seconds(text: str) -> int:
    matches = re.findall(r"<break time=\"(\d+)s\"\s*/>", text)
    return sum(int(m) for m in matches)


def build_section_text(state: str, intention: str, breath_method: str, is_last: bool) -> str:
    pause_pattern = [10, 12, 8, 10, 12, 15, 10, 8, 12, 10, 8, 12, 10, 10, 12]
    closing = "Stay here for a few quiet breaths." if is_last else "Let this settle, then we will continue."

    lines = [
        f"{state}.",
        "Notice the points of contact beneath you.",
        "Let your jaw, shoulders, and belly be unguarded.",
        "There is nothing to force in this moment.",
        f"Let the body hear this signal: {intention}.",
        "Allow your breath to move in its own rhythm.",
        f"{breath_method.capitalize()}.",
        "Name one sensation without changing it.",
        "If emotion is present, let it be present and held.",
        closing,
    ]

    chunks: list[str] = []
    for i, line in enumerate(lines):
        chunks.append(line)
        chunks.append(f'<break time="{pause_pattern[i]}s"/>')

    for extra in pause_pattern[len(lines):]:
        chunks.append(f'<break time="{extra}s"/>')

    return "\n".join(chunks)


def build_music_prompt(state: str, duration: int, intention: str, transition: str, style: str) -> str:
    return (
        f"### {state}\n"
        f"- **Duration target:** ~{duration // 60}:{duration % 60:02d}\n"
        f"- **Emotional tone:** grounded, warm, safe; intention: {intention}\n"
        f"- **Style anchor:** {style}\n"
        "- **Prompt (Suno-ready):** "
        f"Create an ambient, low-movement, non-percussive bed for somatic breathwork. "
        f"Keep harmonic motion minimal and warm. Support spoken voice without competing frequencies. "
        f"State focus: {state.lower()}, with gentle space and long sustains."
        "\n"
        f"- **Transition to next section:** {transition}\n"
    )


def main() -> None:
    args = parse_args()
    base_dir = Path(__file__).resolve().parents[1]
    input_path = (base_dir / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input)
    output_root = (base_dir / args.output_root).resolve() if not Path(args.output_root).is_absolute() else Path(args.output_root)

    data = validate_and_fill(load_input(input_path))
    min_min, max_min = parse_duration_range(data["total_target_duration_minutes"])
    target_mid_sec = ((min_min + max_min) / 2) * 60

    slug = to_slug(str(data["day_number"]), str(data["session_title"]))
    out_dir = output_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    states: list[str] = data["state_names"]
    intentions: list[str] = data["state_intentions"]

    section_script_blocks: list[str] = []
    rows: list[dict[str, str]] = []

    timeline_sec = 0.0
    section_target = int(round(target_mid_sec / len(states)))
    total_words = 0
    total_pauses = 0

    for idx, (state, intention) in enumerate(zip(states, intentions), start=1):
        section_text = build_section_text(
            state=state,
            intention=intention,
            breath_method=data["breath_method"],
            is_last=idx == len(states),
        )
        words = word_count(section_text)
        pauses = pause_total_seconds(section_text)
        speech_seconds = (words / 98.0) * 60.0
        section_seconds = speech_seconds + pauses

        total_words += words
        total_pauses += pauses

        start = timeline_sec
        end = timeline_sec + section_seconds
        timeline_sec = end

        next_state = states[idx] if idx < len(states) else "close"
        music_instruction = (
            f"Continuous ambient bed; subtle tonal shift for {state.lower()}; keep voice-leading space."
        )
        transition_note = (
            f"Fade motif over 6-10s into {next_state}."
            if idx < len(states)
            else "Resolve gently and leave 15-20s of trailing space."
        )

        rows.append(
            {
                "section_number": str(idx),
                "state_name": state,
                "estimated_start": fmt_ts(start),
                "estimated_end": fmt_ts(end),
                "narration_word_count": str(words),
                "total_pause_seconds": str(pauses),
                "music_instruction": music_instruction,
                "transition_note": transition_note,
            }
        )

        section_script_blocks.append(f"Section {idx} - {state}\n{section_text}")

    total_seconds = timeline_sec
    min_sec, max_sec = min_min * 60, max_min * 60
    duration_status = "on_target"
    adjustment_note = "Duration is within target range."
    if total_seconds < min_sec:
        duration_status = "short"
        adjustment_note = (
            "Script is shorter than target. Extend silence first: add 8-12s pauses at the end of each section "
            "before adding words."
        )
    elif total_seconds > max_sec:
        duration_status = "long"
        adjustment_note = (
            "Script is longer than target. Trim low-priority lines and keep long pauses only where settling is needed."
        )

    elevenlabs_script = "\n\n".join(section_script_blocks).strip() + "\n"
    script_path = out_dir / "elevenlabs-script.txt"
    script_path.write_text(elevenlabs_script, encoding="utf-8")

    timing_path = out_dir / "timing-map.csv"
    with timing_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "section_number",
                "state_name",
                "estimated_start",
                "estimated_end",
                "narration_word_count",
                "total_pause_seconds",
                "music_instruction",
                "transition_note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    music_sections = []
    for i, (state, intention) in enumerate(zip(states, intentions)):
        transition = (
            f"Shift energy by soft crossfade into {states[i + 1]}."
            if i < len(states) - 1
            else "Close with low-volume tail and no dramatic ending."
        )
        music_sections.append(build_music_prompt(state, section_target, intention, transition, data["music_style"]))
    music_content = (
        "# Music Prompts\n\n"
        "Use one continuous music arc with subtle state shifts. Maintain low intensity so narration remains primary.\n\n"
        + "\n".join(music_sections)
    )
    (out_dir / "music-prompts.md").write_text(music_content, encoding="utf-8")

    checklist = [
        "Narration imported and split into 4 sections matching state boundaries.",
        "Voice level peaks between -6 dB and -3 dB.",
        "Music bed stays at least 12 dB below narration during speech.",
        "Crossfades between music sections are 6-10 seconds and not abrupt.",
        "Long pauses preserved (mostly 8-12s, occasional 15s).",
        f"Final export delivered as {data['output_format']}.",
    ]

    guide = f"""# ElevenLabs Studio Assembly Guide

## Session
- **Phase:** {data['phase_name']}
- **Day:** {data['day_number']}
- **Title:** {data['session_title']}
- **Subtitle:** {data['subtitle']}

## 1) Import narration
1. Open ElevenLabs Studio and create a new project.
2. Paste `elevenlabs-script.txt` into the narration track.
3. Generate voice with style notes: {data['voice_style']}.
4. Keep pacing natural; do not compress pauses.

## 2) Split by section
1. Create section markers at each `Section X - State` boundary.
2. Confirm timing against `timing-map.csv`.
3. Keep each state close to equal length unless artistic constraints require minor variation.

## 3) Place music under voice
1. Import or generate one ambient bed per state from `music-prompts.md`.
2. Arrange tracks continuously so the session is musically unbroken.
3. Use subtle tonal shifts only; avoid rhythmic accents or percussion.

## 4) Fades and transitions
1. Apply 6-10s crossfades between state music stems.
2. For narration priority, duck music by 2-4 dB during spoken lines.
3. Preserve intentional silence; avoid filling every gap with movement.

## 5) Voice-leading and final balance
1. Voice must lead; music supports regulation and never competes.
2. Re-check the "Softening" and "Settling" sections for calm continuity.
3. Keep final limiter gentle; avoid pumping.

## 6) Export
1. Export master in requested formats: {data['output_format']}.
2. Name files using the session slug `{slug}`.
3. Spot-check beginning, midpoint, and ending on headphones and phone speakers.

## Production checklist
"""
    guide += "\n".join([f"- [ ] {item}" for item in checklist])
    guide += (
        "\n\n## Timing QA\n"
        f"- Estimated runtime: {fmt_ts(total_seconds)}\n"
        f"- Target range: {int(min_min)}-{int(max_min)} minutes\n"
        f"- Status: {duration_status}\n"
        f"- Note: {adjustment_note}\n"
    )
    (out_dir / "studio-assembly-guide.md").write_text(guide, encoding="utf-8")

    metadata = {
        "phase": data["phase_name"],
        "day": data["day_number"],
        "title": data["session_title"],
        "subtitle": data["subtitle"],
        "duration_target": data["total_target_duration_minutes"],
        "states": states,
        "breath_method": data["breath_method"],
        "completion_message": "Thank you for arriving exactly as you are.",
        "next_session_prompt": "When you are ready, continue to Day 1 to begin gentle regulation.",
    }
    (out_dir / "session-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Console quality report
    tag_valid = bool(re.search(r"<break time=\"\d+s\"\s*/>", elevenlabs_script))
    pauses_ok = all(int(r["total_pause_seconds"]) >= 80 for r in rows)
    density_ok = all(int(r["narration_word_count"]) <= 120 for r in rows)

    print(f"Generated session pack at: {out_dir}")
    print(f"Runtime estimate: {fmt_ts(total_seconds)} (target {min_min}-{max_min} minutes)")
    print(f"Check break tags: {'PASS' if tag_valid else 'FAIL'}")
    print(f"Check pause lengths: {'PASS' if pauses_ok else 'FAIL'}")
    print(f"Check section density: {'PASS' if density_ok else 'FAIL'}")
    print(f"Duration status: {duration_status} ({adjustment_note})")


if __name__ == "__main__":
    main()
