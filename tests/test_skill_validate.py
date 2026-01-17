"""
Tests for scripts/validate-frontmatter.py skill validation functions.

Uses official Claude Code format (name + description).
"""

from pathlib import Path

import pytest

# Import validate-frontmatter.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "validate_frontmatter",
    Path(__file__).parent.parent / "scripts" / "validate-frontmatter.py"
)
validate_frontmatter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_frontmatter)

parse_frontmatter = validate_frontmatter.parse_frontmatter
count_words = validate_frontmatter.count_words
validate_skill = validate_frontmatter.validate_skill


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_parses_simple_frontmatter(self):
        """Should parse simple key-value frontmatter."""
        content = """---
name: test-skill
description: Use when testing validation
---

# Content here
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "Use when testing validation"
        assert "# Content here" in body

    def test_returns_empty_when_no_frontmatter(self):
        """Should return empty dict when no frontmatter."""
        content = "# Just content\n\nNo frontmatter here."

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_handles_incomplete_frontmatter(self):
        """Should handle incomplete frontmatter."""
        content = """---
name: test
"""
        frontmatter, body = parse_frontmatter(content)

        # Should return empty since no closing ---
        assert frontmatter == {}


class TestCountWords:
    """Tests for count_words function."""

    def test_counts_simple_text(self):
        """Should count words in simple text."""
        text = "This is a simple test with seven words"
        assert count_words(text) == 8

    def test_excludes_inline_code(self):
        """Should exclude inline code from word count."""
        text = "Use `some_function()` to do something."
        # Should count: Use, to, do, something. = 4 words
        assert count_words(text) == 4

    def test_excludes_code_blocks(self):
        """Should exclude code blocks from word count."""
        text = """
Some text here.

```python
def function():
    return value
```

More text here.
"""
        # Should only count: Some, text, here., More, text, here. = 6 words
        assert count_words(text) == 6

    def test_empty_string(self):
        """Should return 0 for empty string."""
        assert count_words("") == 0


class TestValidateSkill:
    """Tests for validate_skill function."""

    def test_valid_skill_official_format(self, tmp_path: Path):
        """Should return no errors for valid skill with official format."""
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Use when testing the validation system
---

# Test Skill

This is a test skill for validation.
""")

        errors, warnings = validate_skill(skill_file)
        assert errors == []
        assert warnings == []

    def test_missing_name(self, tmp_path: Path):
        """Should detect missing name field."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
description: Use when testing
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert any("Missing 'name'" in e for e in errors)

    def test_missing_description(self, tmp_path: Path):
        """Should detect missing description field."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert any("Missing 'description'" in e for e in errors)

    def test_name_with_invalid_characters(self, tmp_path: Path):
        """Should detect name with invalid characters."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test_skill (v2)
description: Use when testing
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert any("only letters, numbers, and hyphens" in e for e in errors)

    def test_name_too_long(self, tmp_path: Path):
        """Should detect name exceeding max length."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        long_name = "a" * 70  # Exceeds 64 char limit
        skill_file.write_text(f"""---
name: {long_name}
description: Use when testing
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert any("exceeds 64 chars" in e for e in errors)

    def test_description_not_starting_with_use_when(self, tmp_path: Path):
        """Should warn if description doesn't start with 'Use when'."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: This skill helps with testing
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert errors == []  # Not an error, just a warning
        assert any("should start with" in w for w in warnings)

    def test_deprecated_type_field(self, tmp_path: Path):
        """Should warn about deprecated type field."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Use when testing
type: discipline
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert errors == []
        assert any("'type' field is deprecated" in w for w in warnings)

    def test_deprecated_triggers_field(self, tmp_path: Path):
        """Should warn about deprecated triggers field."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Use when testing
triggers:
  - testing
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert errors == []
        assert any("'triggers' field is deprecated" in w for w in warnings)

    def test_word_count_warning(self, tmp_path: Path):
        """Should warn when word count exceeds limit."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"

        # Create content with >500 words
        lots_of_words = " ".join(["word"] * 600)
        skill_file.write_text(f"""---
name: test-skill
description: Use when testing
---

# Test

{lots_of_words}
""")

        errors, warnings = validate_skill(skill_file)

        assert errors == []
        assert any("exceeds recommended 500" in w for w in warnings)

    def test_description_starting_with_use_for(self, tmp_path: Path):
        """Should accept description starting with 'Use for'."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Use for testing validation systems
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert errors == []
        # Should not warn about description format
        assert not any("should start with" in w for w in warnings)

    def test_description_starting_with_guide_for(self, tmp_path: Path):
        """Should accept description starting with 'Guide for'."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Guide for creating effective skills
---

# Test
""")

        errors, warnings = validate_skill(skill_file)

        assert errors == []
        assert not any("should start with" in w for w in warnings)

    def test_missing_frontmatter(self, tmp_path: Path):
        """Should error on missing frontmatter."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""# Test

No frontmatter here.
""")

        errors, warnings = validate_skill(skill_file)

        assert any("Missing YAML frontmatter" in e for e in errors)
