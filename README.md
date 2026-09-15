# SCMD 2.0 Beta 3

**SCMD — Shortcut Command** 的 CS2 重制版。

Beta 3 的运行实现仍然是 **SCMD 源码 → scmdc 0.10.0 → 纯 CFG / alias package**。菜单 CFG 没有手写；`tools/generate_scmd2.py` 只负责维护大量重复的 SCMD 源码，最终 CS2 运行文件全部由 `scmdc` 生成。

## 直接运行

把部署包完整解压到：

```text
Counter-Strike Global Offensive/game/csgo/cfg/
```

然后在 CS2 Console：

```text
exec scmd
```

全局菜单规则：

```text
0     返回
00    刷新当前菜单
+序号  查看当前菜单项对应的命令 / 参数 / 示例
```

例如在练习工具页：

```text
=4.时间流速 [0.1,0.25,0.5,(1),2]
```

输入：

```text
4
```

循环到下一个预设；输入：

```text
+4
```

不会换页，而是在当前菜单下面显示：

```text
[SCMD] 时间流速
命令: host_timescale {数字}
说明: 输入 4 循环预设；也可直接输入任意合法数字 [LOCAL/CHEATS]
示例: host_timescale 0.75
```

括号表示 SCMD 最近一次明确设置的预设。普通 CFG 无法可靠读取所有外部实时 ConVar，因此 SCMD 尚未建立状态时显示 `(?)`，不会伪造真实值。

## Beta 3：菜单缺字 / clear 时序修复

真实 CS2 中已经确认过原生 `clear` 与后续 Console 输出存在时序竞争：菜单可能顶部缺字、混行或截断。Beta 3 不再默认每页都直接调用 `clear`。

首选项新增三态清屏模式：

```text
=1.清屏模式 [关闭,(软清屏),原生]
```

- **关闭**：不清屏。
- **软清屏（默认）**：打印 24 个空行滚动旧内容，不调用 `clear`，因此不依赖 async / cheats，也避开已知 clear race。
- **原生**：仍使用 `clear`，但由 scmdc async console backend 生成 `clear -> sleep 32ms -> continuation`，用于希望保留真正 clear 的本地环境。

默认使用软清屏，所以普通菜单路径不会再依赖 `sv_cheats 1` 才能正确显示。

## 参数状态行

Beta 3 把独立状态行扩展成参数 / 预设状态行。每项独立维护自己的 selector，不枚举整页组合，因此仍是近似 O(N)。

已实现：

- 时间流速：`0.1 / 0.25 / 0.5 / 1 / 2`
- Demo 速度：`0.25 / 0.5 / 1 / 2 / 4`
- 准星样式：`0..5`
- 准星大小：`1..5`
- 准星粗细：`0.5 / 1 / 1.5 / 2`
- 准星间距：`-3 / -1 / 0 / 1 / 3`
- 准星颜色：`1..5`
- 狙击准星宽度：`1..4`
- Viewmodel FOV：`54 / 60 / 68`
- Viewmodel 位置预设：`1 / 2 / 3`
- 主音量：`0 / 0.25 / 0.5 / 0.75 / 1`
- 菜单音乐 / MVP 音乐 / 十秒警告：`0 / 0.25 / 0.5 / 1`

二态开关继续使用 `[?] / [ON] / [OFF]`；无限弹药继续使用 `[?] / [换弹] / [无限] / [OFF]`。

## 快速跑图

保留五套初始化：

1. 标准跑图
2. 投掷物练习
3. 枪械练习
4. 人机练习
5. 纯净跑图

快速跑图 **永远不会自动绑定任何按键**。需要快捷键必须由用户主动进入“按键与快捷键”。

跑图 preset 会显式设置 `host_timescale 1`，所以初始化后练习工具页可可信地显示：

```text
=4.时间流速 [0.1,0.25,0.5,(1),2]
```

## 武器 / 命令 / 绑定

- 16 个主菜单分类和完整二 / 三级页。
- “全部命令”按 16 大类整理实用 CS2 命令，不把 Source 2 内部开发垃圾全部塞入菜单。
- 武器既有分类页，也有 47 项“全部武器”长页。
- 24 个预设绑定目标 + 8 个 `scmd_custom1..8` 自定义目标。
- 21 个常用按键，共 672 条显式绑定路径；只有用户主动进入绑定菜单才会执行 `bind`。
- 公开 `scmd_*` Command ABI 供用户手动 bind。

用户永久自定义命令放在：

```text
Scmd/Custom.cfg
```

例如：

```cfg
alias scmd_custom1 "say hello"
alias scmd_custom2 "toggle cl_showfps 0 1"
```

## 从源码构建

需要 SCMD Toolchain 0.10.0：

```powershell
python tools/generate_scmd2.py
scmdc build scmd.scmdproj
python tools/verify_generated.py
python tools/verify_beta3.py --sim C:\path\to\scmdsim.exe
```

`scmdsim` 0.10.0 的 CFG-root 模式是 lazy compile：模拟器可以瞬间进入 Console；某个 CFG 第一次 `exec` 时才编译。运行中新增 / 修改 CFG 后也能直接再次 `exec`，不需要重启 simulator。

## 已知边界

`scmdsim` 验证 SCMD / CFG / alias / menu control flow，只模拟当前 backend 依赖的 CS2 Console 子集。`give`、`bot_place`、具体 `mp_*` / `sv_*` / Demo / audio / crosshair 原生命令仍要真实 CS2 做 compatibility pass。

菜单状态表示 **SCMD 最近一次明确建立的状态**；如果用户在 SCMD 外部手动修改同一个 ConVar，普通 CFG 没有通用读取 API 可以自动同步，因此状态可能需要重新由 SCMD 建立。
