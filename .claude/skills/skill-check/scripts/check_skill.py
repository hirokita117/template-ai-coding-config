#!/usr/bin/env python3
"""
Skill Best Practices Compliance Checker

Scans a skill folder and validates it against documented best practices
from the Agent Skills specification, Claude Code skill docs, and
The Complete Guide to Building Skills for Claude.

Outputs a structured report with CRITICAL / WARNING / SUGGESTION severity levels.
"""

import sys
import os
import re
import json
import textwrap
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


# ─── Constants ───────────────────────────────────────────────────────────────

ALLOWED_FRONTMATTER_KEYS = {
    "name", "description", "license", "allowed-tools", "metadata",
    "compatibility",
    # Claude Code extensions
    "argument-hint", "disable-model-invocation", "user-invocable",
    "model", "context", "agent", "hooks",
}

RESERVED_NAME_FRAGMENTS = ["anthropic", "claude"]

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING  = "WARNING"
SEVERITY_SUGGEST  = "SUGGESTION"

SEVERITY_ICON = {
    SEVERITY_CRITICAL: "❌",
    SEVERITY_WARNING:  "⚠️",
    SEVERITY_SUGGEST:  "💡",
}

SEVERITY_ORDER = {
    SEVERITY_CRITICAL: 0,
    SEVERITY_WARNING:  1,
    SEVERITY_SUGGEST:  2,
}

# Rough thresholds
SKILL_MD_WARN_LINES  = 500
SKILL_MD_LARGE_LINES = 800
SKILL_MD_WARN_WORDS  = 5000
DESCRIPTION_VAGUE_PATTERNS = [
    r"^helps?\s+with\b",
    r"^does?\s+things?\b",
    r"^useful\s+for\b",
    r"^manages?\s+stuff\b",
    r"^processes?\s+documents?\s*\.?$",
    r"^handles?\s+tasks?\b",
]

WHEN_TRIGGER_KEYWORDS = [
    "use when", "trigger when", "use for", "use if",
    "use this when", "activate when", "invoke when",
    "when user", "when the user", "do not use for",
]

# Non-English character detection
# CJK ranges
_CJK_RANGES = (
    r'\u3040-\u309F'   # Hiragana
    r'\u30A0-\u30FF'   # Katakana
    r'\u4E00-\u9FFF'   # CJK Unified Ideographs
    r'\u3400-\u4DBF'   # CJK Extension A
    r'\uF900-\uFAFF'   # CJK Compatibility Ideographs
)
# Broader non-ASCII letter ranges (covers Cyrillic, Arabic, Thai, Devanagari, Korean Hangul, etc.)
_NON_ENGLISH_RE = re.compile(
    r'[' + _CJK_RANGES +
    r'\u0400-\u04FF'     # Cyrillic
    r'\u0600-\u06FF'     # Arabic
    r'\u0E00-\u0E7F'     # Thai
    r'\u0900-\u097F'     # Devanagari
    r'\uAC00-\uD7AF'     # Hangul Syllables
    r'\u1100-\u11FF'     # Hangul Jamo
    r']'
)


def contains_non_english(text: str) -> bool:
    """Return True if text contains non-English script characters."""
    return bool(_NON_ENGLISH_RE.search(text))


# ─── Finding dataclass ──────────────────────────────────────────────────────

class Finding:
    def __init__(self, severity, category, message, fix=None):
        self.severity = severity
        self.category = category
        self.message = message
        self.fix = fix

    def to_dict(self):
        d = {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
        }
        if self.fix:
            d["fix"] = self.fix
        return d


# ─── Checker ─────────────────────────────────────────────────────────────────

class SkillChecker:
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path.resolve()
        self.findings: list[Finding] = []
        self.frontmatter: dict = {}
        self.body: str = ""
        self.raw_content: str = ""
        self.all_files: list[Path] = []

    # ── helpers ──

    def add(self, severity, category, message, fix=None):
        self.findings.append(Finding(severity, category, message, fix))

    def _collect_files(self):
        """Gather all files in the skill directory recursively."""
        self.all_files = sorted(
            p for p in self.skill_path.rglob("*") if p.is_file()
        )

    # ── 1. Folder structure ──

    def check_folder_structure(self):
        cat = "Folder Structure"

        # SKILL.md must exist (exact case)
        skill_md = self.skill_path / "SKILL.md"
        if not skill_md.exists():
            # Check common misspellings
            for variant in ["skill.md", "SKILL.MD", "Skill.md", "Skill.MD"]:
                if (self.skill_path / variant).exists():
                    self.add(SEVERITY_CRITICAL, cat,
                             f"Found '{variant}' but it must be exactly 'SKILL.md' (case-sensitive).",
                             f"Rename the file: mv {variant} SKILL.md")
                    return False
            self.add(SEVERITY_CRITICAL, cat,
                     "SKILL.md not found in the skill directory.",
                     "Create a SKILL.md file with YAML frontmatter and instructions.")
            return False

        # Folder name should be kebab-case
        folder_name = self.skill_path.name
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', folder_name):
            self.add(SEVERITY_WARNING, cat,
                     f"Folder name '{folder_name}' is not in kebab-case.",
                     f"Rename to something like '{re.sub(r'[^a-z0-9]+', '-', folder_name.lower()).strip('-')}'")

        # README.md should NOT exist inside the skill folder
        readme = self.skill_path / "README.md"
        if readme.exists():
            self.add(SEVERITY_WARNING, cat,
                     "README.md found inside skill folder. Documentation should go in SKILL.md or references/.",
                     "Remove README.md and move its content to SKILL.md or references/.")

        return True

    # ── 2. Frontmatter parsing and validation ──

    def check_frontmatter(self):
        cat = "YAML Frontmatter"
        skill_md = self.skill_path / "SKILL.md"
        self.raw_content = skill_md.read_text(encoding="utf-8")

        # Must start with ---
        if not self.raw_content.lstrip("\ufeff").startswith("---"):
            self.add(SEVERITY_CRITICAL, cat,
                     "No YAML frontmatter found. SKILL.md must start with '---'.",
                     "Add frontmatter:\n---\nname: your-skill-name\ndescription: What it does. Use when ...\n---")
            return False

        match = re.match(r'^-{3,}\s*\n(.*?)\n-{3,}', self.raw_content.lstrip("\ufeff"), re.DOTALL)
        if not match:
            self.add(SEVERITY_CRITICAL, cat,
                     "Frontmatter delimiters (---) not properly closed.",
                     "Ensure frontmatter is enclosed between two '---' lines.")
            return False

        fm_text = match.group(1)
        try:
            self.frontmatter = yaml.safe_load(fm_text)
            if not isinstance(self.frontmatter, dict):
                self.add(SEVERITY_CRITICAL, cat,
                         "Frontmatter must be a YAML mapping (key: value pairs).")
                return False
        except yaml.YAMLError as e:
            self.add(SEVERITY_CRITICAL, cat,
                     f"Invalid YAML in frontmatter: {e}")
            return False

        # Body after frontmatter
        self.body = self.raw_content[match.end():].strip()

        # Unexpected keys
        unexpected = set(self.frontmatter.keys()) - ALLOWED_FRONTMATTER_KEYS
        if unexpected:
            self.add(SEVERITY_WARNING, cat,
                     f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}. "
                     f"Allowed keys: {', '.join(sorted(ALLOWED_FRONTMATTER_KEYS))}",
                     "Remove or move unexpected keys into the 'metadata' field.")

        # ── name field ──
        name = self.frontmatter.get("name")
        if name is None:
            self.add(SEVERITY_CRITICAL, cat, "'name' field is missing from frontmatter.")
        else:
            name = str(name).strip()
            if not name:
                self.add(SEVERITY_CRITICAL, cat, "'name' field is empty.")
            else:
                if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
                    self.add(SEVERITY_CRITICAL, cat,
                             f"name '{name}' must be kebab-case (lowercase letters, digits, hyphens).",
                             f"Use: {re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')}")
                if len(name) > 64:
                    self.add(SEVERITY_CRITICAL, cat,
                             f"name is {len(name)} characters (max 64).")
                for reserved in RESERVED_NAME_FRAGMENTS:
                    if reserved in name.lower():
                        self.add(SEVERITY_CRITICAL, cat,
                                 f"name contains reserved word '{reserved}'.",
                                 "Choose a name that does not include 'claude' or 'anthropic'.")
                if "<" in name or ">" in name:
                    self.add(SEVERITY_CRITICAL, cat,
                             "name contains XML angle brackets (< >). This is forbidden.")

        # ── description field ──
        desc = self.frontmatter.get("description")
        if desc is None:
            self.add(SEVERITY_CRITICAL, cat, "'description' field is missing from frontmatter.")
        else:
            desc = str(desc).strip()
            if not desc:
                self.add(SEVERITY_CRITICAL, cat, "'description' field is empty.")
            else:
                if "<" in desc or ">" in desc:
                    self.add(SEVERITY_CRITICAL, cat,
                             "description contains XML angle brackets (< >). This is forbidden for security.",
                             "Remove all < and > characters from the description.")
                if len(desc) > 1024:
                    self.add(SEVERITY_CRITICAL, cat,
                             f"description is {len(desc)} chars (max 1024).",
                             "Shorten the description. Move details to the SKILL.md body.")
                self._check_description_quality(desc)

        # ── compatibility field ──
        compat = self.frontmatter.get("compatibility")
        if compat is not None:
            compat = str(compat).strip()
            if len(compat) > 500:
                self.add(SEVERITY_WARNING, cat,
                         f"compatibility is {len(compat)} chars (max 500).")

        # ── Optional fields validation ──
        dmi = self.frontmatter.get("disable-model-invocation")
        if dmi is not None and not isinstance(dmi, bool):
            self.add(SEVERITY_WARNING, cat,
                     f"disable-model-invocation should be true or false, got '{dmi}'.")

        ui = self.frontmatter.get("user-invocable")
        if ui is not None and not isinstance(ui, bool):
            self.add(SEVERITY_WARNING, cat,
                     f"user-invocable should be true or false, got '{ui}'.")

        ctx = self.frontmatter.get("context")
        if ctx is not None and ctx != "fork":
            self.add(SEVERITY_WARNING, cat,
                     f"context field only supports 'fork'. Got '{ctx}'.")

        return True

    def _check_description_quality(self, desc: str):
        cat = "Description Quality"
        desc_lower = desc.lower()

        # Non-English language check
        if contains_non_english(desc):
            self.add(SEVERITY_WARNING, cat,
                     "Description contains non-English characters. "
                     "Write the description in English for best triggering accuracy. "
                     "Claude handles English skill definitions most reliably, regardless of the user's session language.",
                     "Rewrite the description in English. "
                     "Structure: '[What the skill does in English]. Use when [trigger conditions in English].'")
            # Skip word-count and English-pattern checks since they won't be meaningful
            return

        # WHEN check: description should include trigger conditions
        has_when = any(kw in desc_lower for kw in WHEN_TRIGGER_KEYWORDS)

        if not has_when:
            self.add(SEVERITY_WARNING, cat,
                     "Description lacks trigger phrases (WHEN to use). "
                     "Include phrases like 'Use when user asks to ...', 'Use for ...', 'Trigger when ...'.",
                     "Add: 'Use when ...' or 'Use for ...' clause describing when Claude should activate this skill.")

        # Vague description check
        for pattern in DESCRIPTION_VAGUE_PATTERNS:
            if re.match(pattern, desc_lower):
                self.add(SEVERITY_WARNING, cat,
                         f"Description appears too vague (matches pattern: '{pattern}').",
                         "Be specific: describe concrete actions, file types, and user intents.")
                break

        # Very short description (English word count)
        word_count = len(desc.split())
        if word_count < 8:
            self.add(SEVERITY_WARNING, cat,
                     f"Description is very short ({word_count} words). "
                     "Aim for at least 15-30 words covering WHAT and WHEN.",
                     "Expand: '[What the skill does]. Use when [trigger conditions].'")

        # Check for specific trigger phrases (concrete user language)
        has_quoted_triggers = bool(re.search(r'["\'].*?["\']', desc))
        has_specific_verbs = any(v in desc_lower for v in [
            "create", "generate", "analyze", "build", "fix", "deploy",
            "review", "set up", "configure", "migrate", "convert",
        ])
        if not has_quoted_triggers and not has_specific_verbs and word_count >= 8:
            self.add(SEVERITY_SUGGEST, cat,
                     "Description lacks concrete action verbs or quoted trigger phrases.",
                     "Include specific actions ('create', 'analyze', ...) or user phrases (\"help me plan\").")

    # ── 3. Body quality ──

    def check_body_quality(self):
        cat = "Instructions Quality"
        if not self.body:
            self.add(SEVERITY_WARNING, cat,
                     "SKILL.md body is empty. Add instructions for Claude to follow.")
            return

        lines = self.body.split("\n")
        line_count = len(lines)

        # Size checks (progressive disclosure)
        if line_count > SKILL_MD_LARGE_LINES:
            self.add(SEVERITY_WARNING, "Progressive Disclosure",
                     f"SKILL.md body is {line_count} lines (recommended < {SKILL_MD_WARN_LINES}). "
                     "Consider moving detailed references to separate files.",
                     "Move large reference sections to references/ and link from SKILL.md.")
        elif line_count > SKILL_MD_WARN_LINES:
            self.add(SEVERITY_SUGGEST, "Progressive Disclosure",
                     f"SKILL.md body is {line_count} lines. Consider whether some content "
                     "could be split to support files for better progressive disclosure.")

        # Word count check (only meaningful for English text)
        if not contains_non_english(self.body):
            word_count = len(self.body.split())
            if word_count > SKILL_MD_WARN_WORDS:
                self.add(SEVERITY_SUGGEST, "Progressive Disclosure",
                         f"SKILL.md is ~{word_count} words. Large content loads into context on every trigger. "
                         "Move detailed docs to references/ to reduce token usage.")

        # Check for vague instructions
        body_lower = self.body.lower()
        vague_phrases = [
            "validate the data before proceeding",
            "make sure to handle errors",
            "do it properly",
            "process things correctly",
        ]
        for phrase in vague_phrases:
            if phrase in body_lower:
                self.add(SEVERITY_SUGGEST, cat,
                         f"Vague instruction found: '{phrase}'. Prefer specific, actionable guidance.",
                         "Replace with concrete steps, tool names, or script references.")

        # Check for error handling / troubleshooting section
        has_error_section = any(
            heading in body_lower
            for heading in [
                "# error", "# troubleshoot", "## error", "## troubleshoot",
                "# common issue", "## common issue", "# debugging", "## debugging",
                "error handling", "if .* fails", "if .* error",
            ]
        )
        if not has_error_section:
            self.add(SEVERITY_SUGGEST, cat,
                     "No error handling or troubleshooting section found.",
                     "Add a section like:\n## Troubleshooting\n- Error: [message] → Solution: [fix]")

        # Check for examples section
        has_examples = any(
            kw in body_lower
            for kw in ["# example", "## example", "example:", "**example"]
        )
        if not has_examples:
            self.add(SEVERITY_SUGGEST, cat,
                     "No examples section found. Examples help Claude produce consistent results.",
                     "Add a ## Examples section with concrete input/output pairs.")

        # Check if instructions are purely descriptive vs. actionable
        imperative_markers = [
            r"\b(run|execute|call|create|generate|fetch|check|verify|read|write|save|use|install)\b",
        ]
        has_imperative = any(
            re.search(pat, self.body, re.IGNORECASE) for pat in imperative_markers
        )
        if not has_imperative:
            self.add(SEVERITY_SUGGEST, cat,
                     "Instructions may lack imperative/actionable language. "
                     "Use verbs like 'Run', 'Create', 'Check', 'Verify' for clearer guidance.")

    # ── 4. Support files and references ──

    def check_support_files(self):
        cat = "Support Files"
        self._collect_files()

        # Find files in the skill directory other than SKILL.md
        support_files = [
            f for f in self.all_files
            if f.name != "SKILL.md" and not f.name.startswith(".")
        ]

        if not support_files:
            return  # No support files to check

        # Check if support files are referenced from SKILL.md
        body_lower = self.body.lower()
        raw_lower = self.raw_content.lower()

        unreferenced = []
        for sf in support_files:
            relative = sf.relative_to(self.skill_path)
            name_only = sf.name.lower()
            rel_str = str(relative).lower()

            # Check if referenced by relative path, filename, or as a link
            if (rel_str not in raw_lower
                    and name_only not in raw_lower
                    and sf.stem.lower() not in raw_lower):
                unreferenced.append(str(relative))

        if unreferenced:
            files_list = ", ".join(unreferenced[:10])
            suffix = f" (and {len(unreferenced) - 10} more)" if len(unreferenced) > 10 else ""
            self.add(SEVERITY_WARNING, cat,
                     f"Support file(s) not referenced from SKILL.md: {files_list}{suffix}. "
                     "Claude won't know when to load unreferenced files.",
                     "Add references in SKILL.md, e.g.: 'For details, see [file.md](file.md)'")

        # Check for __pycache__ or .pyc
        pycache = [f for f in self.all_files if "__pycache__" in str(f) or f.suffix == ".pyc"]
        if pycache:
            self.add(SEVERITY_SUGGEST, cat,
                     "Python cache files found. Consider adding __pycache__/ to .gitignore or removing them.")

    # ── 5. Security ──

    def check_security(self):
        cat = "Security"

        # Check for angle brackets in entire frontmatter text
        fm_text = ""
        match = re.match(r'^-{3,}\s*\n(.*?)\n-{3,}', self.raw_content.lstrip("\ufeff"), re.DOTALL)
        if match:
            fm_text = match.group(1)
            if "<" in fm_text or ">" in fm_text:
                self.add(SEVERITY_CRITICAL, cat,
                         "XML angle brackets (< >) found in frontmatter. "
                         "This is a security restriction — frontmatter appears in Claude's system prompt.",
                         "Remove all < and > from frontmatter fields.")

        # Check for suspicious patterns in scripts
        scripts_dir = self.skill_path / "scripts"
        if scripts_dir.is_dir():
            for script in scripts_dir.rglob("*"):
                if not script.is_file():
                    continue
                try:
                    content = script.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

                # Check for obvious exfiltration patterns
                suspicious_patterns = [
                    (r"curl\s+.*\s+--data", "Potential data exfiltration via curl"),
                    (r"wget\s+.*\s+-O\s*-\s*\|", "Potential piped download execution"),
                    (r"eval\s*\(\s*base64", "Potential obfuscated code execution"),
                ]
                for pattern, desc in suspicious_patterns:
                    if re.search(pattern, content):
                        self.add(SEVERITY_WARNING, cat,
                                 f"Suspicious pattern in {script.relative_to(self.skill_path)}: {desc}",
                                 "Review this script carefully before distributing.")

    # ── 6. context: fork consistency ──

    def check_context_fork_consistency(self):
        cat = "Context Fork"
        ctx = self.frontmatter.get("context")
        if ctx != "fork":
            return

        # Skills with context: fork should have explicit task instructions
        body_lower = self.body.lower()
        has_steps = bool(re.search(r'(step\s*\d|^\s*\d+\.)', self.body, re.MULTILINE | re.IGNORECASE))
        has_task = any(kw in body_lower for kw in ["your task", "execute", "perform", "run the"])

        if not has_steps and not has_task:
            self.add(SEVERITY_WARNING, cat,
                     "Skill uses context: fork but lacks explicit task steps. "
                     "Sub-agents need actionable instructions, not just reference content.",
                     "Add numbered steps or a clear task description for the sub-agent.")

        # Check agent field
        agent = self.frontmatter.get("agent")
        if agent is None:
            self.add(SEVERITY_SUGGEST, cat,
                     "context: fork is set but 'agent' field is not specified (defaults to 'general-purpose').",
                     "Consider specifying agent: Explore, Plan, or a custom agent name.")

    # ── Run all checks ──

    def run(self):
        ok = self.check_folder_structure()
        if ok:
            fm_ok = self.check_frontmatter()
            if fm_ok:
                self.check_body_quality()
                self.check_support_files()
                self.check_security()
                self.check_context_fork_consistency()
        return self.findings


# ─── Report Formatter ────────────────────────────────────────────────────────

def format_report(skill_path: Path, findings: list[Finding]) -> str:
    lines = []

    # Header
    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  Skill Best Practices Check: {skill_path.name}")
    lines.append(f"  Path: {skill_path}")
    lines.append("=" * 70)

    if not findings:
        lines.append("")
        lines.append("  ✅  All checks passed! Your skill follows best practices.")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    # Summary counts
    counts = defaultdict(int)
    for f in findings:
        counts[f.severity] += 1

    total_passed_approx = 15 - len(findings)  # rough estimate of total checks
    if total_passed_approx < 0:
        total_passed_approx = 0

    lines.append("")
    summary_parts = []
    for sev in [SEVERITY_CRITICAL, SEVERITY_WARNING, SEVERITY_SUGGEST]:
        if counts[sev]:
            summary_parts.append(f"{SEVERITY_ICON[sev]} {sev}: {counts[sev]}")
    lines.append("  Summary: " + "  |  ".join(summary_parts))
    lines.append("")

    # Group by severity
    sorted_findings = sorted(findings, key=lambda f: SEVERITY_ORDER[f.severity])

    current_sev = None
    idx = 0
    for f in sorted_findings:
        if f.severity != current_sev:
            current_sev = f.severity
            lines.append(f"  ── {SEVERITY_ICON[f.severity]} {f.severity} ──")
            lines.append("")

        idx += 1
        lines.append(f"  [{f.category}]")
        # Wrap long messages
        wrapped = textwrap.fill(f.message, width=66, initial_indent="    ", subsequent_indent="    ")
        lines.append(wrapped)

        if f.fix:
            fix_wrapped = textwrap.fill(f.fix, width=66, initial_indent="    → ", subsequent_indent="      ")
            lines.append(fix_wrapped)

        lines.append("")

    lines.append("=" * 70)

    # JSON output for programmatic use
    json_findings = [f.to_dict() for f in findings]
    lines.append("")
    lines.append("JSON (for programmatic use):")
    lines.append(json.dumps({
        "skill": str(skill_path),
        "summary": dict(counts),
        "findings": json_findings,
    }, indent=2, ensure_ascii=False))

    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        target = Path.cwd()
    else:
        target = Path(sys.argv[1])

    target = target.resolve()

    if not target.is_dir():
        print(f"ERROR: '{target}' is not a directory.")
        sys.exit(1)

    # If target contains SKILL.md directly, use it
    # Otherwise check if it's a parent containing skill subdirs
    if (target / "SKILL.md").exists():
        checker = SkillChecker(target)
        findings = checker.run()
        print(format_report(target, findings))
        has_critical = any(f.severity == SEVERITY_CRITICAL for f in findings)
        sys.exit(1 if has_critical else 0)
    else:
        # Look for skill subdirectories
        skill_dirs = sorted(
            d for d in target.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )
        if not skill_dirs:
            print(f"ERROR: No SKILL.md found in '{target}' or its subdirectories.")
            print("Provide a path to a skill folder containing SKILL.md.")
            sys.exit(1)

        any_critical = False
        for sd in skill_dirs:
            checker = SkillChecker(sd)
            findings = checker.run()
            print(format_report(sd, findings))
            if any(f.severity == SEVERITY_CRITICAL for f in findings):
                any_critical = True
            print("")

        sys.exit(1 if any_critical else 0)


if __name__ == "__main__":
    main()
