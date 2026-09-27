<div align="center">

# /next

**Queue your next request in Claude Code without interrupting the one in progress.**

English · [한국어](README.ko.md) · [日本語](README.ja.md)

<img src="assets/demo-en.gif" width="960" alt="Recorded in Claude Code. With Enter, 'add a test for an empty list' lands right after the fix, before the tests ran, and both requests end in one reply. With /next, it waits while Claude fixes the bug and runs the tests, then runs as a new turn.">

</div>

## Install

```bash
npx claude-next-skill
```

Or paste this into Claude Code (or any coding agent) and let it install for you:

```text
Install the /next skill for Claude Code by running `npx -y claude-next-skill`.
If npx isn't available, download https://raw.githubusercontent.com/Seokwoooo/claude-next/main/skills/next/SKILL.md and save it unchanged as ~/.claude/skills/next/SKILL.md.
When it's done, tell me to open a new Claude Code session.
```

Open a new Claude Code session after installing.

## Usage

While Claude is working, type:

```text
/next run the tests and fix anything that fails
```

It waits until the current turn ends, then runs as a new turn.

- **Queue several:** press Enter after each one. They run in order, one turn each.
- **Cancel:** with the input box empty, press `↑`, delete the line, and press Enter. Don't use `Ctrl+C` for this, it stops Claude.

## Why

While Claude is working, a normal message is handed to Claude as soon as the current tool call finishes, in the middle of the task. Slash commands wait until the turn ends ([docs](https://code.claude.com/docs/en/interactive-mode#when-claude-code-sends-what-you-queued)). `/next` is a one-line skill built on that.

<details>
<summary><b>How it works</b></summary>

This is the whole skill ([`skills/next/SKILL.md`](skills/next/SKILL.md)):

```markdown
---
name: next
description: Queue a follow-up request that runs after the current turn finishes.
argument-hint: <next request>
disable-model-invocation: true
---

Treat the following as the user's follow-up request and carry it out now, continuing from the current conversation: $ARGUMENTS
```

- Claude Code's command queue does the waiting. The skill only hands over your request when its turn comes.
- `disable-model-invocation: true` means only you can run it. Claude never sees it in its skill list, so it costs no context until you use it.

</details>

<details>
<summary><b>Update, uninstall, manual install</b></summary>

- Update: run `npx claude-next-skill` again.
- Uninstall: `npx claude-next-skill uninstall`
- Without Node: save [`skills/next/SKILL.md`](skills/next/SKILL.md) as `~/.claude/skills/next/SKILL.md` (on Windows, `%USERPROFILE%\.claude\skills\next\SKILL.md`).

</details>

<details>
<summary><b>Tested</b></summary>

[`tests/verify.sh`](tests/verify.sh) drives a real Claude Code session in tmux, queues two `/next` commands during a multi-step task, and reads the session transcript to check what reached Claude and when. It passes on Claude Code 2.1.283 (macOS):

```text
✓ both /next were queued during the first turn (2/2)
✓ neither /next reached Claude during the first turn (leaks: 0)
✓ the second /next didn't reach Claude during the first /next (leaks: 0)
✓ each /next ran as its own turn (2/2)
✓ reply order: FIRST_DONE -> SECOND_DONE -> THIRD_DONE
```

Run it again after updating Claude Code (needs `tmux` and `jq`).

</details>

<details>
<summary><b>Limits</b></summary>

- It waits for the main turn to end, not for background tasks Claude started.
- Permission prompts still apply.
- It's a personal skill, so it works in local sessions on your machine, not in cloud sessions.

</details>

## License

[MIT](LICENSE)
