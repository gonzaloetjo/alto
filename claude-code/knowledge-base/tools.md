# Claude Code > Tools

> Built-in tools available to Claude Code.

## Core Tools

| Tool | Purpose | Typical Use |
|------|---------|-------------|
| `Read` | Read file contents | Examine code, config, docs |
| `Write` | Create/overwrite files | New files, full replacements |
| `Edit` | Modify file sections | Targeted changes, refactoring |
| `Glob` | Find files by pattern | `**/*.ts`, `src/**/*.py` |
| `Grep` | Search file contents | Find patterns, usages |
| `Bash` | Execute shell commands | Git, npm, build tools |
| `Task` | Spawn subagent | Delegate to specialists |
| `WebFetch` | Fetch URL content | Documentation, APIs |
| `WebSearch` | Search the web | Current information |

## Read-Only Tools

| Tool | Description |
|------|-------------|
| `Read` | Read file contents (supports images, PDFs, notebooks) |
| `Glob` | Match files by glob pattern |
| `Grep` | Search with regex (ripgrep-based) |

## Modification Tools

| Tool | Description |
|------|-------------|
| `Write` | Create new files or overwrite existing |
| `Edit` | Replace specific text in files |
| `NotebookEdit` | Edit Jupyter notebook cells |

## Execution Tools

| Tool | Description |
|------|-------------|
| `Bash` | Execute shell commands with timeout |
| `Task` | Spawn isolated subagent for complex tasks |

## Network Tools

| Tool | Description |
|------|-------------|
| `WebFetch` | Fetch and process web content |
| `WebSearch` | Search the web for information |

## Interaction Tools

| Tool | Description |
|------|-------------|
| `AskUserQuestion` | Present choices to user |
| `EnterPlanMode` | Switch to read-only planning |
| `ExitPlanMode` | Signal plan completion |

---

## Tool Details

### Read

Reads file contents with line numbers.

```
Read(file_path, offset?, limit?)
```

| Parameter | Description |
|-----------|-------------|
| `file_path` | Absolute path to file |
| `offset` | Line number to start (optional) |
| `limit` | Number of lines to read (optional) |

**Supports**: Code, text, images (PNG, JPG), PDFs, Jupyter notebooks (.ipynb)

### Write

Creates or overwrites a file completely.

```
Write(file_path, content)
```

**Note**: Prefer `Edit` for modifications to existing files.

### Edit

Replaces specific text in a file.

```
Edit(file_path, old_string, new_string, replace_all?)
```

| Parameter | Description |
|-----------|-------------|
| `file_path` | Absolute path to file |
| `old_string` | Text to find and replace |
| `new_string` | Replacement text |
| `replace_all` | Replace all occurrences (default: false) |

**Note**: `old_string` must be unique in the file, or use `replace_all: true`.

### Glob

Finds files matching a glob pattern.

```
Glob(pattern, path?)
```

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files |
| `src/**/*.py` | Python files in src/ |
| `*.md` | Markdown in current dir |
| `{src,lib}/**` | Files in src/ or lib/ |

### Grep

Searches file contents with regex.

```
Grep(pattern, path?, glob?, output_mode?)
```

| Parameter | Description |
|-----------|-------------|
| `pattern` | Regex pattern to search |
| `path` | Directory to search (default: cwd) |
| `glob` | Filter files by glob |
| `output_mode` | `content`, `files_with_matches`, `count` |

**Context options**: `-A` (after), `-B` (before), `-C` (around)

### Bash

Executes shell commands.

```
Bash(command, description?, timeout?, run_in_background?)
```

| Parameter | Description |
|-----------|-------------|
| `command` | Shell command to execute |
| `description` | What the command does |
| `timeout` | Max milliseconds (default: 120000) |
| `run_in_background` | Run async (default: false) |

**Note**: Use dedicated tools (Read, Edit, Grep) instead of shell equivalents.

### Task

Spawns an isolated subagent.

```
Task(prompt, subagent_type, description, model?, run_in_background?)
```

| Parameter | Description |
|-----------|-------------|
| `prompt` | Instructions for the subagent |
| `subagent_type` | Agent type (e.g., `Explore`, `Plan`) |
| `description` | Short description (3-5 words) |
| `model` | `sonnet`, `opus`, `haiku` |
| `run_in_background` | Run async |

### AskUserQuestion

Presents choices to the user.

```
AskUserQuestion(questions)
```

Each question has:
- `question`: The question text
- `header`: Short label (max 12 chars)
- `options`: 2-4 choices with label and description
- `multiSelect`: Allow multiple selections

---

## Tool Availability by Mode

| Tool | Default | Plan Mode | Sandboxed |
|------|---------|-----------|-----------|
| Read | Yes | Yes | Yes |
| Glob | Yes | Yes | Yes |
| Grep | Yes | Yes | Yes |
| Edit | Yes | **No** | Yes |
| Write | Yes | **No** | Yes |
| Bash | Yes | **No** | Restricted |
| WebFetch | Yes | **No** | Depends |
| WebSearch | Yes | **No** | Depends |
| Task | Yes | Yes | Yes |
| AskUserQuestion | Yes | Yes | Yes |

---

## Permission Patterns

Control tool access in `settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm:*)",
      "Read(./src/**)",
      "Edit(./src/**/*.ts)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Read(.env*)"
    ]
  }
}
```

| Pattern | Matches |
|---------|---------|
| `Tool` | All uses of the tool |
| `Tool(pattern)` | Uses matching pattern |
| `Tool(prefix:*)` | Uses starting with prefix |
| `Tool(./path/**)` | Path glob patterns |

---

## Related

- [settings.md](settings.md) - Permission configuration
- [permissions.md](permissions.md) - Permission modes
- [hooks.md](hooks.md) - Intercept tool calls
