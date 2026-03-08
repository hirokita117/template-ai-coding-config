#!/usr/bin/env python3
"""
Discover available skill directories.

Searches common skill locations and prints a numbered list
of skill folders (those containing SKILL.md).
"""

import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def find_skill_dirs(search_roots: list[Path]) -> list[dict]:
    """Find directories containing SKILL.md under the given roots."""
    seen = set()
    skills = []

    for root in search_roots:
        if not root.is_dir():
            continue
        # Direct children that are skill dirs
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            skill_md = child / "SKILL.md"
            if skill_md.exists():
                resolved = child.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                info = extract_info(skill_md, child)
                skills.append(info)

    return skills


def extract_info(skill_md: Path, skill_dir: Path) -> dict:
    """Extract name and description from SKILL.md frontmatter."""
    info = {
        "path": str(skill_dir),
        "folder": skill_dir.name,
        "name": skill_dir.name,
        "description": "",
    }

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception:
        return info

    match = re.match(r'^-{3,}\s*\n(.*?)\n-{3,}', content.lstrip("\ufeff"), re.DOTALL)
    if not match:
        return info

    if yaml is None:
        # Fallback: regex extraction
        for line in match.group(1).splitlines():
            m = re.match(r'^name:\s*(.+)', line)
            if m:
                info["name"] = m.group(1).strip().strip('"').strip("'")
            m = re.match(r'^description:\s*(.+)', line)
            if m:
                info["description"] = m.group(1).strip().strip('"').strip("'")
        return info

    try:
        fm = yaml.safe_load(match.group(1))
        if isinstance(fm, dict):
            info["name"] = str(fm.get("name", skill_dir.name)).strip()
            desc = str(fm.get("description", "")).strip()
            # Truncate for display
            if len(desc) > 120:
                desc = desc[:117] + "..."
            info["description"] = desc
    except Exception:
        pass

    return info


def get_search_roots() -> list[Path]:
    """Determine which directories to scan for skills."""
    roots = []

    # 1. Project-level: .claude/skills/ from CWD upward
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".claude" / "skills"
        if candidate.is_dir():
            roots.append(candidate)
            break  # only closest project root

    # 2. Personal: ~/.claude/skills/
    home_skills = Path.home() / ".claude" / "skills"
    if home_skills.is_dir():
        roots.append(home_skills)

    return roots


def main():
    roots = get_search_roots()

    if not roots:
        print("NO_SKILLS_DIRS")
        print("Could not find any .claude/skills/ directory.")
        print("Searched:")
        print(f"  - {Path.cwd()}/.claude/skills/  (project)")
        print(f"  - {Path.home()}/.claude/skills/  (personal)")
        sys.exit(0)

    skills = find_skill_dirs(roots)

    if not skills:
        print("NO_SKILLS_FOUND")
        print("Found .claude/skills/ directories but no skill folders (with SKILL.md) inside:")
        for r in roots:
            print(f"  - {r}")
        sys.exit(0)

    # Output structured list
    print(f"FOUND {len(skills)} skill(s):\n")

    for i, s in enumerate(skills, 1):
        print(f"  {i}. {s['name']}")
        print(f"     Path: {s['path']}")
        if s["description"]:
            print(f"     Desc: {s['description']}")
        print()

    # Also print paths for easy copy
    print("PATHS:")
    for s in skills:
        print(s["path"])


if __name__ == "__main__":
    main()
