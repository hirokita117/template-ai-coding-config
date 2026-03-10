---
name: skill-check
description: Diagnose a skill folder for best practices compliance based on the Agent Skills specification. Use when user says "check my skill", "validate this skill", "review skill quality", "skill lint", or wants to verify a SKILL.md follows naming, frontmatter, description, progressive disclosure, security, and structural best practices. Do NOT use for creating or editing skills (use skill-creator instead).
disable-model-invocation: true
allowed-tools: Bash(python *)
argument-hint: "[path-to-skill-folder]"
---

# Skill Best Practices Compliance Checker

Diagnose a skill folder in two phases. Phase 1 runs a deterministic script for structural validation. Phase 2 is a qualitative review that you perform yourself by reading the skill content. Both phases must be completed before the check is considered done.

## Skill selection

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

## Phase 1: Quantitative check (script execution)

The script performs deterministic checks across these categories:

- **Folder Structure**
  - SKILL.md exists with exact casing, folder is kebab-case, no README.md inside skill folder.
- **YAML Frontmatter**
  — Required fields (name, description) present; name is kebab-case ≤64 chars with no reserved words; description ≤1024 chars with no XML brackets; only allowed keys used; optional fields have correct types.
- **Description Quality**
  — Contains both WHAT (what the skill does) and WHEN (trigger conditions); not too vague or too short; includes actionable verbs or trigger phrases.
- **Instructions Quality**
  — Body uses imperative language; instructions are specific and actionable rather than vague.
- **Progressive Disclosure**
  — SKILL.md body size is reasonable (<500 lines ideal); large content should be in references/ files.
- **Error Handling**
  — Presence of troubleshooting or error handling section.
- **Support Files**
  — Bundled files are referenced from SKILL.md.
- **Security**
  — No XML brackets in frontmatter; scripts audited for suspicious patterns.
- **Context Fork Consistency**
  — If `context: fork` is set, the skill has actionable task instructions, not just reference content.

Proceed to Phase 2 even if Phase 1 finds CRITICAL issues (the intent of the skill can still be understood even if the format is broken). However, prepend a note at the top of the Phase 2 report: "Phase 1 found critical errors — fix those first."

## Phase 2: Qualitative review

After Phase 1, read the target skill's SKILL.md and all support files. Review the skill across the following 6 dimensions. Rate each dimension as 🟢 Good / 🟡 Improvable / 🔴 Problem, and provide reasoning and specific improvement suggestions.

### Dimension 1: Trigger accuracy

Read the description and evaluate:

- **Overtrigger risk**: Is the description broad enough to match queries this skill should not handle? Does it overlap with common skills (docx, xlsx, pdf, frontend-design, skill-creator, etc.)?

When suggesting improvements, provide a complete rewritten description.

### Dimension 2: Description-body alignment

Check whether the capabilities advertised in the description are actually covered by the body instructions:

- Are there features mentioned in the description that have no corresponding instructions in the body?
- Are there capabilities in the body that are not mentioned in the description?

### Dimension 3: Workflow completeness

Evaluate the workflows described in the body:

- Are step dependencies explicit? (e.g., if Step 2 relies on Step 1's output, is that stated?)
- Are edge cases considered? (empty input, missing files, API errors, etc.)
- Are termination conditions clear? If iterative loops exist, is the exit condition specified?
- Are confirmation points placed before side-effecting operations (deployments, deletions, external API calls)?

### Dimension 4: Instruction specificity and executability

Assess whether each instruction is unambiguously executable:

- If scripts are referenced, do they actually exist in the skill bundle? Are their arguments documented?
- If MCP tool calls are instructed, are tool names, parameters, and expected return values specified?

### Dimension 5: Progressive Disclosure design quality

Beyond the formal size check in Phase 1, evaluate the information hierarchy:

- Do support file references include guidance on WHEN to read them? A bare link is insufficient. Check for conditional guidance like "For form filling, see FORMS.md" rather than just "See FORMS.md".
- Are there deterministic processes written as prose instructions that should be scripts instead? (Scripts are more token-efficient and reliable.)

### Dimension 6: Practical robustness

Imagine the skill being used in real scenarios:

- Are frontmatter options (allowed-tools, context, disable-model-invocation) appropriate for the skill's nature? (e.g., a skill with side effects should have `disable-model-invocation: true`)
- Are there security concerns? (external URL access, user data handling, etc.)

---

## Final report

Combine Phase 1 and Phase 2 results into a single report with this structure:

```
📋 Skill Diagnostic Report: <skill-name>

━━ Phase 1: Quantitative Check ━━
CRITICAL: N / WARNING: N / SUGGESTION: N
(Summary of script output. Refer to script output for details)

━━ Phase 2: Qualitative Review ━━
1. Trigger accuracy:          🟢/🟡/🔴  (one-line summary)
2. Description-body alignment: 🟢/🟡/🔴  (one-line summary)
3. Workflow completeness:      🟢/🟡/🔴  (one-line summary)
4. Instruction specificity:    🟢/🟡/🔴  (one-line summary)
5. Progressive Disclosure:     🟢/🟡/🔴  (one-line summary)
6. Practical robustness:       🟢/🟡/🔴  (one-line summary)

━━ Priority Improvement Actions ━━
(Prioritize Phase 1 CRITICAL + Phase 2 🔴 items first.
 List up to 5 concrete fix steps in priority order.)
```

Every improvement action must include a specific "what to change and how" proposal. For description rewrites, provide the complete replacement text. For instruction additions, show the exact text to insert and where.

If the user wants, apply the fixes on the spot.
