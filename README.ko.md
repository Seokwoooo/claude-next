<div align="center">

# /next

**Claude Code가 작업하는 동안 다음 요청을 예약하세요. 지금 하는 작업은 방해하지 않습니다.**

[English](README.md) · 한국어 · [日本語](README.ja.md)

<img src="assets/demo-ko.gif" width="960" alt="실제 Claude Code 녹화. Enter로 보내면 'add a test for an empty list'가 버그 수정 직후, 테스트를 돌리기도 전에 끼어들고 두 요청이 한 답변으로 끝납니다. /next로 보내면 Claude가 버그를 고치고 테스트를 돌리는 동안 기다렸다가 새 턴으로 실행됩니다.">

</div>

## 설치

```bash
npx claude-next-skill
```

또는 아래 내용을 Claude Code(다른 코딩 에이전트도 됩니다)에 붙여 넣으면 알아서 설치합니다.

```text
Claude Code용 /next 스킬을 설치해줘. `npx -y claude-next-skill`을 실행하면 돼.
npx를 쓸 수 없으면 https://raw.githubusercontent.com/Seokwoooo/claude-next/main/skills/next/SKILL.md 를 내려받아서 내용을 바꾸지 말고 ~/.claude/skills/next/SKILL.md 로 저장해줘.
끝나면 Claude Code 세션을 새로 열라고 알려줘.
```

설치한 뒤에는 Claude Code 세션을 새로 여세요.

## 사용법

Claude가 작업하는 중에 이렇게 입력하세요.

```text
/next 테스트 돌리고 실패하는 거 고쳐줘
```

지금 턴이 끝날 때까지 기다렸다가 새 턴으로 실행됩니다.

- **여러 개 예약:** 하나 입력할 때마다 Enter를 누르세요. 넣은 순서대로 하나씩 실행됩니다.
- **취소:** 입력창이 비어 있을 때 `↑`를 누르고, 그 줄을 지운 뒤 Enter를 누르세요. 이때 `Ctrl+C`는 쓰지 마세요. Claude의 작업이 멈춥니다.

## 왜 필요한가

Claude가 작업하는 중에 보낸 일반 메시지는 진행 중인 도구 호출이 끝나는 즉시, 작업 도중에 Claude에게 전달됩니다. 슬래시 명령은 턴이 끝날 때까지 기다립니다([공식 문서](https://code.claude.com/docs/en/interactive-mode#when-claude-code-sends-what-you-queued)). `/next`는 이 점을 활용한 한 줄짜리 스킬입니다.

<details>
<summary><b>동작 원리</b></summary>

스킬 전체가 이게 다입니다([`skills/next/SKILL.md`](skills/next/SKILL.md)).

```markdown
---
name: next
description: Queue a follow-up request that runs after the current turn finishes.
argument-hint: <next request>
disable-model-invocation: true
---

Treat the following as the user's follow-up request and carry it out now, continuing from the current conversation: $ARGUMENTS
```

- 기다리는 일은 Claude Code의 명령 대기열이 합니다. 스킬은 자기 차례가 오면 요청을 넘겨줄 뿐입니다.
- `disable-model-invocation: true`라서 사용자만 실행할 수 있습니다. Claude는 스킬 목록에서 이 스킬을 볼 수 없고, 쓰기 전까지는 컨텍스트도 차지하지 않습니다.
- 본문은 영어지만 요청은 입력한 언어 그대로 전달됩니다.

</details>

<details>
<summary><b>업데이트 · 제거 · 수동 설치</b></summary>

- 업데이트: `npx claude-next-skill`을 다시 실행하세요.
- 제거: `npx claude-next-skill uninstall`
- Node 없이 설치: [`skills/next/SKILL.md`](skills/next/SKILL.md)를 `~/.claude/skills/next/SKILL.md`로 저장하세요(Windows는 `%USERPROFILE%\.claude\skills\next\SKILL.md`).

</details>

<details>
<summary><b>검증</b></summary>

[`tests/verify.sh`](tests/verify.sh)는 tmux 안에서 실제 Claude Code 세션을 띄웁니다. 여러 단계 작업이 도는 동안 `/next` 두 개를 넣고, 세션 기록을 읽어 무엇이 언제 Claude에게 전달됐는지 확인합니다. Claude Code 2.1.283(macOS)에서 통과했습니다.

```text
✓ both /next were queued during the first turn (2/2)
✓ neither /next reached Claude during the first turn (leaks: 0)
✓ the second /next didn't reach Claude during the first /next (leaks: 0)
✓ each /next ran as its own turn (2/2)
✓ reply order: FIRST_DONE -> SECOND_DONE -> THIRD_DONE
```

Claude Code를 업데이트한 뒤 다시 돌려 보세요(`tmux`, `jq` 필요).

</details>

<details>
<summary><b>한계</b></summary>

- 메인 턴이 끝나기를 기다립니다. Claude가 백그라운드로 돌려 둔 작업까지 기다리지는 않습니다.
- 권한 확인은 그대로 적용됩니다.
- 개인 스킬이라 내 컴퓨터의 로컬 세션에서만 동작하고, 클라우드 세션에서는 쓸 수 없습니다.

</details>

## 라이선스

[MIT](LICENSE)
