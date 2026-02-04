# Claude Code > Output Styles

> Custom behavior via `.claude/output-styles/`.

## Directory Structure

```
~/.claude/output-styles/           # User scope (personal)
├── technical-writer.md
├── research-assistant.md
└── tutor-mode.md

.claude/output-styles/             # Project scope (team)
├── security-auditor.md
└── domain-expert.md
```

## Scope Locations

| Location | Scope | Shared |
|----------|-------|--------|
| `.claude/output-styles/` | Project (team) | Yes (committed) |
| `~/.claude/output-styles/` | User (personal) | No |

---

## Built-in Styles

| Style | Purpose | Best For |
|-------|---------|----------|
| **Default** | Standard software engineering mode | Code changes, testing, deployment |
| **Explanatory** | Educational mode with insights | Learning how code works |
| **Learning** | Interactive teaching mode | Hands-on skill building |

### Default
Standard Claude Code behavior optimized for efficient software engineering.

### Explanatory
Provides educational "Insights" between code modifications, explaining implementation choices and codebase patterns.

### Learning
Goes further than Explanatory:
- Shares insights about the code
- Asks you to contribute small code pieces
- Marks code with `TODO(human)` for you to implement
- Teaches by guiding while you implement

---

## File Format

```markdown
---
name: Display Name
description: Brief description shown in /output-style menu
keep-coding-instructions: false
---

# Style Instructions

Your custom instructions here...
```

---

## Frontmatter Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | String | Filename | Display name in UI |
| `description` | String | None | Shown in `/output-style` menu |
| `keep-coding-instructions` | Boolean | `false` | Retain default coding instructions |

### `keep-coding-instructions`

- **`false`** (default): Removes all software engineering instructions. Use for non-coding tasks.
- **`true`**: Keeps coding instructions while adding your custom behavior. Use for specialized coding modes.

---

## How to Use

### Interactive Menu

```bash
/output-style
```

Opens a menu showing all available styles.

### Direct Activation

```bash
/output-style style-name
```

Examples:
```bash
/output-style explanatory
/output-style learning
/output-style technical-writer
```

### Via Settings

```json
{
  "outputStyle": "style-name"
}
```

### Persistence

Changes are saved to `.claude/settings.local.json` (personal, not committed).

---

## Examples

### Technical Writer

```markdown
---
name: Technical Writer
description: Adapt Claude for technical documentation and API writing
keep-coding-instructions: false
---

# Technical Writer Mode

You are a technical writer specializing in clear, precise documentation.

## Core Behaviors

- Use precise, industry-standard terminology
- Structure information hierarchically
- Provide complete examples with expected outputs
- Include prerequisites and dependencies
- Highlight warnings and edge cases

## Response Format

- Lead with a brief overview
- Use numbered lists for sequential steps
- Use bullets for alternatives
- Include "Before you begin" sections
- Add "Related topics" at the end

## Tone

- Professional and authoritative
- Clear and accessible
- Define technical terms on first use
- Use active voice
- Be concise while remaining complete
```

### Security Auditor (with coding)

```markdown
---
name: Security Auditor
description: Specialized mode for security reviews and vulnerability analysis
keep-coding-instructions: true
---

# Security Auditor Mode

You are a security-focused code auditor. You maintain coding abilities while prioritizing security.

## Audit Methodology

- Check OWASP Top 10, CWE-25 vulnerabilities
- Assess authentication/authorization
- Evaluate encryption practices
- Review input validation
- Check for hardcoded secrets
- Assess dependency risks

## Assessment Framework

- Severity: Critical, High, Medium, Low, Informational
- CVSS scoring when applicable
- Risk = likelihood × impact
- Specific remediation guidance
- Testing recommendations
```

### Research Assistant

```markdown
---
name: Research Assistant
description: Adapt Claude for research and analysis tasks
keep-coding-instructions: false
---

# Research Assistant Mode

You are a research assistant for academic or professional research projects.

## Responsibilities

- Systematically gather and organize information
- Critically evaluate source quality
- Identify patterns, gaps, and contradictions
- Synthesize findings into coherent insights
- Document sources and methodologies

## Output Standards

- Include citations
- Evidence-based conclusions
- Distinguish findings from interpretation
- Flag information needing verification
- Recommend further research
```

### Tutor Mode

```markdown
---
name: Tutor
description: Interactive learning mode that guides rather than gives answers
keep-coding-instructions: true
---

# Tutor Mode

You are an educational tutor helping users learn by doing.

## Teaching Approach

- Guide discovery rather than providing answers
- Ask leading questions
- Break problems into smaller steps
- Celebrate progress and correct gently
- Adapt to the learner's level

## Code Assistance

When helping with code:
- Mark sections for the user to complete: `// TODO(human): implement this`
- Provide scaffolding, not complete solutions
- Ask "What do you think should go here?"
- Review their attempts constructively
```

---

## Output Styles vs Other Features

| Feature | Purpose | System Prompt Impact |
|---------|---------|---------------------|
| **Output Styles** | Change fundamental behavior | **Replaces** default prompt |
| **CLAUDE.md** | Add project context | Adds as user context |
| **`--append-system-prompt`** | Temporary additions | Appends to prompt |
| **Agents** | Delegate specific tasks | Custom per agent |
| **Commands** | Quick actions | No impact |

---

## When to Use Each

| Scenario | Use |
|----------|-----|
| Change Claude's fundamental role | Output Styles |
| Add project-specific context | CLAUDE.md |
| One-time temporary instructions | `--append-system-prompt` |
| Delegate specialized tasks | Agents |
| Quick reusable prompts | Commands |

---

## Creating Custom Styles

### Step 1: Choose Scope

- **User** (`~/.claude/output-styles/`): Personal, all projects
- **Project** (`.claude/output-styles/`): Team-shared, this project

### Step 2: Create File

```bash
mkdir -p .claude/output-styles
cat > .claude/output-styles/my-style.md << 'EOF'
---
name: My Custom Style
description: What this style does
keep-coding-instructions: false
---

# Instructions

Your custom behavior instructions here...
EOF
```

### Step 3: Test

```bash
/output-style my-style
```

---

## Best Practices

1. **Be specific**: Vague instructions get ignored
2. **Define behaviors**: Explicit tone, format, approach
3. **Include examples**: Show expected output patterns
4. **Test thoroughly**: Try multiple prompts
5. **Use clear names**: Indicate purpose in filename
6. **Add descriptions**: Help others understand the style

---

## Related

- [memory.md](memory.md) - CLAUDE.md for project context
- [agents.md](agents.md) - Delegated specialists
- [settings.md](settings.md) - Style configuration
