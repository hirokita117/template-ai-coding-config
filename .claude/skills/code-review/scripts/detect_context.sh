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
COMPOSER_FILES=$(rg --files -g 'composer.json' 2>/dev/null || true)
PYPROJECT_FILES=$(rg --files -g 'pyproject.toml' 2>/dev/null || true)
SETUP_PY_FILES=$(rg --files -g 'setup.py' 2>/dev/null || true)
REQUIREMENTS_FILES=$(rg --files -g 'requirements.txt' 2>/dev/null || true)
GOMOD_FILES=$(rg --files -g 'go.mod' 2>/dev/null || true)
CARGO_FILES=$(rg --files -g 'Cargo.toml' 2>/dev/null || true)
POM_FILES=$(rg --files -g 'pom.xml' 2>/dev/null || true)
GRADLE_FILES=$(rg --files -g 'build.gradle' -g 'build.gradle.kts' 2>/dev/null || true)
GEMFILE_FILES=$(rg --files -g 'Gemfile' 2>/dev/null || true)

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
if [ -n "$COMPOSER_FILES" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}php"
  if has_pattern_in_files '"laravel/framework"' "$COMPOSER_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}laravel"
  fi
  if has_pattern_in_files '"symfony/' "$COMPOSER_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}symfony"
  fi
fi

# Python
PYTHON_FILES=""
[ -n "$PYPROJECT_FILES" ] && PYTHON_FILES="$PYPROJECT_FILES"
[ -n "$SETUP_PY_FILES" ] && PYTHON_FILES="${PYTHON_FILES:+$PYTHON_FILES
}$SETUP_PY_FILES"
[ -n "$REQUIREMENTS_FILES" ] && PYTHON_FILES="${PYTHON_FILES:+$PYTHON_FILES
}$REQUIREMENTS_FILES"

if [ -n "$PYTHON_FILES" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}python"
  if has_pattern_in_files 'django' "$PYTHON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}django"
  fi
  if has_pattern_in_files 'fastapi' "$PYTHON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}fastapi"
  fi
  if has_pattern_in_files 'flask' "$PYTHON_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}flask"
  fi
fi

# Go
if [ -n "$GOMOD_FILES" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}go"
fi

# Rust
if [ -n "$CARGO_FILES" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}rust"
fi

# Java/Kotlin
if [ -n "$POM_FILES" ] || [ -n "$GRADLE_FILES" ]; then
  GRADLE_KTS_FILES=$(rg --files -g 'build.gradle.kts' 2>/dev/null || true)
  if [ -n "$GRADLE_KTS_FILES" ] || echo "$CHANGED_FILES" | grep -q '\.kt$'; then
    LANGUAGES="${LANGUAGES:+$LANGUAGES,}kotlin"
  else
    LANGUAGES="${LANGUAGES:+$LANGUAGES,}java"
  fi
  BUILD_FILES=""
  [ -n "$POM_FILES" ] && BUILD_FILES="$POM_FILES"
  [ -n "$GRADLE_FILES" ] && BUILD_FILES="${BUILD_FILES:+$BUILD_FILES
}$GRADLE_FILES"
  if has_pattern_in_files 'spring' "$BUILD_FILES"; then
    FRAMEWORKS="${FRAMEWORKS:+$FRAMEWORKS,}spring"
  fi
fi

# Ruby
if [ -n "$GEMFILE_FILES" ]; then
  LANGUAGES="${LANGUAGES:+$LANGUAGES,}ruby"
  if has_pattern_in_files 'rails' "$GEMFILE_FILES"; then
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
