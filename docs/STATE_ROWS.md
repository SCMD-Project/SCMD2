# SCMD 2.0 状态行模型

SCMD 2.0 禁止为多个独立开关 / 参数枚举整个页面状态。

错误模型：

```text
8 switches  -> 2^8  = 256 pages
16 switches -> 2^16 = 65536 pages
```

正确模型：

```text
page
  -> row_fps()
  -> row_impacts()
  -> row_timescale()
  -> row_volume()
```

每个 row 独立维护：

- 一个 SCMD 状态变量 / selector；
- 一个 renderer function；
- 一个公开 action / cycle action；
- 必要时一个 page-local action-and-render wrapper；
- 一个 `+N` usage/help entry。

复杂度近似 O(N)。

## Boolean row

游戏镜像状态约定：

```text
0 = unknown
1 = off
2 = on
```

输出：

```text
[?]
[OFF]
[ON]
```

## Multi-state row

例如无限弹药：

```text
0 = unknown
1 = off
2 = infinite, reload retained
3 = infinite, no reload
```

输出：

```text
[?]
[OFF]
[换弹]
[无限]
```

## Parameter / preset row

例如时间流速：

```text
=4.时间流速 [0.1,0.25,0.5,(1),2]
```

括号表示 SCMD 当前 selector。未知时：

```text
=4.时间流速 [0.1,0.25,0.5,1,2,(?)]
```

菜单数字循环预设；`+数字` 打印真实 Console command、参数形式和示例，但不会切页：

```text
+4
-> host_timescale {数字}
-> host_timescale 0.75
```

普通 CFG 无法可靠读取所有外部实时 ConVar，因此状态只在 SCMD 明确建立后才标为已知。用户在 SCMD 外部修改同一 ConVar 后可能使镜像变旧；SCMD 不伪造“实时读取”。
