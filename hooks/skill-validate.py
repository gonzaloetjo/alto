#!/usr/bin/env python3
"""
Skill validation hook for ALTO development.
Checks skill frontmatter and structure on file save.
"""

import json
import re
import sys
from pathlib import Path

# Word limits by type
WORD_LIMITS = {
    "discipline": 300,
    "technique": 500,
    "reference": 800,
}

# Required sections by type
REQUIRED_SECTIONS = {
    "discipline": ["hard rule", "warning signs"],
    "technique": [],  # flexible
    "reference": [],  # flexible
}

# Words that suggest workflow in description (should be in triggers only)
WORKFLOW_WORDS = ["then", "next", "after", "before", "first", "finally", "step"]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            # Handle list values
            if value.startswith("[") or value == "":
                continue  # Skip complex values for now
            frontmatter[key] = value

    return frontmatter, parts[2]


def count_words(text: str) -> int:
    """Count words in text, excluding code blocks."""
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    return len(text.split())


def find_sections(content: str) -> list[str]:
    """Find all ## headings in content."""
    return [m.group(1).lower() for m in re.finditer(r"^## (.+)$", content, re.MULTILINE)]


def validate_skill(file_path: Path) -> list[str]:
    """Validate a skill file. Returns list of issues."""
    issues = []
    content = file_path.read_text()

    frontmatter, body = parse_frontmatter(content)

    # Check required frontmatter
    if "name" not in frontmatter:
        issues.append("Missing 'name' in frontmatter")

    if "type" not in frontmatter:
        issues.append("Missing 'type' in frontmatter (discipline|technique|reference)")

    skill_type = frontmatter.get("type", "technique")

    # Check triggers field exists (via grep since we simplified parsing)
    if "triggers:" not in content[:500]:
        issues.append("Missing 'triggers:' field - use triggers instead of description for activation conditions")

    # Check word count
    word_count = count_words(body)
    limit = WORD_LIMITS.get(skill_type, 500)
    if word_count > limit:
        issues.append(f"Word count {word_count} exceeds {limit} limit for type '{skill_type}'")

    # Check required sections
    sections = find_sections(body)
    for required in REQUIRED_SECTIONS.get(skill_type, []):
        if required not in sections:
            issues.append(f"Missing required section '## {required.title()}' for type '{skill_type}'")

    return issues


def main():
    """Main hook entry point."""
    try:
        hook_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    tool_name = hook_data.get("tool_name", "")
    tool_input = hook_data.get("tool_input", {})

    # Only check on Write/Edit to skill files
    if tool_name not in ["Write", "Edit"]:
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return

    # Check if it's a skill file (SKILL.md in skills directory)
    if "skills/" not in file_path or not file_path.endswith("SKILL.md"):
        return

    path = Path(file_path)
    if not path.exists():
        return

    issues = validate_skill(path)

    if issues:
        print(f"\n⚠️  Skill validation warnings for {path.name}:")
        for issue in issues:
            print(f"  - {issue}")
        print()


if __name__ == "__main__":
    main()
