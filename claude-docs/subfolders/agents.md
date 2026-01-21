# Claude Code Custom Agents (`.claude/agents/`)

Agents are specialized AI assistants that Claude delegates tasks to. They have isolated contexts, specific tool access, and focused personas for particular domains.

## Directory Structure

```
.claude/agents/
├── code-reviewer.md
├── debugger.md
├── security-auditor.md
├── data-analyst.md
└── db-reader.md
```

## Scope Locations

| Location | Priority | Scope | Shared |
|----------|----------|-------|--------|
| CLI flag | 1 (highest) | Session | No |
| `.claude/agents/` | 2 | Project | Yes (git) |
| `~/.claude/agents/` | 3 | User | No |
| Plugins | 4 (lowest) | Plugin | Via plugin |

## Agent File Format

### Basic Agent

```markdown
---
name: code-reviewer
description: Expert code review specialist. Reviews code for quality, security, and maintainability.
---

You are a senior code reviewer with expertise in identifying:
- Logic errors and bugs
- Security vulnerabilities
- Performance issues
- Code style violations
- Missing test coverage

Provide constructive, actionable feedback.
```

### Full-Featured Agent

```yaml
---
name: security-auditor
description: Security specialist for vulnerability assessment and secure coding guidance
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
model: opus
permissionMode: default
skills: security-audit, dependency-check
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly.sh"
---

You are a security auditor specializing in application security.

## Expertise

- OWASP Top 10 vulnerabilities
- Secure coding practices
- Authentication and authorization
- Cryptography best practices
- Dependency security

## Approach

1. Identify potential vulnerabilities
2. Assess severity and impact
3. Provide specific remediation steps
4. Reference security standards (CWE, CVE)

## Output Format

For each finding:
- **Severity**: Critical/High/Medium/Low
- **Location**: File and line number
- **Description**: What the issue is
- **Impact**: What could happen
- **Remediation**: How to fix it
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase, hyphens) |
| `description` | Yes | When Claude should delegate to this agent |
| `tools` | No | Allowed tools (inherits all if omitted) |
| `disallowedTools` | No | Tools to explicitly deny |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | No | See permission modes below |
| `skills` | No | Skills to load (comma-separated names) |
| `hooks` | No | PreToolUse/PostToolUse hooks |

## Permission Modes

| Mode | Description |
|------|-------------|
| `default` | Normal permission prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Minimal prompts (still asks for dangerous ops) |
| `bypassPermissions` | Skip all prompts (use carefully) |
| `plan` | Plan mode - research only, no edits |

## Tool Restrictions

### Allow Specific Tools

```yaml
---
name: reader-only
tools: Read, Grep, Glob
---
```

This agent can ONLY use Read, Grep, and Glob.

### Deny Specific Tools

```yaml
---
name: no-write-agent
disallowedTools: Write, Edit, Bash
---
```

This agent inherits all tools EXCEPT Write, Edit, and Bash.

### Combined Restrictions

```yaml
---
name: safe-bash-agent
tools: Read, Grep, Glob, Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-safe-commands.sh"
---
```

## Examples

### Read-Only Code Reviewer

```markdown
# .claude/agents/code-reviewer.md

---
name: code-reviewer
description: Reviews code for quality issues without making changes
tools: Read, Grep, Glob
model: sonnet
---

You are a code reviewer. Analyze code for:

1. **Correctness**: Logic errors, edge cases, race conditions
2. **Security**: Injection, XSS, authentication issues
3. **Performance**: N+1 queries, memory leaks, inefficient algorithms
4. **Maintainability**: Complexity, naming, documentation
5. **Testing**: Coverage gaps, test quality

## Output Format

### Summary
Brief overview of code quality.

### Issues Found
| Severity | Location | Issue | Suggestion |
|----------|----------|-------|------------|
| High | file:line | Description | Fix |

### Recommendations
Prioritized list of improvements.
```

### Debugger Agent

```markdown
# .claude/agents/debugger.md

---
name: debugger
description: Investigates bugs, analyzes stack traces, and identifies root causes
tools: Read, Grep, Glob, Bash
model: opus
---

You are a debugging specialist. Your approach:

## Investigation Process

1. **Reproduce**: Understand how to trigger the issue
2. **Isolate**: Narrow down the problem area
3. **Trace**: Follow the execution path
4. **Identify**: Find the root cause
5. **Verify**: Confirm the cause explains all symptoms

## Techniques

- Stack trace analysis
- Log examination
- State inspection
- Binary search through commits
- Minimal reproduction cases

## Output

Provide:
- Root cause explanation
- Evidence supporting conclusion
- Suggested fix with code
- Prevention recommendations
```

### Database Reader (Safe SQL)

```markdown
# .claude/agents/db-reader.md

---
name: db-reader
description: Executes read-only database queries for analysis and reporting
tools: Bash
permissionMode: default
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-sql.sh"
---

You are a database analyst. You can execute READ-ONLY queries.

## Restrictions

- SELECT queries only
- No INSERT, UPDATE, DELETE, DROP, ALTER
- No transaction modifications
- No schema changes

## Query Guidelines

- Always use explicit column names (not SELECT *)
- Include LIMIT clauses for large tables
- Use EXPLAIN for query optimization
- Format results clearly

## Output Format

```
Query: [the SQL query]
Results: [formatted table]
Analysis: [interpretation of results]
```
```

### Security Auditor

```markdown
# .claude/agents/security-auditor.md

---
name: security-auditor
description: Performs security audits and vulnerability assessments
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
model: opus
skills: security-audit
---

You are a security auditor specializing in application security.

## Audit Scope

1. **Code Review**: Static analysis for vulnerabilities
2. **Dependencies**: Known CVEs in packages
3. **Configuration**: Security misconfigurations
4. **Authentication**: Auth/authz weaknesses
5. **Data Handling**: Sensitive data exposure

## Severity Levels

- **CRITICAL**: Immediate exploitation possible
- **HIGH**: Significant risk, fix before release
- **MEDIUM**: Moderate risk, plan remediation
- **LOW**: Minor issues, best practice improvements

## Report Format

### Executive Summary
High-level findings overview.

### Detailed Findings
For each issue:
- CWE/CVE reference
- Location and evidence
- Impact assessment
- Remediation steps

### Recommendations
Prioritized security improvements.
```

### Data Analyst

```markdown
# .claude/agents/data-analyst.md

---
name: data-analyst
description: Analyzes data, generates reports, and creates visualizations
tools: Read, Bash, Write
model: sonnet
---

You are a data analyst. Your capabilities:

## Analysis Types

- Exploratory data analysis
- Statistical summaries
- Trend identification
- Anomaly detection
- Correlation analysis

## Tools

- Python (pandas, numpy, matplotlib)
- SQL queries
- CSV/JSON processing
- Report generation

## Output Guidelines

- Present findings clearly
- Include relevant visualizations
- Provide statistical context
- Note data quality issues
- Suggest further analysis
```

### Parallel Researcher

```markdown
# .claude/agents/researcher.md

---
name: researcher
description: Researches topics using web search and documentation
tools: WebSearch, WebFetch, Read, Grep, Glob
model: haiku
permissionMode: dontAsk
---

You are a research assistant. Gather information efficiently.

## Research Process

1. Search for relevant sources
2. Fetch and analyze content
3. Cross-reference information
4. Synthesize findings

## Output Format

### Topic: [subject]

**Summary**: Brief overview

**Key Findings**:
- Finding 1
- Finding 2

**Sources**:
- [Title](URL)

**Further Reading**:
- Related topics to explore
```

## Agent Delegation

Claude automatically delegates to agents when:
- Task matches agent description
- Agent has required specialized tools
- Context suggests agent expertise needed

You can also explicitly invoke: "Use the code-reviewer agent to review this PR"

## Agents vs Skills vs Commands

| Aspect | Agents | Skills | Commands |
|--------|--------|--------|----------|
| **Context** | Always isolated | Optional (`context: fork`) | Main conversation |
| **Persona** | Specialized AI | Capability set | Prompt template |
| **Tools** | Configurable | Configurable | Configurable |
| **Invocation** | Auto-delegation | Auto + explicit | Explicit only |
| **Best for** | Specialized tasks | Reusable workflows | Quick prompts |

## Hooks in Agents

```yaml
---
name: safe-executor
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "./scripts/lint-file.sh"
---
```

## Best Practices

1. **Clear specialization**: Each agent should have a distinct purpose
2. **Minimal tools**: Only grant tools the agent needs
3. **Descriptive names**: Make purpose obvious from name
4. **Rich descriptions**: Help Claude know when to delegate
5. **Safety first**: Use hooks to validate dangerous operations
6. **Test delegation**: Verify Claude delegates appropriately

## Troubleshooting

**Agent not being used:**
- Check description matches task type
- Verify agent file is valid YAML/Markdown
- Ensure no syntax errors in frontmatter

**Agent has wrong permissions:**
- Check `tools` and `disallowedTools` fields
- Verify permission inheritance
- Check `permissionMode` setting

**Agent behaves unexpectedly:**
- Review the system prompt (content after frontmatter)
- Check if skills are loaded correctly
- Verify model setting is appropriate
