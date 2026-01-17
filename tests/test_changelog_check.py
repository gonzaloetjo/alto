"""
Tests for hooks/changelog-check.py functions.
"""

from pathlib import Path

import pytest

# Import will use conftest.py path setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

# Use importlib to handle the hyphenated filename
import importlib.util
spec = importlib.util.spec_from_file_location(
    "changelog_check",
    Path(__file__).parent.parent / "hooks" / "changelog-check.py"
)
changelog_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog_check)

is_key_file = changelog_check.is_key_file


class TestIsKeyFile:
    """Tests for is_key_file function."""

    def test_templates_claude_md(self):
        """Should identify templates/CLAUDE.md as key file."""
        assert is_key_file("templates/CLAUDE.md") is True
        assert is_key_file("templates/CLAUDE.md.setup") is True

    def test_devenv_nix(self):
        """Should identify devenv.nix as key file."""
        assert is_key_file("devenv.nix") is True
        assert is_key_file("./devenv.nix") is True

    def test_agents_directory(self):
        """Should identify files in agents/ as key files."""
        assert is_key_file("agents/alto-backend.md") is True
        assert is_key_file("agents/alto-frontend.md") is True
        assert is_key_file("./agents/new-agent.md") is True

    def test_hooks_directory(self):
        """Should identify files in hooks/ as key files."""
        assert is_key_file("hooks/session-start.py") is True
        assert is_key_file("hooks/arbiter-scheduler.py") is True
        assert is_key_file("./hooks/new-hook.py") is True

    def test_skills_directory(self):
        """Should identify files in skills/ as key files."""
        assert is_key_file("skills/scope-discipline/SKILL.md") is True
        assert is_key_file(".claude/skills/test/SKILL.md") is True

    def test_architecture_md(self):
        """Should identify ARCHITECTURE.md as key file."""
        assert is_key_file("ARCHITECTURE.md") is True
        assert is_key_file("./ARCHITECTURE.md") is True

    def test_readme_md(self):
        """Should identify README.md as key file."""
        assert is_key_file("README.md") is True
        assert is_key_file("./README.md") is True

    def test_non_key_files(self):
        """Should return False for non-key files."""
        assert is_key_file("src/main.py") is False
        assert is_key_file("package.json") is False
        assert is_key_file("tests/test_main.py") is False
        assert is_key_file("docs/guide.md") is False

    def test_changelog_itself(self):
        """CHANGELOG.md itself is not a key file (it's the required file)."""
        assert is_key_file("CHANGELOG.md") is False

    def test_partial_matches(self):
        """Should match partial paths containing key patterns."""
        assert is_key_file("some/path/agents/test.md") is True
        assert is_key_file("nested/hooks/hook.py") is True
        assert is_key_file("deep/nested/skills/skill.md") is True

    def test_similar_but_different_names(self):
        """Should not match similar but different names."""
        # The function uses substring matching, so 'agents/' in 'my_agents/' matches
        # These don't contain any of the key patterns
        assert is_key_file("src/myfile.py") is False
        assert is_key_file("webhook.py") is False  # no 'hooks/' pattern
        assert is_key_file("lib/utils.ts") is False
