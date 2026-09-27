#!/usr/bin/env python3
"""Generates assets/hero-{en,ko,ja}.svg: an animated Enter-vs-/next comparison.

Run: python3 assets/hero.py
The base (non-animated) attributes hold the final frame, so viewers without
animation (or with reduced motion) still see the whole story.
"""
from pathlib import Path

W, H = 880, 400  # canvas size

STRINGS = {
    "en": dict(
        header="You type a follow-up while Claude is still working",
        sub1="plain message", sub2="queued command",
        segs=("lint", "test", "build", "reply"),
        chip="release note", typed="typed mid-task",
        mid="delivered mid-task", mixed="mixed reply", out1="✕  2 requests, 1 reply",
        queued="queued", turn_end="turn ends", out2="✓  runs as its own turn",
    ),
    "ko": dict(
        header="Claude가 작업하는 중에 다음 요청을 입력하면",
        sub1="일반 메시지", sub2="대기열 명령",
        segs=("lint", "test", "build", "답변"),
        chip="릴리스 노트", typed="작업 중 입력",
        mid="작업 중간에 끼어듦", mixed="섞인 답변", out1="✕  요청 2개, 답변 1개",
        queued="대기 중", turn_end="턴 종료", out2="✓  끝난 뒤 따로 실행",
    ),
    "ja": dict(
        header="Claude の作業中に次の依頼を入力すると",
        sub1="通常メッセージ", sub2="キューのコマンド",
        segs=("lint", "test", "build", "返答"),
        chip="リリースノート", typed="作業中に入力",
        mid="作業の途中に割り込む", mixed="混ざった返答", out1="✕  依頼2つ、返答1つ",
        queued="待機中", turn_end="ターン終了", out2="✓  完了後に単独で実行",
    ),
}

SANS = ("-apple-system,BlinkMacSystemFont,'Segoe UI','Apple SD Gothic Neo','Malgun Gothic',"
        "'Hiragino Sans','Yu Gothic','Noto Sans CJK KR','Noto Sans CJK JP','Noto Sans',sans-serif")
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

C = dict(bg="#0d1117", lane="#161b22", line="#30363d", seg="#21262d", text="#e6edf3", dim="#8b949e",
         run="#d97757", red="#f85149", redfill="#da3633", green="#3fb950", greenfill="#238636", chip="#388bfd")

# Story timeline, in seconds from when the task starts
LINT, TEST, BUILD, REPLY = (0.3, 2.0), (2.0, 3.8), (3.8, 5.4), (5.4, 6.4)
CHIP_IN = 0.9
END = 7.4  # every element has reached its final state by now

# The loop opens on the finished picture, so a paused or unanimated render still tells the whole story.
# It then fades out, resets while invisible (RESET), plays the story from START, and holds the result.
RESET, START = 2.15, 2.4
LOOP = START + END + 1.6

SEG_X, SEG_W, GAP = 200, 120, 8
TRACK_Y, TRACK_H = 60, 32
SLOT_X = SEG_X + 4 * (SEG_W + GAP)  # 712: right-hand slot for the queued chip
CHIP_W = 120
CHIP_START = (SLOT_X, 14)
BOUNDARY = SEG_X + SEG_W + GAP // 2  # between lint and test
CHIP_MID = (BOUNDARY - CHIP_W // 2, TRACK_Y - 24)  # lands on the lint|test boundary
CHIP_QUEUED = (SLOT_X + 8, TRACK_Y)


def pct(t):
    return f"{t / LOOP * 100:.2f}%"


class Anim:
    """Collects @keyframes rules and gives each animated element its own class."""

    def __init__(self):
        self.rules = []

    def add(self, name, frames, extra="", story=True):
        if story:  # frames run from story time 0 (initial state) to END (final state)
            first, last = frames[0][1], frames[-1][1]
            frames = ([(0, last), (RESET, last), (RESET + 0.01, first)]
                      + [(START + t, p) for t, p in frames] + [(LOOP, last)])
        body = " ".join(f"{pct(t)}{{{props}}}" for t, props in frames)
        self.rules.append(f"@keyframes {name}{{{body}}}")
        self.rules.append(f".{name}{{animation:{name} {LOOP}s linear infinite;{extra}}}")
        return name


def seg_progress(anim, lane, i, span):
    start, end = span
    return anim.add(f"p{lane}{i}", [
        (0, "transform:scaleX(0)"), (start, "transform:scaleX(0)"),
        (end, "transform:scaleX(1)"), (END, "transform:scaleX(1)"),
    ], "transform-box:fill-box;transform-origin:0 50%")


def appear(anim, name, at, dur=0.3):
    return anim.add(name, [
        (0, "opacity:0"), (at, "opacity:0"), (at + dur, "opacity:1"), (END, "opacity:1"),
    ])


def move(anim, name, start, stops):
    """stops: list of (t0, t1, (x, y)) moves, positions relative to the element's final spot."""
    frames = [(0, f"transform:translate({start[0]}px,{start[1]}px)")]
    pos = start
    for t0, t1, dest in stops:
        frames.append((t0, f"transform:translate({pos[0]}px,{pos[1]}px)"))
        frames.append((t1, f"transform:translate({dest[0]}px,{dest[1]}px)"))
        pos = dest
    frames.append((END, f"transform:translate({pos[0]}px,{pos[1]}px)"))
    return anim.add(name, frames)


def text(x, y, s, size=13, fill=C["dim"], weight=400, anchor="start", font=SANS, cls="", extra=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{c}{extra}>{s}</text>')


def lane(anim, n, y, s, name, name_color):
    out = [f'<g transform="translate(0,{y})">',
           f'<rect x="16" y="0" width="{W - 32}" height="136" rx="12" fill="{C["lane"]}"/>',
           text(36, 66, name, 28, name_color, 700, font=MONO),
           text(36, 92, s["sub1"] if n == 1 else s["sub2"], 13)]

    spans = (LINT, TEST, BUILD, REPLY)
    for i, label in enumerate(s["segs"]):
        x = SEG_X + i * (SEG_W + GAP)
        out.append(f'<rect x="{x}" y="{TRACK_Y}" width="{SEG_W}" height="{TRACK_H}" rx="6" '
                   f'fill="{C["seg"]}" stroke="{C["line"]}"/>')
        cls = seg_progress(anim, n, i, spans[i])
        fill = C["run"]
        if n == 1 and i == 3:  # lane 1's reply turns red once it's done: two answers in one
            red = anim.add("mixfill", [(0, f"fill:{C['run']}"), (REPLY[1], f"fill:{C['run']}"),
                                       (REPLY[1] + 0.3, f"fill:{C['redfill']}"), (END, f"fill:{C['redfill']}")])
            out.append(f'<g class="{cls}"><rect class="{red}" x="{x}" y="{TRACK_Y}" width="{SEG_W}" '
                       f'height="{TRACK_H}" rx="6" fill="{C["redfill"]}"/></g>')
            before = anim.add("mixlabel0", [(0, "opacity:1"), (REPLY[1], "opacity:1"),
                                            (REPLY[1] + 0.3, "opacity:0"), (END, "opacity:0")])
            after = appear(anim, "mixlabel1", REPLY[1])
            cx = x + SEG_W / 2
            out.append(text(cx, TRACK_Y + 21, label, 13, C["text"], 600, "middle", MONO, before, ' opacity="0"'))
            out.append(text(cx, TRACK_Y + 21, s["mixed"], 12, "#ffffff", 700, "middle", SANS, after))
            continue
        out.append(f'<rect class="{cls}" x="{x}" y="{TRACK_Y}" width="{SEG_W}" height="{TRACK_H}" '
                   f'rx="6" fill="{fill}"/>')
        out.append(text(x + SEG_W / 2, TRACK_Y + 21, label, 13, C["text"], 600, "middle", MONO))

    # "typed mid-task" hint next to where the chip first shows up
    hint = anim.add(f"hint{n}", [(0, "opacity:0"), (CHIP_IN, "opacity:0"), (CHIP_IN + 0.3, "opacity:1"),
                                 (CHIP_IN + 1.2, "opacity:1"), (CHIP_IN + 1.5, "opacity:0"), (END, "opacity:0")])
    out.append(text(CHIP_START[0] - 10, CHIP_START[1] + 20, s["typed"], 12, C["dim"], 400, "end", cls=hint,
                    extra=' opacity="0"'))

    if n == 1:
        end = CHIP_MID
        mv = move(anim, "chip1", (CHIP_START[0] - end[0], CHIP_START[1] - end[1]),
                  [(LINT[1], LINT[1] + 0.4, (0, 0))])
        stroke = anim.add("hit", [(0, f"stroke:{C['chip']}"), (LINT[1] + 0.35, f"stroke:{C['chip']}"),
                                  (LINT[1] + 0.45, f"stroke:{C['red']}"), (END, f"stroke:{C['red']}")])
        chip_fill = C["chip"]
        call = appear(anim, "mid", LINT[1] + 0.4)
        out.append(f'<line class="{call}" x1="{BOUNDARY}" y1="{TRACK_Y + 6}" x2="{BOUNDARY}" y2="{TRACK_Y + TRACK_H + 4}" '
                   f'stroke="{C["red"]}" stroke-width="3" stroke-linecap="round"/>')
        out.append(text(BOUNDARY, TRACK_Y + TRACK_H + 26, "▲ " + s["mid"], 12, C["red"], 600,
                        "middle", cls=call))
        res = appear(anim, "out1", REPLY[1] + 0.2)
        out.append(text(W - 36, TRACK_Y + TRACK_H + 26, s["out1"], 13, C["red"], 700, "end", cls=res))
        chip_cls = f"{mv}"
        rect_extra = f' class="{stroke}" stroke-width="2.5"'
    else:
        end = CHIP_QUEUED
        mv = move(anim, "chip2", (CHIP_START[0] - end[0], CHIP_START[1] - end[1]),
                  [(CHIP_IN + 0.5, CHIP_IN + 0.9, (0, 0))])
        # waits dashed & dim, then becomes a solid green turn of its own
        wait = anim.add("wait", [(0, "opacity:1"), (CHIP_IN + 0.9, "opacity:1"), (2.6, "opacity:.45"),
                                 (3.6, "opacity:1"), (4.6, "opacity:.45"), (5.6, "opacity:1"), (END, "opacity:1")])
        fill = anim.add("go", [(0, f"fill:{C['chip']};stroke:{C['chip']};stroke-dasharray:none"),
                               (CHIP_IN + 0.9, f"fill:{C['lane']};stroke:{C['dim']};stroke-dasharray:5 4"),
                               (REPLY[1], f"fill:{C['lane']};stroke:{C['dim']};stroke-dasharray:5 4"),
                               (REPLY[1] + 0.3, f"fill:{C['greenfill']};stroke:{C['green']};stroke-dasharray:none"),
                               (END, f"fill:{C['greenfill']};stroke:{C['green']};stroke-dasharray:none")])
        q = anim.add("queued", [(0, "opacity:0"), (CHIP_IN + 0.9, "opacity:0"), (CHIP_IN + 1.1, "opacity:1"),
                                (REPLY[1], "opacity:1"), (REPLY[1] + 0.2, "opacity:0"), (END, "opacity:0")])
        out.append(text(end[0] + CHIP_W / 2, TRACK_Y - 10, s["queued"] + " …", 12, C["dim"], 600, "middle",
                        cls=q, extra=' opacity="0"'))
        div = appear(anim, "div", REPLY[1])
        out.append(f'<g class="{div}"><line x1="{SLOT_X + 2}" y1="{TRACK_Y - 16}" x2="{SLOT_X + 2}" '
                   f'y2="{TRACK_Y + TRACK_H + 8}" stroke="{C["green"]}" stroke-width="1.5" stroke-dasharray="4 4"/>'
                   + text(SLOT_X - 4, TRACK_Y - 10, s["turn_end"], 12, C["green"], 600, "end") + "</g>")
        res = appear(anim, "out2", REPLY[1] + 0.4)
        out.append(text(W - 36, TRACK_Y + TRACK_H + 26, s["out2"], 13, C["green"], 700, "end", cls=res))
        chip_cls = f"{mv} {wait}"
        chip_fill = C["greenfill"]
        rect_extra = f' class="{fill}" stroke="{C["green"]}" stroke-width="1.5"'

    chip_in = appear(anim, f"chipin{n}", CHIP_IN)
    stroke_attr = "" if n == 2 else f' stroke="{C["red"]}"'
    out.append(f'<g class="{chip_in}"><g class="{chip_cls}">'
               f'<rect x="{end[0]}" y="{end[1]}" width="{CHIP_W}" height="{TRACK_H}" rx="16" '
               f'fill="{chip_fill}"{stroke_attr}{rect_extra}/>'
               + text(end[0] + CHIP_W / 2, end[1] + 21, s["chip"], 13, "#ffffff", 600, "middle")
               + "</g></g>")
    out.append("</g>")
    return "\n".join(out)


def build(lang):
    s = STRINGS[lang]
    anim = Anim()
    body = [
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="{C["bg"]}" stroke="{C["line"]}"/>',
        text(32, 44, s["header"], 17, C["text"], 600),
        lane(anim, 1, 64, s, "Enter", C["red"]),
        lane(anim, 2, 220, s, "/next", C["green"]),
        text(W - 32, H - 20, "claude-next", 12, "#484f58", 600, "end", MONO),
    ]
    scene = anim.add("scene", [(0, "opacity:1"), (RESET - 0.35, "opacity:1"), (RESET - 0.05, "opacity:0"),
                               (START - 0.1, "opacity:0"), (START + 0.1, "opacity:1"), (LOOP, "opacity:1")],
                     story=False)
    css = "\n".join(anim.rules)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" lang="{lang}">
<title>Enter vs /next</title>
<desc>{s["header"]}: Enter — {s["mid"]}, {s["out1"][3:]}. /next — {s["queued"]}, {s["out2"][3:]}.</desc>
<style>
{css}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
{body[0]}
<g class="{scene}">
{chr(10).join(body[1:])}
</g>
</svg>
'''


if __name__ == "__main__":
    here = Path(__file__).parent
    for lang in STRINGS:
        (here / f"hero-{lang}.svg").write_text(build(lang), encoding="utf-8")
        print(f"wrote {here / f'hero-{lang}.svg'}")
