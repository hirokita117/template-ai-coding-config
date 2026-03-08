#!/usr/bin/env bash
# detect_context.sh - Collect diff and project metadata for code review
set -euo pipefail

# --- Diff detection ---
STAGED_DIFF=$(git diff --cached --stat 2>/dev/null || true)
if [ -n "$STAGED_DIFF" ]; then
  DIFF_MODE="staged"
  CHANGED_FILES=$(git diff --cached --name-only)
  DIFF_STAT=$(git diff --cached --stat)
else
  # Detect base branch
  BASE_BRANCH=""
  for candidate in main master develop; do
    if git rev-parse --verify "$candidate" >/dev/null 2>&1; then
      BASE_BRANCH="$candidate"
      break
    fi
  done

  if [ -z "$BASE_BRANCH" ]; then
    echo "DIFF_MODE=none"
    echo "ERROR=No staged changes and no base branch found"
    exit 0
  fi

  MERGE_BASE=$(git merge-base "$BASE_BRANCH" HEAD 2>/dev/null || echo "")
  if [ -z "$MERGE_BASE" ] || [ "$(git rev-parse HEAD)" = "$MERGE_BASE" ]; then
    echo "DIFF_MODE=none"
    echo "ERROR=No changes found compared to $BASE_BRANCH"
    exit 0
  fi

  DIFF_MODE="branch:$BASE_BRANCH"
  CHANGED_FILES=$(git diff --name-only "$MERGE_BASE"...HEAD)
  DIFF_STAT=$(git diff --stat "$MERGE_BASE"...HEAD)
fi

# --- Language & framework detection ---
LANGUAGES=""
FRAMEWORKS=""
PACKAGE_JSON_FILES=$(rg --files -g 'package.json' 2>/dev/null || true)
TSCONFIG_FILES=$(rg --files -g 'tsconfig.json' -g 'tsconfig.*.json' 2>/dev/null || true)

has_pattern_in_files() {
  local pattern="$1"
  local files="$2"

  [ -n "$files" ] || return 1

  while IFS= read -r file; do
    [ -n "$file" ] || continue
    if grep -q "$pattern" "$file" 2>/dev/null; then
      return 0
    fi
  done <<< "$files"

  return 1
}

# JavaScript/TypeScript
if [ -n "$PACKAGE_JSON_FILES" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}javascript"
  if [ -n "$TSCONFIG_FILES" ] || echo "$CHANGED_FILES" | grep -q '\.tsx\?\b'; then
    LANGUAGES="${LANGUAGES},typescript"
  fi

  # Detect frameworks from package.json files across the repo.
  if has_pattern_in_files '"react"' "$PACKAGE_JSON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}react"
  fi
  if has_pattern_in_files '"next"' "$PACKAGE_JSON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}nextjs"
  fi
  if has_pattern_in_files '"vue"' "$PACKAGE_JSON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}vue"
  fi
  if has_pattern_in_files '"express"' "$PACKAGE_JSON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}express"
  fi
  if has_pattern_in_files '"nestjs\|@nestjs"' "$PACKAGE_JSON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}nestjs"
  fi
fi

# PHP
if [ -f "composer.json" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}php"
  if grep -q '"laravel/framework"' composer.json 2>/dev/null; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}laravel"
  fi
  if grep -q '"symfony/' composer.json 2>/dev/null; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}symfony"
  fi
fi

# Python
if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}python"
  if grep -rq 'django' pyproject.toml setup.py requirements.txt 2>/dev/null; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}django"
  fi
  if grep -rq 'fastapi' pyproject.toml setup.py requirements.txt 2>/dev/null; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}fastapi"
  fi
  if grep -rq 'flask' pyproject.toml setup.py requirements.txt 2>/dev/null; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}flask"
  fi
fi

# Go
if [ -f "go.mod" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}go"
fi

# Rust
if [ -f "Cargo.toml" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}rust"
fi

# Java/Kotlin
if [ -f "pom.xml" ] || [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
  if [ -f "build.gradle.kts" ] || echo "$CHANGED_FILES" | grep -q '\.kt$'; then
    LANGUAGES="${LANGUAGES:+$LANGUAGES,}kotlin"
  else
    LANGUAGES="${LANGUAGES:+$LANGUAGES,}java"
  fi
  if grep -rq 'spring' pom.xml build.gradle build.gradle.kts 2>/dev/null; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}spring"
  fi
fi

# Ruby
if [ -f "Gemfile" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}ruby"
  if grep -q 'rails' Gemfile 2>/dev/null; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}rails"
  fi
fi

# --- File category detection ---
HAS_BACKEND=false
HAS_FRONTEND=false
HAS_TESTS=false
HAS_SECURITY_SENSITIVE=false
HAS_TYPED_LANG=false

while IFS= read -r file; do
  # Backend patterns
  if echo "$file" | grep -qE '(controller|service|repository|model|migration|api|server|handler|middleware|route)'; then
    HAS_BACKEND=true
  fi
  # Frontend patterns
  if echo "$file" | grep -qE '\.(jsx|tsx|vue|svelte|css|scss|sass|less)$|components/|pages/|views/'; then
    HAS_FRONTEND=true
  fi
  # Test patterns
  if echo "$file" | grep -qE '(^|/)(__tests__/.*|.*(_test|\.test|\.spec)\.[^.]+)$'; then
    HAS_TESTS=true
  fi
  # Security-sensitive patterns
  if echo "$file" | grep -qiE '(auth|login|password|token|secret|crypt|session|permission|role|oauth|saml|jwt|\.env|credential)'; then
    HAS_SECURITY_SENSITIVE=true
  fi
done <<< "$CHANGED_FILES"

# Typed language detection
if echo "$LANGUAGES" | grep -qE '(typescript|go|rust|java|kotlin)'; then
  HAS_TYPED_LANG=true
fi

# --- Project configuration detection ---
HAS_CLAUDE_MD=false
[ -f "CLAUDE.md" ] && HAS_CLAUDE_MD=true

HAS_LINTER=false
LINTER_CONFIG=""
while IFS= read -r config; do
  [ -n "$config" ] || continue
  HAS_LINTER=true
  LINTER_CONFIG="${LINTER_CONFIG:+$LINTER_CONFIG,}$config"
done <<< "$(rg --files \
  -g '.eslintrc' -g '.eslintrc.js' -g '.eslintrc.json' -g '.eslintrc.yml' -g 'eslint.config.js' -g 'eslint.config.mjs' \
  -g 'phpstan.neon' -g 'phpstan.neon.dist' -g '.phpcs.xml' -g 'phpcs.xml' \
  -g '.pylintrc' -g '.flake8' -g '.ruff.toml' -g 'ruff.toml' \
  -g '.golangci.yml' -g '.golangci.yaml' \
  -g '.rubocop.yml' 2>/dev/null || true)"

# --- Output ---
echo "DIFF_MODE=$DIFF_MODE"
echo "LANGUAGES=${LANGUAGES:-unknown}"
echo "FRAMEWORKS=${FRAMEWORKS:-none}"
echo "HAS_CLAUDE_MD=$HAS_CLAUDE_MD"
echo "HAS_LINTER=$HAS_LINTER"
echo "LINTER_CONFIG=${LINTER_CONFIG:-none}"
echo "HAS_BACKEND=$HAS_BACKEND"
echo "HAS_FRONTEND=$HAS_FRONTEND"
echo "HAS_TESTS=$HAS_TESTS"
echo "HAS_SECURITY_SENSITIVE=$HAS_SECURITY_SENSITIVE"
echo "HAS_TYPED_LANG=$HAS_TYPED_LANG"
echo "CHANGED_FILES<<EOF"
echo "$CHANGED_FILES"
echo "EOF"
echo "DIFF_STAT<<EOF"
echo "$DIFF_STAT"
echo "EOF"
