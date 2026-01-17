"""
Tests for hooks/skill-validate.py functions.
"""

import json
from pathlib import Path

import pytest

# Import will use conftest.py path setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

# Use importlib to handle the hyphenated filename
import importlib.util
spec = importlib.util.spec_from_file_location(
    "skill_validate",
    Path(__file__).parent.parent / "hooks" / "skill-validate.py"
)
skill_validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_validate)

parse_frontmatter = skill_validate.parse_frontmatter
count_words = skill_validate.count_words
find_sections = skill_validate.find_sections
validate_skill = skill_validate.validate_skill


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_parses_simple_frontmatter(self):
        """Should parse simple key-value frontmatter."""
        content = """---
name: test-skill
type: discipline
---

# Content here
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["name"] == "test-skill"
        assert frontmatter["type"] == "discipline"
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


class TestFindSections:
    """Tests for find_sections function."""

    def test_finds_h2_sections(self):
        """Should find all ## headings."""
        content = """
# Title

## First Section

Content.

## Second Section

More content.

## Third Section
"""
        sections = find_sections(content)

        assert sections == ["first section", "second section", "third section"]

    def test_returns_empty_when_no_sections(self):
        """Should return empty list when no ## headings."""
        content = "# Just a title\n\nNo sections here."

        sections = find_sections(content)

        assert sections == []

    def test_normalizes_to_lowercase(self):
        """Should return lowercase section names."""
        content = "## Hard Rule\n\n## Warning Signs"

        sections = find_sections(content)

        assert sections == ["hard rule", "warning signs"]


class TestValidateSkill:
    """Tests for validate_skill function."""

    def test_valid_discipline_skill(self, sample_skill_file: Path):
        """Should return no issues for valid discipline skill."""
        issues = validate_skill(sample_skill_file)
        assert issues == []

    def test_missing_name(self, tmp_path: Path):
        """Should detect missing name field."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
type: discipline
triggers:
  - test
---

# Test

## Hard Rule
Test

## Warning Signs
Test
""")

        issues = validate_skill(skill_file)

        assert any("Missing 'name'" in i for i in issues)

    def test_missing_type(self, tmp_path: Path):
        """Should detect missing type field."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
triggers:
  - test
---

# Test
""")

        issues = validate_skill(skill_file)

        assert any("Missing 'type'" in i for i in issues)

    def test_missing_triggers(self, tmp_path: Path):
        """Should detect missing triggers field."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
type: discipline
---

# Test

## Hard Rule
Test

## Warning Signs
Test
""")

        issues = validate_skill(skill_file)

        # Note: the actual message includes the colon: "Missing 'triggers:'"
        assert any("triggers" in i.lower() for i in issues)

    def test_discipline_missing_hard_rule(self, tmp_path: Path):
        """Should detect missing Hard Rule section for discipline."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
type: discipline
triggers:
  - test
---

# Test

## Warning Signs
Test
""")

        issues = validate_skill(skill_file)

        assert any("Hard Rule" in i for i in issues)

    def test_discipline_missing_warning_signs(self, tmp_path: Path):
        """Should detect missing Warning Signs section for discipline."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
type: discipline
triggers:
  - test
---

# Test

## Hard Rule
Test
""")

        issues = validate_skill(skill_file)

        assert any("Warning Signs" in i for i in issues)

    def test_word_count_exceeds_limit(self, tmp_path: Path):
        """Should detect when word count exceeds limit."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"

        # Discipline has 300 word limit
        lots_of_words = " ".join(["word"] * 400)
        skill_file.write_text(f"""---
name: test-skill
type: discipline
triggers:
  - test
---

# Test

## Hard Rule
{lots_of_words}

## Warning Signs
Test
""")

        issues = validate_skill(skill_file)

        assert any("Word count" in i for i in issues)

    def test_technique_no_required_sections(self, tmp_path: Path):
        """Should not require specific sections for technique type."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
type: technique
triggers:
  - test
---

# Test

Just some content.
""")

        issues = validate_skill(skill_file)

        # Should not have section-related issues
        assert not any("section" in i.lower() for i in issues)

    def test_reference_higher_word_limit(self, tmp_path: Path):
        """Should allow more words for reference type."""
        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"

        # Reference has 800 word limit, use 600 words
        words = " ".join(["word"] * 600)
        skill_file.write_text(f"""---
name: test-skill
type: reference
triggers:
  - test
---

# Test

{words}
""")

        issues = validate_skill(skill_file)

        # Should not have word count issue
        assert not any("Word count" in i for i in issues)
