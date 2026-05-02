# elevenlabs-studio-session-builder

## Purpose
Build a full ElevenLabs Studio production package from a guided breathwork session brief. The package includes a narration script with break tags, a timing map, section-level music prompts, a practical Studio assembly guide, and app/web metadata.

## When to use this skill
Use this skill when the user wants to:
- turn a somatic/breathwork brief into a production-ready voice+music session,
- prepare sessions for Metamorphos Flow Space Phase 1 (starting at Day 0 - Arrival),
- keep narration sparse with long pauses and state-based music transitions.

## Inputs
Provide a JSON or YAML file with:
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

### Day 0 defaults
The generator automatically fills missing fields with Day 0 defaults for:
- Phase 1 - Regulate / Day 0 / Arrival
- states: Landing, Noticing, Softening, Settling
- regulation-first narration and ambient music settings.

## Workflow
1. Create (or copy) a brief file from `templates/session-input-template.yaml`.
2. Run the generator script:
   - `python3 scripts/generate_session_pack.py --input examples/day-0-arrival.yaml`
3. Review generated files in `outputs/<session-slug>/`.
4. If timing is outside target range, use the script’s warnings and extend silence (not word count) first.

## Output package
For each session the skill generates:
- `elevenlabs-script.txt`
- `timing-map.csv`
- `music-prompts.md`
- `studio-assembly-guide.md`
- `session-metadata.json`

## Quality checks (automatic)
The script validates:
- break tags are present and syntactically valid,
- pauses are mostly 8s+,
- per-section density is not excessive,
- timing map aligns to generated narration estimates,
- target duration fit (with explicit warnings if short/long).

## Notes for Metamorphos Flow Space
- Phase 1 language remains regulation-first and soma-first.
- No fixing, no forced transformation, no breath-counting protocol.
- Music remains continuous and supportive, with subtle state shifts.
