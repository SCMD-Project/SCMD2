# SCMD 2.0 快速跑图预设

所有预设都只初始化环境，**绝不自动绑定按键**。

## 标准跑图

建议核心：

```cfg
sv_cheats 1
mp_warmup_end
mp_limitteams 0
mp_autoteambalance 0
mp_roundtime 60
mp_roundtime_defuse 60
mp_roundtime_hostage 60
mp_freezetime 0
mp_buy_anywhere 1
mp_buytime 9999
mp_maxmoney 60000
mp_startmoney 60000
mp_afterroundmoney 60000
mp_weapons_allow_typecount -1
ammo_grenade_limit_total 6
mp_ignore_round_win_conditions 1
sv_infinite_ammo 2
bot_kick
mp_restartgame 1
```

说明：
- `sv_infinite_ammo 2` 更适合保留换弹动作；用户可在菜单切到 1。
- `ammo_grenade_limit_total` 当前默认较小，跑图可提高。
- `mp_ignore_round_win_conditions 1` 防止一个人跑图时回合乱结束。

## 投掷物练习

在标准跑图基础上：

```cfg
sv_grenade_trajectory_prac_pipreview 1
sv_grenade_trajectory_prac_trailtime 8
sv_showimpacts 1
sv_showimpacts_time 8
```

快捷动作：
- `sv_rethrow_last_grenade`
- `noclip`
- `bot_place`

## 枪械练习

重点：
- 无限/半无限弹药
- 弹着点
- 购买任意位置
- 高资金
- 长回合
- 可选双方快速重生

可选：

```cfg
sv_showimpacts 1
sv_showimpacts_penetration 1
mp_respawn_on_death_t 1
mp_respawn_on_death_ct 1
```

## 人机练习

重点：
- 关闭队伍人数限制
- 关闭自动平衡
- 长回合
- 用户自行添加、放置、冻结人机
- 不自动开启 bot mimic

## 纯净跑图

只改变最必要的环境：
- cheats
- 回合时间
- freeze
- buy anywhere / buytime
- money
- grenade limit
- 防止回合自动结束

不主动开：
- 轨迹
- 弹着点
- 无敌
- 人机
- 第三人称

## 恢复练习环境

最稳妥的设计不是“猜默认值并全部写回”，而是：
1. 进入快速跑图前用 `push_var_values` 保存相关 ConVar（若目标环境可靠支持）；
2. 恢复时 `pop_var_values`；
3. 或最简单地提示用户重新加载地图/自己的 CFG。

SCMD 不应假装能完美恢复一个它没有完整快照的复杂用户环境。
