#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "main.scmd"
BUILD = ROOT / "build"
PAGES = BUILD / "Scmd" / "pages"
ASYNC = BUILD / "Scmd" / "async" / "000.cfg"
MANIFEST = BUILD / "Scmd" / "manifest.json"

EXPECTED_ROOT = [
    "菜单\\快捷指令", "菜单\\全部命令", "菜单\\武器与装备", "菜单\\自定义指令",
    "菜单\\快速跑图", "菜单\\练习工具", "菜单\\人机控制", "菜单\\Demo与观战",
    "菜单\\地图与会话", "菜单\\显示与HUD", "菜单\\准星与视角", "菜单\\声音与语音",
    "菜单\\按键与快捷键", "菜单\\CFG与控制台", "菜单\\首选项", "关于SCMD",
]
KEYS = ["f1","f2","f3","f4","f5","f6","f7","f8","f9","f10","f11","f12","ins","del","home","end","pgup","pgdn","mouse3","mouse4","mouse5"]
TARGETS = [
    "scmd_menu","scmd_quick","scmd_practice","scmd_practice_tools","scmd_bots","scmd_weapons",
    "scmd_noclip","scmd_rethrow","scmd_bot_place","scmd_bot_freeze","scmd_bot_mimic","scmd_bot_clear",
    "scmd_fps","scmd_impacts","scmd_trajectory","scmd_showpos","scmd_ammo","scmd_god","scmd_smoke_clear",
    "scmd_round_restart","scmd_warmup_end","scmd_demo_pause","scmd_crosshair","scmd_voice_toggle",
] + [f"scmd_custom{i}" for i in range(1, 9)]


def fail(msg: str) -> None:
    print(f"VERIFY_BETA3_FAIL: {msg}")
    raise SystemExit(1)


def run_sim(sim: Path, script_text: str, *, startup: str = "scmd") -> str:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(script_text)
        script = Path(f.name)
    try:
        cp = subprocess.run(
            [str(sim), str(BUILD), "--exec", startup, "--script", str(script),
             "--no-interactive", "--no-ansi", "--no-engine-messages", "--max-commands", "10000000"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            check=False,
        )
        if cp.returncode != 0:
            fail(f"scmdsim exit={cp.returncode}: {cp.stderr.strip()}")
        return cp.stdout
    finally:
        script.unlink(missing_ok=True)


def require(out: str, text: str, what: str | None = None) -> None:
    if text not in out:
        fail(what or f"missing output: {text}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", type=Path, required=True)
    args = ap.parse_args()
    sim = args.sim.resolve()
    if not sim.is_file():
        fail(f"simulator missing: {sim}")

    source = SRC.read_text(encoding="utf-8")
    if "SCMD 2.0 BETA 3 SOURCE" not in source:
        fail("wrong generated source version")
    if not PAGES.is_dir():
        fail("build/Scmd/pages missing; run scmdc build first")

    # Build metadata / clear-race hardening.
    manifest = MANIFEST.read_text(encoding="utf-8")
    if '"settle_ms": 32' not in manifest or '"mode": "async"' not in manifest:
        fail("project did not compile with async console settle=32ms")
    if not ASYNC.is_file():
        fail("async clear worker missing")
    async_text = ASYNC.read_text(encoding="utf-8")
    if "clear\nsleep 32\n" not in async_text:
        fail("native-clear async worker is not clear -> sleep 32 -> continuation")
    if "u8 pref_clear_mode = 1;" not in source:
        fail("default clear mode is not soft-clear")
    screen_m = re.search(r"function screen_begin\(\)\s*\{(?P<body>.*?)\n\}", source, re.S)
    if not screen_m or screen_m.group("body").count('console.print("");') < 20:
        fail("soft-clear renderer is missing")

    # +N help slots must be reset independently from normal numeric slots.
    for i in range(1, 51):
        if f'command.exec("alias +{i} scmd_noop");' not in source:
            fail(f"+{i} is not reset by reset_slots")
    if "=+序号.查看指令/用法" not in source:
        fail("menu footer does not advertise +N help")

    # Parameter state/preset definitions are source-level, independent row renderers.
    for fn in [
        "row_practice_timescale", "row_demo_speed", "row_cross_style", "row_cross_size",
        "row_cross_thick", "row_cross_gap", "row_cross_color", "row_cross_sniper",
        "row_view_fov", "row_view_preset", "row_sound_volume", "row_sound_menu_music",
        "row_sound_mvp", "row_sound_tensec", "row_pref_clear",
    ]:
        if f"function {fn}()" not in source:
            fail(f"missing parameter row renderer: {fn}")

    # Binding matrix still complete; no install/practice auto-bind path was introduced.
    for key in KEYS:
        for target in TARGETS:
            if f'command.exec("bind {key} {target}");' not in source:
                fail(f"missing bind matrix entry: {key} -> {target}")
    if len(KEYS) * len(TARGETS) != 672:
        fail("binding matrix size changed unexpectedly")

    pages = "\n".join(p.read_text(encoding="utf-8") for p in sorted(PAGES.glob("*.cfg")))
    fn_count = len(re.findall(r"^function [A-Za-z0-9_]+\(\)", source, re.M))
    for i in range(fn_count):
        if f"alias __scmd_fn{i} " not in pages:
            fail(f"generated CFG missing __scmd_fn{i}")

    # Root navigation.
    out = run_sim(sim, "".join(f"{i}\n0\n" for i in range(1, 17)))
    for title in EXPECTED_ROOT:
        require(out, f"=|SCMD 2.0:\\{title}", f"root page did not render: {title}")

    # +N help is page-local and does not clear/navigate away.
    out = run_sim(sim, "+1\n1\n+13\n")
    require(out, "[SCMD] 快捷指令")
    require(out, "命令: scmd_quick")
    require(out, "[SCMD] 菜单项目 13")
    require(out, "命令: cl_showfps {0|1}")
    if out.count("=|SCMD 2.0:\\菜单\\快捷指令") != 1:
        fail("+13 help unexpectedly re-rendered or navigated away from current menu")

    # Old +N alias must not leak after page switch. +13 on practice-tools is deliberately unassigned.
    out = run_sim(sim, "1\n+13\n0\n6\n+13\n")
    if out.count("命令: cl_showfps {0|1}") != 1:
        fail("stale +13 help alias leaked into another page")

    # Timescale row: unknown -> presets; +4 shows syntax.  Practice preset seeds the documented 1x state.
    out = run_sim(sim, "6\n+4\n4\n4\n0\n5\n2\n8\n")
    for text in [
        "=4.时间流速 [0.1,0.25,0.5,1,2,(?)]",
        "命令: host_timescale {数字}",
        "示例: host_timescale 0.75",
        "=4.时间流速 [(0.1),0.25,0.5,1,2]",
        "=4.时间流速 [0.1,(0.25),0.5,1,2]",
        "=4.时间流速 [0.1,0.25,0.5,(1),2]",
    ]:
        require(out, text, f"timescale state/help missing: {text}")

    # Demo speed row.
    out = run_sim(sim, "8\n+6\n6\n6\n")
    for text in [
        "=6.Demo速度 [0.25,0.5,1,2,4,(?)]",
        "命令: demo_timescale {数字}",
        "=6.Demo速度 [(0.25),0.5,1,2,4]",
        "=6.Demo速度 [0.25,(0.5),1,2,4]",
    ]:
        require(out, text, f"demo speed missing: {text}")

    # Crosshair inline parameter row.
    out = run_sim(sim, "11\n+2\n2\n2\n")
    for text in [
        "=2.准星样式 [0,1,2,3,4,5,(?)]",
        "命令: cl_crosshairstyle {数字}",
        "=2.准星样式 [(0),1,2,3,4,5]",
        "=2.准星样式 [0,(1),2,3,4,5]",
    ]:
        require(out, text, f"crosshair preset missing: {text}")

    # Sound inline parameter row.
    out = run_sim(sim, "12\n+1\n1\n1\n")
    for text in [
        "=1.主音量 [0,0.25,0.5,0.75,1,(?)]",
        "命令: volume {数字}",
        "=1.主音量 [(0),0.25,0.5,0.75,1]",
        "=1.主音量 [0,(0.25),0.5,0.75,1]",
    ]:
        require(out, text, f"sound preset missing: {text}")

    # Clear-mode preference: soft by default, native selectable, and reset goes back to soft.
    out = run_sim(sim, "15\n1\n1\n3\n")
    for text in [
        "=1.清屏模式 [关闭,(软清屏),原生]",
        "=1.清屏模式 [关闭,软清屏,(原生)]",
        "=1.清屏模式 [(关闭),软清屏,原生]",
    ]:
        require(out, text, f"clear mode state missing: {text}")

    # All-weapons long page still complete.
    out = run_sim(sim, "3\n1\n00\n")
    require(out, "=1.AK-47")
    require(out, "=47.Healthshot")

    page_count = len(list(PAGES.glob("*.cfg")))
    if page_count >= 1000:
        fail(f"CFG page budget exceeded: {page_count}")

    print("VERIFY_BETA3_PASS")
    print(f"functions={fn_count}")
    print(f"binding_matrix={len(KEYS)}x{len(TARGETS)}={len(KEYS)*len(TARGETS)}")
    print(f"cfg_pages={page_count}")
    print("help_slots=+1..+50")
    print("native_clear_settle_ms=32")
    print("default_clear_mode=soft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
