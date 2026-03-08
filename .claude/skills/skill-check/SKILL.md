---
name: skill-check
description: Diagnose a skill folder for best practices compliance based on the Agent Skills specification. Use when user says "check my skill", "validate this skill", "review skill quality", "skill lint", or wants to verify a SKILL.md follows naming, frontmatter, description, progressive disclosure, security, and structural best practices. Do NOT use for creating or editing skills (use skill-creator instead).
disable-model-invocation: true
allowed-tools: Bash(python *)
argument-hint: "[path-to-skill-folder]"
---

# Skill Best Practices Compliance Checker

Validate a skill folder against documented best practices from:
- Agent Skills API documentation
- Claude Code skill documentation
- The Complete Guide to Building Skills for Claude

## Usage

### When a path is provided (`/skill-check path/to/my-skill`)

Run the checker script directly on the specified folder:

```bash
python ~/.claude/skills/skill-check/scripts/check_skill.py $ARGUMENTS
```

### When no argument is provided (`/skill-check`)

Do NOT default to the current directory. Instead, discover available skills and let the user choose:

1. List skill directories by running:
   ```bash
   python ~/.claude/skills/skill-check/scripts/list_skills.py
   ```
2. Show the user the discovered skills and ask which one to check.
   - If only one skill is found, confirm with the user and proceed.
   - If no skills are found, tell the user and ask them to provide a path explicitly.
3. After the user picks a skill, run the checker on that path:
   ```bash
   python ~/.claude/skills/skill-check/scripts/check_skill.py <chosen-skill-path>
   ```

The script exits with code 0 if no CRITICAL issues found, or 1 if there are CRITICAL issues.

## What it checks

The script performs deterministic checks across these categories:

**Folder Structure** — SKILL.md exists with exact casing, folder is kebab-case, no README.md inside skill folder.

**YAML Frontmatter** — Required fields (name, description) present; name is kebab-case ≤64 chars with no reserved words; description ≤1024 chars with no XML brackets; only allowed keys used; optional fields have correct types.

**Description Quality** — Contains both WHAT (what the skill does) and WHEN (trigger conditions); not too vague or too short; includes actionable verbs or trigger phrases.

**Instructions Quality** — Body uses imperative language; instructions are specific and actionable rather than vague.

**Progressive Disclosure** — SKILL.md body size is reasonable (<500 lines ideal); large content should be in references/ files.

**Error Handling** — Presence of troubleshooting or error handling section.

**Support Files** — Bundled files are referenced from SKILL.md so Claude knows when to load them.

**Security** — No XML brackets in frontmatter; scripts audited for suspicious patterns.

**Context Fork Consistency** — If `context: fork` is set, the skill has actionable task instructions, not just reference content.

## Interpreting results

Findings are classified into three severity levels:

- **CRITICAL** — Must fix. The skill will not function correctly or violates hard constraints (missing SKILL.md, invalid name, missing required fields, security violations).
- **WARNING** — Should fix. The skill may work but is likely to undertrigger, overtrigger, or produce inconsistent results (vague description, unreferenced files, oversized body).
- **SUGGESTION** — Nice to have. Improvements that raise quality (add examples, add troubleshooting section, use imperative language).

## After running

After the script produces its report, review the findings and help the user understand what to fix. For each finding:

1. Explain why it matters (refer to the best practice behind it)
2. Provide the specific fix from the report
3. If the user asks, make the fixes directly

For CRITICAL issues, fix them first — the skill won't work correctly otherwise.
For WARNING issues, prioritize description quality and unreferenced files.
For SUGGESTION issues, recommend but don't insist.
