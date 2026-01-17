#!/usr/bin/env python3
"""
Validate YAML frontmatter in agent and skill files.
Checks required fields and enum values.
"""

import re
import sys
from pathlib import Path

# Valid enum values
VALID_MODELS = ["opus", "sonnet", "haiku"]
VALID_SKILL_TYPES = ["discipline", "technique", "reference"]
VALID_PERMISSION_MODES = ["plan", "acceptEdits", "default"]

# Word limits by skill type
WORD_LIMITS = {
    "discipline": 300,
    "technique": 500,
    "reference": 800,
}

# Required sections by skill type
REQUIRED_SECTIONS = {
    "discipline": ["hard rule", "warning signs"],
    "technique": [],
    "reference": [],
}


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


def find_sections(content: str) -> list[str]:
    """Find all ## headings in content."""
    return [m.group(1).lower() for m in re.finditer(r"^## (.+)$", content, re.MULTILINE)]


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


def validate_skill(file_path: Path, alto_src: Path | None = None) -> list[str]:
    """Validate a skill file. Returns list of issues."""
    issues = []
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
        issues.append(f"{rel_path}: Missing YAML frontmatter")
        return issues

    frontmatter, body = parse_frontmatter(content)

    # Check required fields
    if "name" not in frontmatter:
        issues.append(f"{rel_path}: Missing 'name' in frontmatter")

    if "type" not in frontmatter:
        issues.append(f"{rel_path}: Missing 'type' in frontmatter")
    elif frontmatter.get("type") not in VALID_SKILL_TYPES:
        issues.append(
            f"{rel_path}: Invalid type '{frontmatter.get('type')}' "
            f"(expected: {', '.join(VALID_SKILL_TYPES)})"
        )

    if "triggers" not in frontmatter:
        issues.append(f"{rel_path}: Missing 'triggers' in frontmatter")

    skill_type = frontmatter.get("type", "technique")

    # Check word count
    word_count = count_words(body)
    limit = WORD_LIMITS.get(skill_type, 500)
    if word_count > limit:
        issues.append(
            f"{rel_path}: Word count {word_count} exceeds {limit} limit for type '{skill_type}'"
        )

    # Check required sections
    sections = find_sections(body)
    for required in REQUIRED_SECTIONS.get(skill_type, []):
        if required not in sections:
            issues.append(
                f"{rel_path}: Missing required section '## {required.title()}' for type '{skill_type}'"
            )

    return issues


def main():
    alto_src = Path(__file__).parent.parent
    all_issues = []

    # Validate agents
    agents_dir = alto_src / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            issues = validate_agent(agent_file)
            all_issues.extend(issues)

    # Validate skills in multiple locations
    skill_dirs = [
        alto_src / "skills",
        alto_src / ".claude" / "skills",
    ]

    for skill_dir in skill_dirs:
        if skill_dir.exists():
            for skill_file in skill_dir.glob("*/SKILL.md"):
                issues = validate_skill(skill_file, alto_src)
                all_issues.extend(issues)

    # Print results
    if all_issues:
        print("Frontmatter validation errors:")
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("All frontmatter valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
