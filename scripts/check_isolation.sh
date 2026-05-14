#!/usr/bin/env bash
#
# Pre-flight check before running the benchmark matrix.
# Reports environment state that could pollute results in subscription mode
# (since --bare is disabled). Exits 0 always — informational only.
#
# Usage: bash scripts/check_isolation.sh

set -u

YELLOW=$'\033[33m'
GREEN=$'\033[32m'
RED=$'\033[31m'
RESET=$'\033[0m'

warn() { echo "${YELLOW}[warn]${RESET} $*"; }
ok()   { echo "${GREEN}[ ok ]${RESET} $*"; }
bad()  { echo "${RED}[fail]${RESET} $*"; }

echo "Checking benchmark isolation prerequisites..."
echo

# 1. Claude Code present + version
if ! command -v claude >/dev/null 2>&1; then
    bad "claude CLI not found in PATH"
    exit 1
fi
CLAUDE_VERSION="$(claude --version 2>/dev/null | head -1)"
ok "claude: $CLAUDE_VERSION"

# 2. ~/.claude/CLAUDE.md — biggest residual pollution risk
if [[ -f "$HOME/.claude/CLAUDE.md" ]]; then
    SIZE=$(wc -c < "$HOME/.claude/CLAUDE.md" 2>/dev/null || echo 0)
    if [[ "$SIZE" -gt 0 ]]; then
        warn "~/.claude/CLAUDE.md exists ($SIZE bytes) — will be auto-loaded into every run."
        warn "    Recommended: mv ~/.claude/CLAUDE.md{,.bench-bak}  before the matrix."
    else
        ok "~/.claude/CLAUDE.md is empty"
    fi
else
    ok "~/.claude/CLAUDE.md not present"
fi

# 3. Plugins synced under ~/.claude/plugins
if [[ -d "$HOME/.claude/plugins" ]] && [[ -n "$(ls -A "$HOME/.claude/plugins" 2>/dev/null)" ]]; then
    PLUGIN_COUNT=$(ls -1 "$HOME/.claude/plugins" 2>/dev/null | wc -l)
    warn "~/.claude/plugins has $PLUGIN_COUNT entries — plugin sync runs each invocation."
    warn "    Subscription mode cannot disable this. Consider temporarily moving the dir."
else
    ok "no user-level plugins"
fi

# 4. Hooks in user-level settings
if [[ -f "$HOME/.claude/settings.json" ]]; then
    if command -v jq >/dev/null 2>&1; then
        HOOK_COUNT=$(jq -r '[.hooks // {} | to_entries[] | .value[]?] | length' \
                     "$HOME/.claude/settings.json" 2>/dev/null || echo 0)
        if [[ "${HOOK_COUNT:-0}" -gt 0 ]]; then
            warn "~/.claude/settings.json defines $HOOK_COUNT hook(s). --setting-sources project skips them, but verify with a dry-run."
        else
            ok "no user-level hooks in settings.json"
        fi
    fi
fi

# 5. Auth mode preview
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    warn "ANTHROPIC_API_KEY is set in env → runs will use api-key auth (pay-per-token)."
    warn "    Unset it if you want subscription billing."
else
    ok "auth mode: subscription (OAuth/keychain)"
fi

# 6. Required CLI tools
for tool in jq yq python3 git npm; do
    if command -v "$tool" >/dev/null 2>&1; then
        ok "$tool: $(command -v "$tool")"
    else
        bad "$tool not found in PATH"
    fi
done

# 7. Node deps for Task 01
if [[ -d "tasks/01_rename/initial_repo/node_modules" ]]; then
    ok "tasks/01_rename/initial_repo: node_modules present"
else
    warn "tasks/01_rename/initial_repo/node_modules missing — run: (cd tasks/01_rename/initial_repo && npm install)"
fi

echo
echo "Done. Review warnings above before running the matrix."
