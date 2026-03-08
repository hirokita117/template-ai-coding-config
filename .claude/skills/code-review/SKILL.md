---
name: code-review
description: Perform automated code review on staged changes or branch diffs. Use when the user requests a code review, asks to review their changes, or invokes /code-review. Analyzes diffs for correctness, security, performance, maintainability, test coverage, and type safety issues. Adapts to the project's tech stack and conventions automatically.
---

# Code Review

Perform structured code review on git diffs, adapting to the project's tech stack and conventions.

## Workflow

### Step 1: Detect Diff

Determine what to review:

```bash
# Check for staged changes first
STAGED=$(git diff --cached --name-only)
if [ -n "$STAGED" ]; then
  # Use staged changes
  DIFF_CMD="git diff --cached"
else
  # Find base branch and diff against it
  BASE=$(git merge-base main HEAD 2>/dev/null || git merge-base master HEAD 2>/dev/null)
  DIFF_CMD="git diff $BASE...HEAD"
fi
```

If no diff is found, inform the user and stop.

### Step 2: Collect Context

Run the context detection script to identify the project's tech stack:

```bash
bash .claude/skills/code-review/scripts/detect_context.sh
```

Parse the output to determine which checklists to apply. Also check for and read `CLAUDE.md` if `HAS_CLAUDE_MD=true` — project-specific conventions override generic best practices.

### Step 3: Select Checklists

Based on context detection results, read the relevant reference files from `.claude/skills/code-review/references/`:

| Condition | Files to Load |
|-----------|---------------|
| Always | `correctness.md`, `maintainability.md` |
| `HAS_BACKEND=true` | `security.md`, `performance.md` |
| `HAS_FRONTEND=true` | `performance.md` |
| `HAS_TYPED_LANG=true` | `type-safety.md` |
| `HAS_TESTS=true` | `test-coverage.md` |
| `HAS_SECURITY_SENSITIVE=true` | `security.md` |

### Step 4: Review

1. Get the full diff with context: run the appropriate `git diff` command with `-U5` for surrounding context
2. For each changed file, read additional surrounding context if needed to understand the change
3. Apply each loaded checklist against the changed lines and their context
4. For large diffs, prioritize review order:
   - Security-sensitive files (auth, credentials, tokens)
   - Business logic (controllers, services, domain models)
   - Tests
   - Configuration and generated files (lowest priority)

### Step 5: Generate Report

Output the review as structured Markdown using this format:

```markdown
# Code Review Report

## Summary
| Severity | Count |
|----------|-------|
| Critical | N     |
| Warning  | N     |
| Suggestion | N   |
| Nit      | N     |

**Files reviewed**: list of reviewed files
**Tech stack detected**: detected languages and frameworks
**Checklists applied**: list of applied checklists

## Critical
### [CR-1] Short title
- **File**: `path/to/file.ts:42`
- **Category**: Security / Correctness / Performance / ...
- **Description**: Explanation of the issue
- **Suggestion**:
\`\`\`diff
- problematic code
+ suggested fix
\`\`\`

## Warnings
### [WR-1] Short title
(same format as Critical)

## Suggestions
### [SG-1] Short title
(same format)

## Nits
### [NT-1] Short title
(same format)
```

Omit severity sections that have no findings. If no issues found at all, output a brief "No issues found" summary.

## Severity Definitions

- **Critical**: Bugs, security vulnerabilities, data loss risk — must fix before merge
- **Warning**: Potential issues under certain conditions — recommended to fix
- **Suggestion**: Code quality and readability improvements — desirable to fix
- **Nit**: Style, naming preferences — optional

## Review Guidelines

- Review ONLY changed lines and their direct context — do not review unchanged code
- ALWAYS include file path and line number for each finding
- When uncertain, classify as Suggestion or lower (minimize false positives)
- CLAUDE.md conventions take priority over generic best practices
- If linter/formatter configs are detected (`HAS_LINTER=true`), skip style issues that those tools would catch
- For large diffs, focus on high-risk areas first and note if review was partial
- Each finding must be actionable — include a concrete suggestion for how to fix
- Do not flag issues that are clearly intentional design decisions
- Use the project's language for descriptions (follow CLAUDE.md language settings if present, otherwise default to Japanese)
