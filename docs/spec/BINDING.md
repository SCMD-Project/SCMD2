# SCMD 2.0 按键绑定设计

## 原则

- 安装 SCMD：不绑定任何键。
- 执行“快速跑图”：不绑定任何键。
- 只有用户主动进入绑定向导时才触碰 bind。
- 覆盖一个已有绑定前必须提示。
- 永远绑定 SCMD 的公开 alias ABI，而不是编译器内部名字。

## 两种目标

### 1. 预设命令

建议可绑定：
- `scmd_menu`
- `scmd_practice`
- `scmd_noclip`
- `scmd_rethrow`
- `scmd_bot_place`
- `scmd_bot_freeze`
- `scmd_bot_mimic`
- `scmd_bot_clear`
- `scmd_impacts`
- `scmd_trajectory`
- `scmd_showpos`
- `scmd_god`
- `scmd_heal`
- `scmd_round_restart`
- `scmd_warmup_end`
- `scmd_fps`
- `scmd_crosshair`
- `scmd_demo_pause`
- `scmd_demo_half`
- `scmd_demo_normal`
- `scmd_demo_double`
- `scmd_voice_toggle`

### 2. 自定义命令

固定槽：
- `scmd_custom1`
- ...
- `scmd_custom8`

用户自己：

```cfg
alias scmd_custom1 "say hello"
```

以后改 alias body 不需要重新绑定按键。

## “按下下一个键”捕获向导

SCMD 不能读取任意下一个输入字符串，但可以临时抢占一组候选键作为捕获器。

流程：
1. 用户选“绑定放置人机”。
2. 保存/记录当前 bind 情况。
3. 临时将候选键绑定到各自 capture alias。
4. 提示用户关闭 Console 后按一个键。
5. 某个 capture alias 触发。
6. 恢复其他临时 bind。
7. 明确将被选中的键 bind 到目标公开 alias。
8. 显示完成页。

第一版候选键建议：
- F1–F12
- 0–9
- Insert/Delete/Home/End/PageUp/PageDown
- Arrow keys
- Mouse3/Mouse4/Mouse5

不要为整张键盘生成几百个选项。

## 手动绑定永远保留

例如：

```cfg
bind p scmd_bot_place
bind n scmd_noclip
bind mouse5 scmd_rethrow
```

这对高级用户比任何向导都更快。
