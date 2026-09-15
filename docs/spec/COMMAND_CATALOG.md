# SCMD 2.0 实用命令全集（精选分类）

这里的“全集”指 **对玩家、CFG 作者、跑图、Demo、服务器管理有实际价值的命令集合**。
故意排除 crash、schema、动画内部、渲染器内部、物理内部、自动化测试框架等低价值开发项。

标记：
- `[CHEATS]`：通常要求 `sv_cheats 1` / 本地环境。
- `[SERVER]`：作用于本地/服务端规则。
- `[DANGER]`：可能破坏用户配置、踢人、退出等，菜单不应一键裸执行。
- `[INFO]`：主要输出信息。

---

## A. CFG / Console

- `alias` — 定义 alias。
- `exec` — 执行 CFG。
- `execifexists` — 文件存在时执行 CFG。
- `exec_async` — 异步/分时执行 CFG。`[CHEATS]`
- `clear` — 清空 Console。
- `clearall` — 清空所有 Console view。
- `echo` — 输出文本。
- `echoln` — 输出一行文本。
- `find` — 按名称/帮助搜索命令。
- `findflags` — 按 flags 搜索命令。
- `help` — 查询命令帮助。
- `grep` — 对输出进行模式过滤。
- `cvarlist` — 列出全部 ConVar / ConCommand。
- `differences` — 显示与默认值不同的 ConVar。
- `print_changed_convars` — 输出已修改 ConVar。
- `toggle` — 切换 ConVar 值。
- `cyclevar` — 在多个值间循环。
- `incrementvar` — 数值增加/减少。
- `multvar` — 数值乘法。
- `push_var_values` — 保存一组当前 ConVar/config 值。
- `pop_var_values` — 恢复之前保存的值。
- `host_writeconfig` — 保存用户配置。
- `writekeybindings` — 保存当前按键绑定。
- `repeat_last_console_command` — 重复上一条 Console 命令。
- `log` — 日志开关。
- `log_flags` — 调整 logging channel flags。
- `log_level` — 调整 logging channel level。
- `log_dumpchannels` — 列出 logging channels。`[INFO]`

---

## B. 按键 / 输入 / 武器槽位

- `bind`
- `unbind`
- `unbindall` `[DANGER]`
- `binddefaults` `[DANGER]`
- `button_info` `[INFO]`
- `key_findbinding` `[INFO]`
- `key_listboundkeys` `[INFO]`
- `lastinv`
- `invnext`
- `invprev`
- `switchhands`
- `switchhandsleft`
- `switchhandsright`
- `buymenu`
- `teammenu`
- `+lookatweapon`
- `+spray_menu`
- `+radialradio`
- `+radialradio2`
- `+radialradio3`
- `+cl_show_team_equipment`
- 常用 bind target：`+attack`、`+attack2`、`+jump`、`+duck`、`+sprint`、`+use`、`+reload`、`+voicerecord`

---

## C. 地图 / 会话

- `maps` `[INFO]`
- `map <name>`
- `changelevel <name>`
- `map_workshop`
- `ds_workshop_changelevel`
- `ds_workshop_listmaps` `[INFO]`
- `connect <address>`
- `connect_hltv`
- `disconnect`
- `timeleft` `[INFO]`
- `pause`
- `unpause`
- `game_alias`
- `quit` `[DANGER]`

---

## D. 游戏 / 回合 / 比赛

命令：
- `mp_warmup_start`
- `mp_warmup_end`
- `mp_pause_match`
- `mp_unpause_match`
- `mp_swapteams`
- `mp_scrambleteams`
- `mp_backup_restore_list_files`
- `mp_backup_restore_load_file`

实用 ConVar：
- `mp_restartgame`
- `mp_freezetime`
- `mp_roundtime`
- `mp_roundtime_defuse`
- `mp_roundtime_hostage`
- `mp_round_restart_delay`
- `mp_buy_anywhere`
- `mp_buytime`
- `mp_startmoney`
- `mp_maxmoney`
- `mp_afterroundmoney`
- `mp_limitteams`
- `mp_autoteambalance`
- `mp_ignore_round_win_conditions`
- `mp_friendlyfire`
- `mp_forcecamera`
- `mp_free_armor`
- `mp_max_armor`
- `mp_respawn_on_death_t`
- `mp_respawn_on_death_ct`
- `mp_respawn_immunitytime`
- `mp_weapons_allow_typecount`
- `mp_weapons_allow_zeus`
- `mp_c4timer`
- `mp_maxrounds`

---

## E. 练习 / Cheats

- `noclip` `[CHEATS]`
- `god` `[CHEATS]`
- `healme <amount>` `[CHEATS]`
- `hurtme <amount>` `[CHEATS]`
- `give <item>` `[LOCAL/CHEATS]`
- `givecurrentammo` `[CHEATS]`
- `getpos` `[CHEATS/INFO]`
- `getpos_exact` `[CHEATS/INFO]`
- `getposcopy` `[CHEATS/INFO]`
- `getposcopy_exact` `[CHEATS/INFO]`
- `sv_rethrow_last_grenade` `[CHEATS]`
- `sv_kill_smokegrenade` `[CHEATS]`
- `plant_bomb` `[CHEATS]`
- `kill` `[CHEATS]`
- `sv_infinite_ammo`
- `sv_grenade_trajectory_prac_pipreview`
- `sv_grenade_trajectory_prac_trailtime`
- `sv_grenade_trajectory_time_spectator`
- `sv_showimpacts`
- `sv_showimpacts_penetration`
- `sv_showimpacts_time`
- `sv_showhitregistration`
- `ammo_grenade_limit_total`
- `sv_gravity`

---

## F. 人机

- `bot_add`
- `bot_add_t`
- `bot_add_ct`
- `bot_kick`
- `bot_kill`
- `bot_place` `[CHEATS]`
- `bot_all_weapons`
- `bot_knives_only`
- `bot_pistols_only`
- `bot_snipers_only`
- `bot_goto_mark` `[CHEATS]`
- `bot_goto_selected` `[CHEATS]`
- `bot_path` `[CHEATS]`

常用 ConVar（发布前实机确认当前语义）：
- `bot_stop`
- `bot_mimic`
- `bot_mimic_yaw_offset`
- `bot_difficulty`

---

## G. 武器 / 购买

- `give <item>`
- `weapon_switch <weapon_name>`
- `givecurrentammo`
- `autobuy`
- `rebuy`
- `buy`
- `buyrandom`
- `buymenu`
- `sellbackall`
- `debug_purchase_defidx`（偏调试，不放主菜单）

相关规则：
- `mp_buy_anywhere`
- `mp_buytime`
- `mp_buy_allow_grenades`
- `mp_buy_allow_guns`
- `mp_weapons_allow_typecount`
- `mp_weapons_allow_zeus`
- `mp_weapons_allow_pistols`
- `mp_weapons_allow_rifles`
- `mp_weapons_allow_smgs`

---

## H. Demo / 观战

- `playdemo`
- `demoui`
- `demo_pause`
- `demo_resume`
- `demo_togglepause`
- `demo_step_tick`
- `demo_timescale`
- `demo_goto`
- `demo_gotomark`
- `demo_gototick`
- `demo_marktick`
- `demo_info`
- `demolist`
- `listdemo`
- `nextdemo`
- `timedemo`
- `timedemoquit`
- `firstperson`
- `thirdperson` `[CHEATS]`

---

## I. 显示 / HUD / 状态

- `cl_showfps`（ConVar）
- `cl_printfps` `[INFO]`
- `cl_ticktiming` `[INFO]`
- `cl_showpos`（ConVar）
- `+cl_show_team_equipment`
- `toggleradarscale`
- `hideradar`
- `drawradar`
- `gameui_hide`
- `gameui_activate`
- `net_status` `[INFO]`
- `net_channels` `[INFO]`

---

## J. 准星 / 视角

准星常用 ConVar：
- `crosshair`
- `cl_crosshairstyle`
- `cl_crosshairsize`
- `cl_crosshairthickness`
- `cl_crosshairgap`
- `cl_crosshairusealpha`
- `cl_crosshairalpha`
- `cl_crosshaircolor`
- `cl_crosshaircolor_r`
- `cl_crosshaircolor_g`
- `cl_crosshaircolor_b`
- `cl_crosshair_drawoutline`
- `cl_crosshair_outlinethickness`
- `cl_crosshairdot`
- `cl_crosshair_t`
- `cl_crosshair_friendly_warning`
- `cl_show_observer_crosshair`
- `cl_crosshair_sniper_width`

视角：
- `viewmodel_fov`
- `viewmodel_offset_x`
- `viewmodel_offset_y`
- `viewmodel_offset_z`
- `viewmodel_presetpos`
- `firstperson`
- `thirdperson` `[CHEATS]`

---

## K. 声音 / 语音

- `volume`
- `snd_mute_losefocus`
- `snd_voipvolume`
- `snd_menumusic_volume`
- `snd_mvp_volume`
- `snd_tensecondwarning_volume`
- `snd_roundstart_volume`
- `snd_roundend_volume`
- `snd_deathcamera_volume`
- `voice_modenable`
- `voice_modenable_toggle`
- `voice_toggle_open_mic`
- `voice_loopback`
- `+voicerecord`
- `play <sound>`
- `playvol`

---

## L. 聊天 / 通信

- `say`
- `say_team`
- `messagemode`
- `messagemode2`
- `player_ping`
- `callvote`
- `listissues`

---

## M. 网络 / 状态

- `status`
- `net_status`
- `net_channels`
- `net_connections_stats`
- `net_showudp`
- `net_option`
- `timeleft`
- `users`
- `sys_info`
- `cpuinfo`（偏信息）
- `cl_ticktiming`

不把 net fake lag/loss 之类放普通主菜单；高级用户可在“全部命令”看到说明。

---

## N. 截图 / 位置 / 记录

- `getpos`
- `getpos_exact`
- `getposcopy`
- `getposcopy_exact`
- `screenshot`
- `png_screenshot`
- `jpeg_screenshot`
- `_record`
- `tv_record`
- `tv_stoprecord`
- `record` / `stop`（若当前 build 注册，发布前以 cvarlist 快照确认）

---

## O. Workshop / 地图

- `map_workshop`
- `ds_workshop_changelevel`
- `ds_workshop_listmaps`
- `host_workshop_map`
- `host_workshop_collection`
- `print_mapgroup`
- `print_mapgroup_sv`
- `maps`
- `changelevel`

---

## P. 服务端 / 管理

这些只放“全部命令”，不作为普通玩家快捷按钮：
- `kick`
- `kickid`
- `banid`
- `banip`
- `listid`
- `listip`
- `writeid`
- `writeip`
- `sv_shutdown`
- `tv_status`
- `tv_clients`
- `tv_broadcast_status`
- `mp_disable_autokick`
- `mp_pause_match`
- `mp_unpause_match`

危险操作必须二次确认。
