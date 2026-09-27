#!/usr/bin/env bash
# End-to-end check that /next reaches Claude only after the current turn ends,
# using a real interactive Claude Code session.
#
# 1. Starts Claude Code inside tmux and gives it a task with sleeps in it.
# 2. Once the first tool call is recorded (the turn is in progress), queues two /next commands.
#    The first /next is also a multi-step task, so we can see whether the second one waits for it.
# 3. Reads the session transcript (JSONL) and checks that:
#    - both /next commands were enqueued before FIRST_DONE (queued mid-turn)
#    - neither /next reached the model before FIRST_DONE (no mid-turn injection)
#    - the second /next didn't reach the model before SECOND_DONE (no injection during the first /next either)
#    - FIRST -> SECOND -> THIRD each ran as a separate turn, in order
#
# Usage: tests/verify.sh            (defaults to haiku)
#        MODEL=sonnet tests/verify.sh
# Needs: tmux, jq, and the skill installed at ~/.claude/skills/next
set -euo pipefail

MODEL="${MODEL:-haiku}"
TIMEOUT="${TIMEOUT:-180}"
TMUX_SESSION="next-verify-$$"
repo="$(cd "$(dirname "$0")/.." && pwd)"
config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

for bin in tmux jq claude uuidgen; do
  command -v "$bin" >/dev/null || { echo "Missing command: $bin" >&2; exit 2; }
done
[[ -f "$config_dir/skills/next/SKILL.md" ]] || { echo "Run ./install.sh first." >&2; exit 2; }

sid="$(uuidgen | tr 'A-Z' 'a-z')"
cleanup() { tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true; }
trap cleanup EXIT

pane() { tmux capture-pane -t "$TMUX_SESSION" -p -S -200; }
send() { tmux send-keys -t "$TMUX_SESSION" -l "$1"; sleep 0.5; tmux send-keys -t "$TMUX_SESSION" Enter; }
transcript() { find "$config_dir/projects" -name "$sid.jsonl" 2>/dev/null | head -1; }
wait_for() { # $1: what we're waiting for, $2: condition to eval
  local i
  for ((i = 0; i < TIMEOUT; i++)); do
    if eval "$2"; then return 0; fi
    sleep 1
  done
  echo "Timed out waiting for: $1" >&2
  pane | tail -30 >&2
  exit 1
}

echo "Claude Code $(claude --version) · model $MODEL · session $sid"
tmux new-session -d -s "$TMUX_SESSION" -x 160 -y 50 -c "$repo" \
  "claude --model $MODEL --session-id $sid --allowedTools Bash --settings '{\"disableAllHooks\":true}'"

# Accept the folder trust prompt if it shows up ("No, exit" is selected by default).
wait_for "input box" 'pane | grep -q -E "❯|trust"'
if pane | grep -q "Yes, I trust"; then
  tmux send-keys -t "$TMUX_SESSION" Down; sleep 0.5; tmux send-keys -t "$TMUX_SESSION" Enter
  wait_for "input box after trust prompt" '! pane | grep -q "Yes, I trust"'
  sleep 2
fi

send 'Make three separate Bash calls, one per command. Do not combine them or run them in the background. First: sleep 8; echo STEP_1 / Second: sleep 8; echo STEP_2 / Third: sleep 8; echo STEP_3 / When all three are done, reply with only FIRST_DONE.'

wait_for "first tool call" '[[ -n "$(transcript)" ]] && grep -q "\"tool_use\"" "$(transcript)"'
send '/next Make two separate Bash calls. Do not combine them or run them in the background. First: sleep 5; echo S_1 / Second: sleep 5; echo S_2 / When both are done, reply with only SECOND_DONE.'
send '/next Reply with only THIRD_DONE.'

wait_for "THIRD_DONE reply" \
  'jq -e "select(.type==\"assistant\") | .message.content[]? | select(.type==\"text\" and (.text|contains(\"THIRD_DONE\")))" "$(transcript)" >/dev/null 2>&1'
sleep 1

f="$(transcript)"
# Flatten each line into {i, kind, text, tools}. queue-operation lines aren't model input, so they get their own kind.
events="$(jq -c --slurp '
  to_entries | map(.key as $i | .value | {
    i: $i,
    kind: (if .type == "queue-operation" then "queue:" + .operation
           elif .type == "assistant" then "assistant"
           elif (.message.content | type) == "string" and (.message.content | contains("<command-name>/next</command-name>")) then "next-command"
           else .type end),
    text: (if .type == "assistant" then ([.message.content[]? | select(.type == "text") | .text] | join(""))
           else (tostring) end),
    tools: (if .type == "assistant" then ([.message.content[]? | select(.type == "tool_use")] | length) else 0 end)
  })' "$f")"

done_at() { jq --arg m "$1" '[.[] | select(.kind == "assistant" and (.text | contains($m)))][0].i // -1' <<<"$events"; }
# Number of model-input lines (queue-operation excluded) before index $1 that match $2
leaks_before() { jq --argjson d "$1" --arg re "$2" '[.[] | select((.kind | startswith("queue:")) | not) | select(.i < $d and (.text | test($re)))] | length' <<<"$events"; }

first_done="$(done_at FIRST_DONE)"
second_done="$(done_at SECOND_DONE)"
enqueued_before="$(jq --argjson d "$first_done" '[.[] | select(.kind == "queue:enqueue" and .i < $d and (.text | test("SECOND_DONE|THIRD_DONE")))] | length' <<<"$events")"
leaked_first="$(leaks_before "$first_done" "SECOND_DONE|THIRD_DONE")"
leaked_second="$(leaks_before "$second_done" "THIRD_DONE")"
second_start="$(jq '[.[] | select(.kind == "next-command")][0].i // -1' <<<"$events")"
second_tools="$(jq --argjson a "$second_start" --argjson b "$second_done" '[.[] | select(.i > $a and .i < $b) | .tools] | add // 0' <<<"$events")"
order="$(jq -r '[.[] | select(.kind == "assistant" and (.text | test("FIRST_DONE|SECOND_DONE|THIRD_DONE"))) | .text | capture("(?<t>FIRST_DONE|SECOND_DONE|THIRD_DONE)").t] | join(" -> ")' <<<"$events")"
next_turns="$(jq '[.[] | select(.kind == "next-command")] | length' <<<"$events")"

fail=0
check() { if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; fail=1; fi; }
echo "Results (transcript: $f)"
check "first turn ended with FIRST_DONE"                                        '[[ $first_done -ge 0 ]]'
check "both /next were queued during the first turn ($enqueued_before/2)"         '[[ $enqueued_before -eq 2 ]]'
check "neither /next reached Claude during the first turn (leaks: $leaked_first)"  '[[ $leaked_first -eq 0 ]]'
check "the first /next used tools ($second_tools tool calls)"                     '[[ $second_tools -ge 1 ]]'
check "the second /next didn't reach Claude during the first /next (leaks: $leaked_second)" '[[ $second_done -ge 0 && $leaked_second -eq 0 ]]'
check "each /next ran as its own turn ($next_turns/2)"                            '[[ $next_turns -eq 2 ]]'
check "reply order: $order"                                                      '[[ "$order" == "FIRST_DONE -> SECOND_DONE -> THIRD_DONE" ]]'

if [[ $fail -eq 0 ]]; then echo "PASS"; else echo "FAIL"; exit 1; fi
