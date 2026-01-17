#!/usr/bin/env python3
"""
Validate YAML frontmatter in agent and skill files.

Skills use official Claude Code format (name + description).
See: https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md
"""

import re
import sys
from pathlib import Path

# Valid enum values for agents
VALID_MODELS = ["opus", "sonnet", "haiku"]
VALID_PERMISSION_MODES = ["plan", "acceptEdits", "default"]

# Skill limits (from superpowers best practices)
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_SKILL_WORDS = 500  # Warning threshold
RECOMMENDED_SKILL_WORDS = 200  # For frequently-loaded skills


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter = {}
    current_key = None
    list_values = []

    for line in parts[1].strip().split("\n"):
        # Handle list items
        if line.strip().startswith("- "):
            if current_key:
                list_values.append(line.strip()[2:])
            continue

        # Save accumulated list
        if current_key and list_values:
            frontmatter[current_key] = list_values
            list_values = []
            current_key = None

        # Parse key: value
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if value == "" or value.startswith("["):
                # Start of list or empty value
                current_key = key
            else:
                frontmatter[key] = value

    # Save final list if any
    if current_key and list_values:
        frontmatter[current_key] = list_values

    return frontmatter, parts[2]


def count_words(text: str) -> int:
    """Count words in text, excluding code blocks."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    return len(text.split())


def validate_agent(file_path: Path) -> list[str]:
    """Validate an agent file. Returns list of issues."""
    issues = []
    content = file_path.read_text()

    if not content.startswith("---"):
        issues.append(f"{file_path.name}: Missing YAML frontmatter")
        return issues

    frontmatter, _ = parse_frontmatter(content)

    # Check required fields
    if "tools" not in frontmatter:
        issues.append(f"{file_path.name}: Missing 'tools' in frontmatter")

    if "model" not in frontmatter:
        issues.append(f"{file_path.name}: Missing 'model' in frontmatter")
    elif frontmatter.get("model") not in VALID_MODELS:
        issues.append(
            f"{file_path.name}: Invalid model '{frontmatter.get('model')}' "
            f"(expected: {', '.join(VALID_MODELS)})"
        )

    # Optional: permissionMode validation
    if "permissionMode" in frontmatter:
        if frontmatter["permissionMode"] not in VALID_PERMISSION_MODES:
            issues.append(
                f"{file_path.name}: Invalid permissionMode '{frontmatter['permissionMode']}' "
                f"(expected: {', '.join(VALID_PERMISSION_MODES)})"
            )

    return issues


def validate_skill(file_path: Path, alto_src: Path | None = None) -> tuple[list[str], list[str]]:
    """Validate a skill file.

    Returns (errors, warnings) tuple.
    Uses official Claude Code format: name + description only.
    """
    errors = []
    warnings = []
    content = file_path.read_text()

    # Get relative path for better error messages
    if alto_src:
        try:
            rel_path = file_path.relative_to(alto_src)
        except ValueError:
            rel_path = file_path
    else:
        rel_path = file_path

    if not content.startswith("---"):
        errors.append(f"{rel_path}: Missing YAML frontmatter")
        return errors, warnings

    frontmatter, body = parse_frontmatter(content)

    # === Required fields (official format) ===

    # name is required
    if "name" not in frontmatter:
        errors.append(f"{rel_path}: Missing 'name' in frontmatter")
    else:
        name = frontmatter["name"]
        # Name should use only letters, numbers, hyphens
        if not re.match(r'^[a-zA-Z0-9-]+$', name):
            errors.append(f"{rel_path}: name '{name}' should use only letters, numbers, and hyphens")
        if len(name) > MAX_NAME_LENGTH:
            errors.append(f"{rel_path}: name exceeds {MAX_NAME_LENGTH} chars ({len(name)})")

    # description is required (this is how Claude discovers skills)
    if "description" not in frontmatter:
        errors.append(f"{rel_path}: Missing 'description' in frontmatter (required for skill discovery)")
    else:
        desc = frontmatter["description"]
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            errors.append(f"{rel_path}: description exceeds {MAX_DESCRIPTION_LENGTH} chars ({len(desc)})")

        # Superpowers best practice: description should start with "Use when"
        desc_lower = desc.lower()
        if not (desc_lower.startswith("use when") or desc_lower.startswith("use for") or
                desc_lower.startswith("guide for") or desc_lower.startswith("use to")):
            warnings.append(
                f"{rel_path}: description should start with 'Use when...' to describe triggering conditions"
            )

    # === Deprecated fields (ALTO legacy) ===

    if "type" in frontmatter:
        warnings.append(
            f"{rel_path}: 'type' field is deprecated - Claude Code ignores it. "
            "Document skill type in body instead."
        )

    if "triggers" in frontmatter:
        warnings.append(
            f"{rel_path}: 'triggers' field is deprecated - Claude Code ignores it. "
            "Put triggering conditions in 'description' field."
        )

    # === Content quality checks (warnings) ===

    word_count = count_words(body)
    if word_count > MAX_SKILL_WORDS:
        warnings.append(
            f"{rel_path}: {word_count} words exceeds recommended {MAX_SKILL_WORDS}. "
            "Consider moving heavy content to references/ subdir."
        )

    return errors, warnings


def main():
    alto_src = Path(__file__).parent.parent
    all_errors = []
    all_warnings = []

    # Validate agents
    agents_dir = alto_src / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            errors = validate_agent(agent_file)
            all_errors.extend(errors)

    # Validate skills in multiple locations
    skill_dirs = [
        alto_src / "skills",
        alto_src / ".claude" / "skills",
    ]

    for skill_dir in skill_dirs:
        if skill_dir.exists():
            for skill_file in skill_dir.glob("*/SKILL.md"):
                errors, warnings = validate_skill(skill_file, alto_src)
                all_errors.extend(errors)
                all_warnings.extend(warnings)

    # Print results
    exit_code = 0

    if all_errors:
        print("Frontmatter validation ERRORS:")
        for error in all_errors:
            print(f"  ✗ {error}")
        exit_code = 1

    if all_warnings:
        print("\nFrontmatter validation WARNINGS:")
        for warning in all_warnings:
            print(f"  ! {warning}")

    if not all_errors and not all_warnings:
        print("All frontmatter valid ✓")
    elif not all_errors:
        print("\nNo errors (warnings only)")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
