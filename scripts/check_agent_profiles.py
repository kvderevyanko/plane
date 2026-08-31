#!/usr/bin/env python3
"""Validate the cost and reasoning profiles of LR1600 specialist agents.

This is a deterministic preflight: it prevents an accidental fallback to the
``gpt-5.6`` alias (GPT-5.6 Sol) or a silent change of reasoning effort.
"""

from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".codex" / "agents"
EXPECTED_PROFILES = {
    "aero-analyst": ("gpt-5.6-terra", "high"),
    "aircraft-lead": ("gpt-5.6-sol", "high"),
    "avionics-autopilot": ("gpt-5.6-terra", "high"),
    "cad-laser-engineer": ("gpt-5.6-terra", "medium"),
    "independent-reviewer": ("gpt-5.6-sol", "high"),
    "structures-manufacturing": ("gpt-5.6-terra", "high"),
}


def validate_agent_profiles(agents_dir: Path = AGENTS_DIR) -> list[str]:
    """Return every profile-policy violation found in *agents_dir*."""
    errors: list[str] = []
    expected_names = set(EXPECTED_PROFILES)
    actual_paths = {path.stem: path for path in agents_dir.glob("*.toml")}

    for missing_name in sorted(expected_names - set(actual_paths)):
        errors.append(f"missing agent profile: {missing_name}.toml")
    for extra_name in sorted(set(actual_paths) - expected_names):
        errors.append(f"unexpected agent profile: {extra_name}.toml")

    for name, (expected_model, expected_effort) in EXPECTED_PROFILES.items():
        path = actual_paths.get(name)
        if path is None:
            continue
        try:
            profile = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as error:
            errors.append(f"{path.name}: invalid TOML: {error}")
            continue

        if profile.get("name") != name:
            errors.append(f"{path.name}: name must be {name!r}")
        if profile.get("model") != expected_model:
            errors.append(f"{path.name}: model must be {expected_model!r}")
        if profile.get("model_reasoning_effort") != expected_effort:
            errors.append(
                f"{path.name}: model_reasoning_effort must be {expected_effort!r}"
            )
    return errors


def main() -> int:
    errors = validate_agent_profiles()
    if errors:
        print("Agent profile policy failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Agent profile policy passed: 2 GPT-5.6 Sol gates and 4 GPT-5.6 Terra specialists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
