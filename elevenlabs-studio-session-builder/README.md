# elevenlabs-studio-session-builder

Reusable Codex Skill project for creating ElevenLabs Studio production packs from guided breathwork session briefs.

## Structure

- `SKILL.md` - skill behavior and operating workflow.
- `templates/` - starter input template.
- `examples/` - example briefs (includes Day 0 - Arrival).
- `scripts/` - Python generator.
- `outputs/` - generated production packs.

## Requirements

- Python 3.9+
- Optional for YAML input: `pyyaml`

## Usage

From this skill folder:

```bash
python3 scripts/generate_session_pack.py --input examples/day-0-arrival.yaml
```

Optional output root override:

```bash
python3 scripts/generate_session_pack.py --input examples/day-0-arrival.yaml --output-root outputs
```

## Input contract

The generator expects:

- `phase_name`
- `day_number`
- `session_title`
- `subtitle`
- `session_purpose`
- `total_target_duration_minutes`
- `number_of_states`
- `state_names`
- `state_intentions`
- `voice_style`
- `pause_style`
- `music_style`
- `breath_method`
- `transition_goal`
- `output_format`

Missing fields are auto-filled from Day 0 defaults.

## Output files

For a Day 0 Arrival run, the pack is generated in `outputs/day-0-arrival/`:

- `elevenlabs-script.txt`
- `timing-map.csv`
- `music-prompts.md`
- `studio-assembly-guide.md`
- `session-metadata.json`

## Quality checks performed by script

- Break tag presence and syntax pattern.
- Section pause-duration floor (long-pause intent).
- Section narration density.
- Runtime estimate versus target duration range.

If duration misses target, the script recommends adding or trimming silence before changing copy.
