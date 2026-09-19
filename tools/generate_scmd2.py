from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional, Union

SCRIPT = Path(__file__).resolve()
OUT = SCRIPT.parents[1]
SRC = OUT / 'src'
TOOLS = OUT / 'tools'
SRC.mkdir(parents=True, exist_ok=True)
TOOLS.mkdir(parents=True, exist_ok=True)

@dataclass
class Func:
    name: str
    body: Union[list[str], Callable[[dict[str,int]], list[str]]]
    command_alias: Optional[str] = None

funcs: list[Func] = []
name_to_func: dict[str, Func] = {}

def addf(name, body, alias=None):
    if name in name_to_func:
        raise ValueError(name)
    f = Func(name, body, alias)
    funcs.append(f)
    name_to_func[name] = f
    return name

def qtext(s: str) -> str:
    if '"' in s or '\n' in s or '\r' in s:
        raise ValueError(f'unsupported SCMD text: {s!r}')
    # SCMD string literals unescape "\\" -> "\" once (frontend/parser.c). The
    # 0.13.0 cfg loader preserves backslashes literally ("Console CFG is not a
    # C string literal"), so one doubling encodes one runtime backslash.
    # The 0.10.0-era loader unescaped a second time, which is why this used to
    # emit four backslashes per intended one.
    return s.replace('\\', '\\\\')

def pr(s: str) -> str:
    return f'console.print("{qtext(s)}");'

def cmd(s: str) -> str:
    if '"' in s or '\n' in s or '\r' in s:
        raise ValueError(f'unsupported command string: {s!r}')
    return f'command.exec("{qtext(s)}");'

def comment(s: str) -> str:
    return f'// {s}'

# ---------------------------------------------------------------------------
# Globals: 0 unknown, 1 OFF, 2 ON for mirrored game state unless noted.
# ---------------------------------------------------------------------------
globals_src = '''
// SCMD 2.0 runtime state.
// For game state mirrors: 0 = unknown, 1 = off, 2 = on.
u8 st_fps = 0;
u8 st_hud = 0;
u8 st_crosshair = 0;
u8 st_impacts = 0;
u8 st_trajectory = 0;
u8 st_showpos = 0;
u8 st_god = 0;
u8 st_bot_stop = 0;
u8 st_bot_mimic = 0;
u8 st_voice = 0;
u8 st_loopback = 0;
u8 st_mute_losefocus = 0;
u8 st_dot = 0;
u8 st_outline = 0;
u8 st_tcross = 0;
// ammo: 0 unknown, 1 off, 2 reload-mode, 3 infinite-without-reload.
u8 st_ammo = 0;
// Preset selectors: 0 = unknown unless a documented default is safe.
u8 st_timescale = 0;       // 0.1,0.25,0.5,1,2
u8 st_demo_speed = 0;      // 0.25,0.5,1,2,4
u8 st_cross_style = 0;
u8 st_cross_size = 0;
u8 st_cross_thickness = 0;
u8 st_cross_gap = 0;
u8 st_cross_color = 0;
u8 st_sniper_width = 0;
u8 st_view_fov = 0;         // 54,60,68
u8 st_view_preset = 0;
u8 st_volume = 0;           // 0,0.25,0.5,0.75,1
u8 st_menu_music = 0;
u8 st_mvp_music = 0;
u8 st_tensec = 0;
// 0 none, otherwise binding target id.
u8 bind_target = 0;

// clear mode: 0 none, 1 soft scroll clear, 2 native clear (delayed async).
u8 pref_clear_mode = 1;
bool pref_tips = true;
'''.strip()

# ---------------------------------------------------------------------------
# Helpers (internal SCMD calls are safe; they are never directly exposed).
# ---------------------------------------------------------------------------
reset_lines = [comment('Clear numeric menu aliases so handlers from the previous page cannot leak.')]
reset_lines += [cmd('alias 0 scmd_noop'), cmd('alias 00 scmd_noop')]
reset_lines += [cmd(f'alias {i} scmd_noop') for i in range(1, 51)]
reset_lines += [cmd(f'alias +{i} scmd_noop') for i in range(1, 51)]
addf('reset_slots', reset_lines)

addf('screen_begin', [
    'if(pref_clear_mode == 1)',
    '{',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '    console.print("");',
    '}',
    'else if(pref_clear_mode == 2)',
    '{',
    '    console.clear();',
    '}',
])

addf('noop', [], 'scmd_noop')

# ---------------------------------------------------------------------------
# Help metadata. Every menu slot gets a +N helper alias.
# ---------------------------------------------------------------------------
help_registry: dict[str, tuple[str, str, str]] = {}
help_serial = 0

def register_help(alias: Optional[str], syntax: str, description: str = '', example: str = ''):
    if alias:
        help_registry[alias] = (syntax, description, example)

def ensure_help(text: str, target: str, explicit: Optional[str] = None) -> str:
    global help_serial
    if explicit:
        return explicit
    help_serial += 1
    alias = f'scmd_h_{help_serial}'
    syntax, desc, example = help_registry.get(target, (target, f'执行或打开: {text}', ''))
    body = [
        pr('--------------------------------'),
        pr(f'[SCMD] {text}'),
        pr(f'命令: {syntax}'),
    ]
    if desc:
        body.append(pr(f'说明: {desc}'))
    if example:
        body.append(pr(f'示例: {example}'))
    body += [pr('提示: 输入 00 可刷新当前菜单'), pr('--------------------------------')]
    addf(f'help_{help_serial}', body, alias)
    return alias

# ---------------------------------------------------------------------------
# Generic action builders.
# ---------------------------------------------------------------------------

def add_action(name, commands, message=None, alias=None, render=None, extra_lines=None, usage=None, description=None, example=None):
    lines = []
    for c in commands:
        lines.append(cmd(c))
    if extra_lines:
        lines.extend(extra_lines)
    if render:
        lines.append(cmd(render))
    if message:
        lines += [
            'if(pref_tips)',
            '{',
            '    ' + pr(message),
            '}',
        ]
    if alias:
        syntax = usage or (commands[0] if len(commands) == 1 else alias)
        desc = description or (message.replace('[SCMD] ', '') if message else (f'组合动作，共 {len(commands)} 条命令' if len(commands) > 1 else '执行该命令'))
        register_help(alias, syntax, desc, example or '')
    return addf(name, lines, alias)


def add_toggle(name, state, on_cmd, off_cmd, label, alias=None):
    # Public toggle actions never force a menu render. This keeps public scmd_*
    # commands suitable for key binds. Menu-specific wrappers call the toggle
    # and then re-render their own page.
    lines = [
        f'if({state} == 2)',
        '{',
        '    ' + cmd(off_cmd),
        f'    {state} = 1;',
        '    if(pref_tips)',
        '    {',
        '        ' + pr(f'[SCMD] {label}: OFF'),
        '    }',
        '}',
        'else',
        '{',
        '    ' + cmd(on_cmd),
        f'    {state} = 2;',
        '    if(pref_tips)',
        '    {',
        '        ' + pr(f'[SCMD] {label}: ON'),
        '    }',
        '}',
    ]
    if alias:
        command_name = on_cmd.split()[0]
        register_help(alias, f'{command_name} {{0|1}}', f'切换{label}；菜单状态表示 SCMD 最近一次设置', f'{command_name} 1')
    return addf(name, lines, alias)

def add_toggle_page_action(name, toggle_func, page_alias, alias):
    pub = name_to_func[toggle_func].command_alias if toggle_func in name_to_func else None
    if pub and pub in help_registry:
        help_registry[alias] = help_registry[pub]
    return addf(name, [f'{toggle_func}();', cmd(page_alias)], alias)

def add_preset_cycle(name, state, command_name, values, label, alias, description='', example=''):
    lines=[]
    for i,value in enumerate(values,1):
        nxt = i + 1 if i < len(values) else 1
        kw = 'if' if i == 1 else 'else if'
        lines += [f'{kw}({state} == {i})','{','    '+cmd(f'{command_name} {values[nxt-1]}'),f'    {state} = {nxt};','}']
    lines += ['else','{','    '+cmd(f'{command_name} {values[0]}'),f'    {state} = 1;','}']
    register_help(alias, f'{command_name} {{数字}}', description or f'输入菜单序号循环 {label} 预设；也可手动输入任意合法数值', example or f'{command_name} {values[0]}')
    return addf(name, lines, alias)

def add_cycle_page_action(name, cycle_func, page_alias, alias):
    pub = name_to_func[cycle_func].command_alias if cycle_func in name_to_func else None
    if pub and pub in help_registry:
        help_registry[alias] = help_registry[pub]
    return addf(name, [f'{cycle_func}();', cmd(page_alias)], alias)

def preset_row_text(num, text, values, selected):
    shown=[]
    for i,v in enumerate(values,1):
        shown.append(f'({v})' if selected == i else str(v))
    if selected == 0:
        shown.append('(?)')
    return f'={num}.{text} [' + ','.join(shown) + ']'

def add_preset_row_renderer(name, state, num, text, values):
    body=[]
    for i in range(1,len(values)+1):
        kw='if' if i==1 else 'else if'
        body += [f'{kw}({state} == {i})','{','    '+pr(preset_row_text(num,text,values,i)),'}']
    body += ['else','{','    '+pr(preset_row_text(num,text,values,0)),'}']
    addf(name, body)
    return name

# Stable public actions.
add_action('a_clear_console', ['clear'], alias='scmd_clear')
add_action('a_disconnect', ['disconnect'], alias='scmd_disconnect')
add_action('a_buy_menu', ['buymenu'], alias='scmd_buymenu')
add_action('a_team_menu', ['teammenu'], alias='scmd_teammenu')
add_action('a_switchhands', ['switchhands'], alias='scmd_switchhands')
add_action('a_noclip', ['noclip'], '[SCMD] 已切换飞行', alias='scmd_noclip')
add_action('a_rethrow', ['sv_rethrow_last_grenade'], '[SCMD] 已重新投掷', alias='scmd_rethrow')
add_action('a_bot_place', ['bot_place'], '[SCMD] 已执行 bot_place', alias='scmd_bot_place')
add_action('a_bot_clear', ['bot_kick all'], '[SCMD] 已清除全部人机', alias='scmd_bot_clear')
add_action('a_round_restart', ['mp_restartgame 1'], '[SCMD] 正在重新开始回合', alias='scmd_round_restart')
add_action('a_warmup_end', ['mp_warmup_end'], '[SCMD] 已结束热身', alias='scmd_warmup_end')
add_action('a_getpos', ['getpos'], alias='scmd_showpos_once')
add_action('a_getposcopy', ['getposcopy_exact'], alias='scmd_poscopy')
add_action('a_smoke_clear', ['sv_kill_smokegrenade'], '[SCMD] 已清除烟雾', alias='scmd_smoke_clear')
add_action('a_heal', ['healme 100'], '[SCMD] 已执行治疗', alias='scmd_heal')
add_action('a_kill', ['kill'], alias='scmd_kill')

# Human-facing usage metadata for common actions.
register_help('scmd_noclip','noclip','切换飞行模式 [LOCAL/CHEATS]','noclip')
register_help('scmd_rethrow','sv_rethrow_last_grenade','重新投掷上一个投掷物 [LOCAL/CHEATS]','sv_rethrow_last_grenade')
register_help('scmd_bot_place','bot_place','在准星位置放置一个现有人机 [LOCAL/CHEATS]','bot_place')
register_help('scmd_round_restart','mp_restartgame {秒}','重新开始当前回合','mp_restartgame 1')
register_help('scmd_showpos_once','getpos','输出当前位置','getpos')
register_help('scmd_poscopy','getposcopy_exact','输出可复制的精确位置','getposcopy_exact')
register_help('scmd_smoke_clear','sv_kill_smokegrenade','清除当前烟雾 [LOCAL/CHEATS]','sv_kill_smokegrenade')
register_help('scmd_heal','healme {数字}','恢复指定生命值 [LOCAL/CHEATS]','healme 100')

# Dynamic toggles.
# Render aliases are defined later but are plain console command names, so forward reference is fine.
add_toggle('t_fps', 'st_fps', 'cl_showfps 1', 'cl_showfps 0', 'FPS显示', alias='scmd_fps')
add_toggle('t_hud', 'st_hud', 'cl_drawhud 1', 'cl_drawhud 0', 'HUD显示', alias='scmd_hud')
add_toggle('t_crosshair', 'st_crosshair', 'crosshair 1', 'crosshair 0', '准星显示', alias='scmd_crosshair')
add_toggle('t_impacts', 'st_impacts', 'sv_showimpacts 1', 'sv_showimpacts 0', '弹着点', alias='scmd_impacts')
add_toggle('t_trajectory', 'st_trajectory', 'sv_grenade_trajectory_prac_pipreview 1', 'sv_grenade_trajectory_prac_pipreview 0', '投掷物轨迹', alias='scmd_trajectory')
add_toggle('t_showpos', 'st_showpos', 'cl_showpos 1', 'cl_showpos 0', '位置显示', alias='scmd_showpos')
add_toggle('t_god', 'st_god', 'god 1', 'god 0', '无敌', alias='scmd_god')
add_toggle('t_bot_stop', 'st_bot_stop', 'bot_stop 1', 'bot_stop 0', '冻结人机', alias='scmd_bot_freeze')
add_toggle('t_bot_mimic', 'st_bot_mimic', 'bot_mimic 1', 'bot_mimic 0', '人机模仿', alias='scmd_bot_mimic')
add_toggle('t_voice', 'st_voice', 'voice_modenable 1', 'voice_modenable 0', '语音接收', alias='scmd_voice_toggle')
add_toggle('t_loopback', 'st_loopback', 'voice_loopback 1', 'voice_loopback 0', '麦克风回放', alias='scmd_voice_loopback')
add_toggle('t_mute_losefocus', 'st_mute_losefocus', 'snd_mute_losefocus 1', 'snd_mute_losefocus 0', '失焦静音', alias='scmd_mute_losefocus')
add_toggle('t_dot', 'st_dot', 'cl_crosshairdot 1', 'cl_crosshairdot 0', '准星中心点', alias='scmd_crosshair_dot')
add_toggle('t_outline', 'st_outline', 'cl_crosshair_drawoutline 1', 'cl_crosshair_drawoutline 0', '准星描边', alias='scmd_crosshair_outline')
add_toggle('t_tcross', 'st_tcross', 'cl_crosshair_t 1', 'cl_crosshair_t 0', 'T形准星', alias='scmd_crosshair_t')

# Ammo 3-state cycle.
addf('t_ammo', [
    'if(st_ammo == 2)',
    '{',
    '    ' + cmd('sv_infinite_ammo 1'),
    '    st_ammo = 3;',
    '}',
    'else if(st_ammo == 3)',
    '{',
    '    ' + cmd('sv_infinite_ammo 0'),
    '    st_ammo = 1;',
    '}',
    'else',
    '{',
    '    ' + cmd('sv_infinite_ammo 2'),
    '    st_ammo = 2;',
    '}',
    'if(pref_tips)',
    '{',
    '    if(st_ammo == 3)',
    '    {',
    '        ' + pr('[SCMD] 无限弹药: 无限'),
    '    }',
    '    else if(st_ammo == 2)',
    '    {',
    '        ' + pr('[SCMD] 无限弹药: 换弹'),
    '    }',
    '    else',
    '    {',
    '        ' + pr('[SCMD] 无限弹药: OFF'),
    '    }',
    '}',
], 'scmd_ammo')
register_help('scmd_ammo','sv_infinite_ammo {0|1|2}','菜单循环：换弹 / 无限 / OFF；也可以手动设置','sv_infinite_ammo 2')

# Parameter/preset cycles. Numeric menu entries call a page wrapper; public aliases do not force page redraw.
add_preset_cycle('p_timescale','st_timescale','host_timescale',['0.1','0.25','0.5','1','2'],'时间流速','scmd_timescale','调整游戏时间流速 [LOCAL/CHEATS]','host_timescale 0.75')
add_preset_cycle('p_demo_speed','st_demo_speed','demo_timescale',['0.25','0.5','1','2','4'],'Demo速度','scmd_demo_speed','调整 Demo 播放速度','demo_timescale 1')
add_preset_cycle('p_cross_style','st_cross_style','cl_crosshairstyle',['0','1','2','3','4','5'],'准星样式','scmd_cross_style','循环常用准星样式','cl_crosshairstyle 4')
add_preset_cycle('p_cross_size','st_cross_size','cl_crosshairsize',['1','2','3','4','5'],'准星大小','scmd_cross_size','循环常用准星大小','cl_crosshairsize 2.5')
add_preset_cycle('p_cross_thickness','st_cross_thickness','cl_crosshairthickness',['0.5','1','1.5','2'],'准星粗细','scmd_cross_thickness','循环常用准星粗细','cl_crosshairthickness 0.5')
add_preset_cycle('p_cross_gap','st_cross_gap','cl_crosshairgap',['-3','-1','0','1','3'],'准星间距','scmd_cross_gap','循环常用准星间距','cl_crosshairgap -2')
add_preset_cycle('p_cross_color','st_cross_color','cl_crosshaircolor',['1','2','3','4','5'],'准星颜色','scmd_cross_color','循环准星颜色预设','cl_crosshaircolor 4')
add_preset_cycle('p_sniper_width','st_sniper_width','cl_crosshair_sniper_width',['1','2','3','4'],'狙击准星宽度','scmd_sniper_width','循环狙击准星宽度','cl_crosshair_sniper_width 1')
add_preset_cycle('p_view_fov','st_view_fov','viewmodel_fov',['54','60','68'],'Viewmodel FOV','scmd_view_fov','循环 Viewmodel FOV 预设','viewmodel_fov 68')
add_preset_cycle('p_view_preset','st_view_preset','viewmodel_presetpos',['1','2','3'],'Viewmodel预设','scmd_view_preset','循环 Viewmodel 位置预设','viewmodel_presetpos 1')
add_preset_cycle('p_volume','st_volume','volume',['0','0.25','0.5','0.75','1'],'主音量','scmd_volume_cycle','循环主音量预设','volume 0.8')
add_preset_cycle('p_menu_music','st_menu_music','snd_menumusic_volume',['0','0.25','0.5','1'],'菜单音乐','scmd_menu_music_cycle','循环菜单音乐音量预设','snd_menumusic_volume 0.3')
add_preset_cycle('p_mvp_music','st_mvp_music','snd_mvp_volume',['0','0.25','0.5','1'],'MVP音乐','scmd_mvp_music_cycle','循环 MVP 音乐音量预设','snd_mvp_volume 0.5')
add_preset_cycle('p_tensec','st_tensec','snd_tensecondwarning_volume',['0','0.25','0.5','1'],'十秒警告','scmd_tensec_cycle','循环十秒警告音量预设','snd_tensecondwarning_volume 0.5')

# Bot one-shots.
add_action('a_bot_add', ['bot_add'], '[SCMD] 已添加人机', alias='scmd_bot_add')
add_action('a_bot_add_t', ['bot_add_t'], '[SCMD] 已添加T人机', alias='scmd_bot_add_t')
add_action('a_bot_add_ct', ['bot_add_ct'], '[SCMD] 已添加CT人机', alias='scmd_bot_add_ct')
add_action('a_bot_kill', ['bot_kill all'], '[SCMD] 已击杀全部人机', alias='scmd_bot_kill')
add_action('a_bot_all_weapons', ['bot_all_weapons'], '[SCMD] 人机允许全部武器')
add_action('a_bot_pistols', ['bot_pistols_only'], '[SCMD] 人机仅手枪')
add_action('a_bot_snipers', ['bot_snipers_only'], '[SCMD] 人机仅狙击枪')
add_action('a_bot_knives', ['bot_knives_only'], '[SCMD] 人机仅刀')

# Demo actions.
for nm, command, pub in [
    ('demo_toggle', 'demo_togglepause', 'scmd_demo_pause'),
    ('demo_pause', 'demo_pause', None),
    ('demo_resume', 'demo_resume', None),
    ('demo_step', 'demo_step_tick 1', None),
    ('demo_ui', 'demoui', None),
    ('demo_quarter', 'demo_timescale 0.25', 'scmd_demo_quarter'),
    ('demo_half', 'demo_timescale 0.5', 'scmd_demo_half'),
    ('demo_normal', 'demo_timescale 1', 'scmd_demo_normal'),
    ('demo_double', 'demo_timescale 2', 'scmd_demo_double'),
    ('demo_quad', 'demo_timescale 4', 'scmd_demo_quad'),
    ('demo_info', 'demo_info', None),
    ('demo_list', 'demolist', None),
    ('demo_list2', 'listdemo', None),
]:
    add_action('a_'+nm, [command], alias=pub)

# Config/console actions.
add_action('a_key_list', ['key_listboundkeys'])
add_action('a_write_keys', ['writekeybindings'], '[SCMD] 已请求保存按键绑定')
add_action('a_host_writeconfig', ['host_writeconfig'], '[SCMD] 已请求保存用户配置')
add_action('a_differences', ['differences'])
add_action('a_changed', ['print_changed_convars'])
add_action('a_export_cvarlist', ['cvarlist log scmd_cvarlist'], '[SCMD] 已请求导出完整命令表')
add_action('a_reload_custom', ['execifexists Scmd/Custom'], '[SCMD] 已重新加载 Custom.cfg')
add_action('a_reload_scmd', ['exec scmd'], alias='scmd_reload')

# Map/session actions.
for nm, command in [
    ('maps','maps'), ('timeleft','timeleft'), ('pause','pause'), ('unpause','unpause'),
    ('swapteams','mp_swapteams'), ('scramble','mp_scrambleteams'), ('workshop','ds_workshop_listmaps'),
]:
    add_action('a_map_'+nm, [command])

# Sound volume presets and other setting actions.
for suffix, value in [('0','0'),('25','0.25'),('50','0.5'),('75','0.75'),('100','1')]:
    add_action('a_volume_'+suffix, [f'volume {value}'], f'[SCMD] 主音量 {suffix}%')
for suffix, value in [('0','0'),('25','0.25'),('50','0.5'),('100','1')]:
    add_action('a_menu_music_'+suffix, [f'snd_menumusic_volume {value}'], f'[SCMD] 菜单音乐 {suffix}%')
for suffix, value in [('0','0'),('25','0.25'),('50','0.5'),('100','1')]:
    add_action('a_mvp_'+suffix, [f'snd_mvp_volume {value}'], f'[SCMD] MVP音乐 {suffix}%')
for suffix, value in [('0','0'),('25','0.25'),('50','0.5'),('100','1')]:
    add_action('a_tensec_'+suffix, [f'snd_tensecondwarning_volume {value}'], f'[SCMD] 十秒警告音量 {suffix}%')

# Crosshair/viewmodel actions.
for style in [0,1,2,3,4,5]:
    add_action(f'a_cross_style_{style}', [f'cl_crosshairstyle {style}'], f'[SCMD] 准星样式 {style}')
for label, value in [('1','1'),('2','2'),('3','3'),('4','4'),('5','5')]:
    add_action('a_cross_size_'+label, [f'cl_crosshairsize {value}'], f'[SCMD] 准星大小 {value}')
for label, value in [('05','0.5'),('1','1'),('15','1.5'),('2','2')]:
    add_action('a_cross_thick_'+label, [f'cl_crosshairthickness {value}'], f'[SCMD] 准星粗细 {value}')
for label, value in [('m3','-3'),('m1','-1'),('0','0'),('1','1'),('3','3')]:
    add_action('a_cross_gap_'+label, [f'cl_crosshairgap {value}'], f'[SCMD] 准星间距 {value}')
for color in range(1,6):
    add_action(f'a_cross_color_{color}', [f'cl_crosshaircolor {color}'], f'[SCMD] 准星颜色预设 {color}')
for width in [1,2,3,4]:
    add_action(f'a_sniper_width_{width}', [f'cl_crosshair_sniper_width {width}'], f'[SCMD] 狙击准星宽度 {width}')
for fov in [54,60,68]:
    add_action(f'a_view_fov_{fov}', [f'viewmodel_fov {fov}'], f'[SCMD] Viewmodel FOV {fov}')
for preset in [1,2,3]:
    add_action(f'a_view_preset_{preset}', [f'viewmodel_presetpos {preset}'], f'[SCMD] Viewmodel 预设 {preset}')

# ---------------------------------------------------------------------------
# Weapons.
# ---------------------------------------------------------------------------
weapons = [
    ('AK-47','weapon_ak47','ak47'), ('M4A4','weapon_m4a1','m4a4'), ('M4A1-S','weapon_m4a1_silencer','m4a1s'),
    ('Galil AR','weapon_galilar','galilar'), ('FAMAS','weapon_famas','famas'), ('AUG','weapon_aug','aug'), ('SG 553','weapon_sg556','sg553'),
    ('AWP','weapon_awp','awp'), ('SSG 08','weapon_ssg08','ssg08'), ('G3SG1','weapon_g3sg1','g3sg1'), ('SCAR-20','weapon_scar20','scar20'),
    ('MAC-10','weapon_mac10','mac10'), ('MP9','weapon_mp9','mp9'), ('MP7','weapon_mp7','mp7'), ('MP5-SD','weapon_mp5sd','mp5sd'),
    ('UMP-45','weapon_ump45','ump45'), ('P90','weapon_p90','p90'), ('PP-Bizon','weapon_bizon','bizon'),
    ('Nova','weapon_nova','nova'), ('XM1014','weapon_xm1014','xm1014'), ('MAG-7','weapon_mag7','mag7'), ('Sawed-Off','weapon_sawedoff','sawedoff'),
    ('M249','weapon_m249','m249'), ('Negev','weapon_negev','negev'),
    ('Glock-18','weapon_glock','glock'), ('USP-S','weapon_usp_silencer','usps'), ('P2000','weapon_hkp2000','p2000'), ('P250','weapon_p250','p250'),
    ('Dual Berettas','weapon_elite','elite'), ('Five-SeveN','weapon_fiveseven','fiveseven'), ('Tec-9','weapon_tec9','tec9'), ('CZ75-Auto','weapon_cz75a','cz75'),
    ('Desert Eagle','weapon_deagle','deagle'), ('R8 Revolver','weapon_revolver','revolver'),
    ('HE Grenade','weapon_hegrenade','he'), ('Flashbang','weapon_flashbang','flash'), ('Smoke Grenade','weapon_smokegrenade','smoke'),
    ('Molotov','weapon_molotov','molotov'), ('Incendiary Grenade','weapon_incgrenade','inc'), ('Decoy','weapon_decoy','decoy'),
    ('Zeus x27','weapon_taser','zeus'), ('Kevlar','item_kevlar','kevlar'), ('Kevlar + Helmet','item_assaultsuit','assaultsuit'), ('Defuse Kit','item_defuser','defuser'),
    ('Knife','weapon_knife','knife'), ('C4','weapon_c4','c4'), ('Healthshot','weapon_healthshot','healthshot'),
]
weapon_alias = {}
for display, item, key in weapons:
    alias = f'scmd_give_{key}'
    weapon_alias[key] = alias
    add_action('give_'+key, [f'give {item}'], f'[SCMD] give {display}', alias=alias)
add_action('a_give_ammo', ['givecurrentammo'], '[SCMD] 已补充当前武器弹药', alias='scmd_give_ammo')

# Equipment packs.
add_action('pack_ak', ['give item_assaultsuit','give weapon_ak47','give weapon_deagle','give weapon_smokegrenade','give weapon_flashbang','give weapon_molotov','give weapon_hegrenade'], '[SCMD] 已发放 AK 整套')
add_action('pack_m4s', ['give item_assaultsuit','give weapon_m4a1_silencer','give weapon_usp_silencer','give weapon_smokegrenade','give weapon_flashbang','give weapon_incgrenade','give weapon_hegrenade'], '[SCMD] 已发放 M4A1-S 整套')
add_action('pack_m4', ['give item_assaultsuit','give weapon_m4a1','give weapon_usp_silencer','give weapon_smokegrenade','give weapon_flashbang','give weapon_incgrenade','give weapon_hegrenade'], '[SCMD] 已发放 M4A4 整套')
add_action('pack_awp', ['give item_assaultsuit','give weapon_awp','give weapon_deagle'], '[SCMD] 已发放 AWP 整套')
add_action('pack_nades', ['give weapon_smokegrenade','give weapon_flashbang','give weapon_molotov','give weapon_incgrenade','give weapon_hegrenade','give weapon_decoy'], '[SCMD] 已发放投掷物包')

# ---------------------------------------------------------------------------
# Practice presets.
# ---------------------------------------------------------------------------
standard_cmds = [
    'sv_cheats 1','mp_warmup_end','mp_limitteams 0','mp_autoteambalance 0','mp_roundtime 60','mp_roundtime_defuse 60',
    'mp_roundtime_hostage 60','mp_freezetime 0','mp_buy_anywhere 1','mp_buytime 9999','mp_maxmoney 60000','mp_startmoney 60000',
    'mp_afterroundmoney 60000','mp_weapons_allow_typecount -1','ammo_grenade_limit_total 6','mp_ignore_round_win_conditions 1',
    'sv_infinite_ammo 2','host_timescale 1','bot_kick','mp_restartgame 1'
]
add_action('preset_standard', standard_cmds, '[SCMD] 标准跑图环境初始化完成', alias='scmd_practice_standard', render='scmd_practice', extra_lines=['st_ammo = 2;','st_timescale = 4;','st_bot_stop = 0;','st_bot_mimic = 0;'])
add_action('preset_grenade', standard_cmds + ['sv_grenade_trajectory_prac_pipreview 1','sv_grenade_trajectory_prac_trailtime 8','sv_showimpacts 1','sv_showimpacts_time 8'], '[SCMD] 投掷物练习环境初始化完成', alias='scmd_practice_grenade', render='scmd_practice', extra_lines=['st_ammo = 2;','st_timescale = 4;','st_trajectory = 2;','st_impacts = 2;'])
add_action('preset_aim', standard_cmds + ['sv_showimpacts 1','sv_showimpacts_penetration 1','mp_respawn_on_death_t 1','mp_respawn_on_death_ct 1'], '[SCMD] 枪械练习环境初始化完成', alias='scmd_practice_aim', render='scmd_practice', extra_lines=['st_ammo = 2;','st_timescale = 4;','st_impacts = 2;'])
add_action('preset_bot', standard_cmds + ['bot_add_ct'], '[SCMD] 人机练习环境初始化完成', alias='scmd_practice_bot', render='scmd_practice', extra_lines=['st_ammo = 2;','st_timescale = 4;'])
minimal_cmds = ['sv_cheats 1','mp_warmup_end','mp_limitteams 0','mp_autoteambalance 0','mp_roundtime 60','mp_roundtime_defuse 60','mp_freezetime 0','mp_buy_anywhere 1','mp_buytime 9999','mp_maxmoney 60000','mp_startmoney 60000','ammo_grenade_limit_total 6','mp_ignore_round_win_conditions 1','host_timescale 1','mp_restartgame 1']
add_action('preset_minimal', minimal_cmds, '[SCMD] 纯净跑图环境初始化完成', alias='scmd_practice_minimal', render='scmd_practice', extra_lines=['st_timescale = 4;'])

# ---------------------------------------------------------------------------
# Static menus and action menu helpers.
# ---------------------------------------------------------------------------

def state_row(lines, var, num, text, on='ON', off='OFF'):
    lines += [
        f'if({var} == 2)', '{', '    ' + pr(f'={num}.{text} [{on}]'), '}',
        f'else if({var} == 1)', '{', '    ' + pr(f'={num}.{text} [{off}]'), '}',
        'else', '{', '    ' + pr(f'={num}.{text} [?]'), '}',
    ]


def ammo_row(lines, num=12, text='无限弹药'):
    lines += [
        'if(st_ammo == 3)', '{', '    ' + pr(f'={num}.{text} [无限]'), '}',
        'else if(st_ammo == 2)', '{', '    ' + pr(f'={num}.{text} [换弹]'), '}',
        'else if(st_ammo == 1)', '{', '    ' + pr(f'={num}.{text} [OFF]'), '}',
        'else', '{', '    ' + pr(f'={num}.{text} [?]'), '}',
    ]

def add_binary_row_renderer(name, var, num, text, on='ON', off='OFF'):
    body=[]
    state_row(body, var, num, text, on, off)
    addf(name, body)
    return name

def add_ammo_row_renderer(name, num, text='无限弹药'):
    body=[]
    ammo_row(body, num, text)
    addf(name, body)
    return name

def add_bool_row_renderer(name, var, num, text):
    body=[
        f'if({var})', '{', '    ' + pr(f'={num}.{text} [ON]'), '}',
        'else', '{', '    ' + pr(f'={num}.{text} [OFF]'), '}',
    ]
    addf(name, body)
    return name

def render_row(lines, renderer, slot, target):
    # Each dynamic row is an independent SCMD function. The page only composes
    # row renderers, so N independent toggles stay O(N), never O(2^N).
    lines.append(f'{renderer}();')
    lines.append(cmd(f'alias {slot} {target}'))

@dataclass
class Item:
    num: int
    text: str
    target: str  # console alias
    help_alias: Optional[str] = None

@dataclass
class DynamicItem:
    num: int
    renderer: str
    target: str
    text: str = ''
    help_alias: Optional[str] = None


def menu_body(title, sections, parent, self_alias, dynamic_builder=None, footer_notes=None):
    # Allocate +N help aliases when the page is defined, not during source emission.
    help_targets={}
    for _, entries in sections:
        for ent in entries:
            if isinstance(ent, (Item, DynamicItem)):
                help_targets[ent.num] = ensure_help(ent.text if isinstance(ent, Item) else (ent.text or f'菜单项目 {ent.num}'), ent.target, ent.help_alias)

    def build(idx):
        lines = ['screen_begin();', 'reset_slots();', pr('================================'), pr(f'=|SCMD 2.0:\\{title}'), pr('================================')]
        for sec_name, entries in sections:
            if sec_name:
                lines.append(pr(f'={sec_name}:'))
            for ent in entries:
                if isinstance(ent, Item):
                    lines.append(pr(f'={ent.num}.{ent.text}'))
                elif isinstance(ent, DynamicItem):
                    lines.append(f'{ent.renderer}();')
                else:
                    lines.append(pr(str(ent)))
            if sec_name:
                lines.append(pr(''))
        if dynamic_builder:
            dynamic_builder(lines)
        if footer_notes:
            for x in footer_notes:
                lines.append(pr(x))
        lines += [pr('================================'), pr('=0.返回'), pr('=00.刷新'), pr('=+序号.查看指令/用法'), pr('================================')]
        if parent:
            lines.append(cmd(f'alias 0 {parent}'))
        else:
            lines.append(cmd(f'alias 0 {self_alias}'))
        lines.append(cmd(f'alias 00 {self_alias}'))
        for _, entries in sections:
            for ent in entries:
                if isinstance(ent, (Item, DynamicItem)):
                    lines.append(cmd(f'alias {ent.num} {ent.target}'))
                    lines.append(cmd(f'alias +{ent.num} {help_targets[ent.num]}'))
        return lines
    return build

# Placeholder pages are created in logical order. Command aliases form the stable menu ABI.
# Main menu.
addf('menu_main', menu_body('菜单', [
    ('指令', [Item(1,'快捷指令','scmd_quick'), Item(2,'全部命令','scmd_commands'), Item(3,'武器与装备','scmd_weapons'), Item(4,'自定义指令','scmd_custom_menu')]),
    ('练习', [Item(5,'快速跑图','scmd_practice'), Item(6,'练习工具','scmd_practice_tools'), Item(7,'人机控制','scmd_bots'), Item(8,'Demo与观战','scmd_demo')]),
    ('设置', [Item(9,'地图与会话','scmd_map'), Item(10,'显示与HUD','scmd_display'), Item(11,'准星与视角','scmd_crosshair_menu'), Item(12,'声音与语音','scmd_sound'), Item(13,'按键与快捷键','scmd_bind'), Item(14,'CFG与控制台','scmd_cfg')]),
    ('SCMD', [Item(15,'首选项','scmd_preferences'), Item(16,'关于SCMD','scmd_about')]),
], None, 'scmd_menu'), 'scmd_menu')

# Quick menu with dynamic rows.
row_quick_fps = add_binary_row_renderer('row_quick_fps','st_fps',13,'FPS显示')
row_quick_impacts = add_binary_row_renderer('row_quick_impacts','st_impacts',14,'弹着点')
row_quick_trajectory = add_binary_row_renderer('row_quick_trajectory','st_trajectory',15,'投掷物轨迹')
row_quick_showpos = add_binary_row_renderer('row_quick_showpos','st_showpos',16,'位置显示')
add_toggle_page_action('quick_fps','t_fps','scmd_quick','scmd_i_quick_fps')
add_toggle_page_action('quick_impacts','t_impacts','scmd_quick','scmd_i_quick_impacts')
add_toggle_page_action('quick_trajectory','t_trajectory','scmd_quick','scmd_i_quick_trajectory')
add_toggle_page_action('quick_showpos','t_showpos','scmd_quick','scmd_i_quick_showpos')
def quick_dyn(lines):
    render_row(lines,row_quick_fps,13,'scmd_i_quick_fps')
    render_row(lines,row_quick_impacts,14,'scmd_i_quick_impacts')
    render_row(lines,row_quick_trajectory,15,'scmd_i_quick_trajectory')
    render_row(lines,row_quick_showpos,16,'scmd_i_quick_showpos')
addf('menu_quick', menu_body('菜单\\快捷指令', [
    ('常用',[Item(1,'清空控制台','scmd_clear'),Item(2,'断开当前服务器','scmd_disconnect'),Item(3,'打开购买菜单','scmd_buymenu'),Item(4,'打开队伍菜单','scmd_teammenu'),Item(5,'切换左右手','scmd_switchhands')]),
    ('练习',[Item(6,'切换飞行','scmd_noclip'),Item(7,'重新投掷上一个投掷物','scmd_rethrow'),Item(8,'放置人机','scmd_bot_place'),Item(9,'冻结/解除人机','scmd_bot_freeze'),Item(10,'清除全部人机','scmd_bot_clear'),Item(11,'重新开始回合','scmd_round_restart'),Item(12,'结束热身','scmd_warmup_end')]),
    ('显示',[DynamicItem(13,row_quick_fps,'scmd_i_quick_fps'),DynamicItem(14,row_quick_impacts,'scmd_i_quick_impacts'),DynamicItem(15,row_quick_trajectory,'scmd_i_quick_trajectory'),DynamicItem(16,row_quick_showpos,'scmd_i_quick_showpos')]),
], 'scmd_menu','scmd_quick'), 'scmd_quick')

# Command index.
command_categories = [
    ('CFG与控制台','scmd_cmd_cfg'),('按键与输入','scmd_cmd_bind'),('地图与会话','scmd_cmd_map'),('游戏与回合','scmd_cmd_game'),
    ('练习与作弊','scmd_cmd_practice'),('人机','scmd_cmd_bot'),('武器与购买','scmd_cmd_weapon'),('Demo与观战','scmd_cmd_demo'),
    ('显示与HUD','scmd_cmd_display'),('准星与视角','scmd_cmd_cross'),('声音与语音','scmd_cmd_sound'),('聊天与通信','scmd_cmd_chat'),
    ('网络与状态','scmd_cmd_net'),('截图/位置/记录','scmd_cmd_capture'),('Workshop与地图','scmd_cmd_workshop'),('服务端与管理','scmd_cmd_server')
]
addf('menu_commands', menu_body('菜单\\全部命令', [('', [Item(i+1,n,a) for i,(n,a) in enumerate(command_categories)])], 'scmd_menu','scmd_commands', footer_notes=['=这是精选实用命令目录','=原始全集请在 CFG与控制台 中导出']), 'scmd_commands')

catalog = {
'cfg': ['alias - 定义别名','exec - 执行CFG','execifexists - 存在时执行CFG','exec_async - 异步执行 [CHEATS]','clear / clearall - 清屏','echo / echoln - 输出文本','find / findflags - 搜索命令','help - 查询帮助','grep - 过滤输出','cvarlist - 命令与ConVar列表','differences - 非默认ConVar','print_changed_convars - 已修改ConVar','toggle / cyclevar - 切换值','incrementvar / multvar - 数值操作','push_var_values / pop_var_values - 保存恢复值','host_writeconfig - 保存配置','writekeybindings - 保存按键'],
'bind': ['bind - 绑定按键','unbind - 解除按键','unbindall - 全部解除 [DANGER]','binddefaults - 默认绑定 [DANGER]','button_info - 按键信息','key_findbinding - 查找绑定','key_listboundkeys - 列出绑定','lastinv / invnext / invprev - 武器切换','switchhands / switchhandsleft / switchhandsright','buymenu / teammenu','+attack / +attack2 / +jump / +duck','+use / +reload / +voicerecord','+lookatweapon / +spray_menu'],
'map': ['maps - 列出地图','map <name> - 加载地图','changelevel <name> - 切图','map_workshop - Workshop地图','ds_workshop_listmaps - Workshop列表','connect <address> - 连接服务器','disconnect - 断开','timeleft - 剩余时间','pause / unpause - 暂停继续','game_alias - 游戏别名','quit - 退出游戏 [DANGER]'],
'game': ['mp_warmup_start / mp_warmup_end','mp_pause_match / mp_unpause_match','mp_swapteams / mp_scrambleteams','mp_restartgame','mp_freezetime','mp_roundtime / mp_roundtime_defuse','mp_round_restart_delay','mp_buy_anywhere / mp_buytime','mp_startmoney / mp_maxmoney','mp_limitteams / mp_autoteambalance','mp_ignore_round_win_conditions','mp_friendlyfire','mp_respawn_on_death_t / ct','mp_c4timer / mp_maxrounds'],
'practice': ['noclip [CHEATS]','god [CHEATS]','healme / hurtme [CHEATS]','give <item> [LOCAL/CHEATS]','givecurrentammo [CHEATS]','getpos / getpos_exact','getposcopy / getposcopy_exact','sv_rethrow_last_grenade','sv_kill_smokegrenade','sv_infinite_ammo','sv_grenade_trajectory_prac_pipreview','sv_grenade_trajectory_prac_trailtime','sv_showimpacts / sv_showimpacts_time','sv_showimpacts_penetration','ammo_grenade_limit_total','sv_gravity'],
'bot': ['bot_add / bot_add_t / bot_add_ct','bot_kick / bot_kill','bot_place [CHEATS]','bot_stop','bot_mimic / bot_mimic_yaw_offset','bot_all_weapons','bot_knives_only','bot_pistols_only','bot_snipers_only','bot_goto_mark / bot_goto_selected [CHEATS]','bot_path [CHEATS]','bot_difficulty'],
'weapon': ['give <item> [LOCAL/CHEATS]','weapon_switch <name>','givecurrentammo','autobuy / rebuy / buy','buyrandom','buymenu','sellbackall','mp_buy_anywhere / mp_buytime','mp_buy_allow_grenades / guns','mp_weapons_allow_typecount','mp_weapons_allow_zeus','mp_weapons_allow_pistols / rifles / smgs'],
'demo': ['playdemo','demoui','demo_pause / demo_resume','demo_togglepause','demo_step_tick','demo_timescale','demo_goto / demo_gototick','demo_marktick / demo_gotomark','demo_info / demolist / listdemo','nextdemo','timedemo / timedemoquit','firstperson','thirdperson [CHEATS]'],
'display': ['cl_showfps','cl_printfps','cl_ticktiming','cl_showpos','+cl_show_team_equipment','toggleradarscale','hideradar / drawradar','gameui_hide / gameui_activate','net_status / net_channels','firstperson / thirdperson [CHEATS]'],
'cross': ['crosshair','cl_crosshairstyle','cl_crosshairsize','cl_crosshairthickness','cl_crosshairgap','cl_crosshairalpha / usealpha','cl_crosshaircolor + RGB','cl_crosshair_drawoutline','cl_crosshairdot','cl_crosshair_t','cl_crosshair_sniper_width','viewmodel_fov','viewmodel_offset_x / y / z','viewmodel_presetpos'],
'sound': ['volume','snd_mute_losefocus','snd_voipvolume','snd_menumusic_volume','snd_mvp_volume','snd_tensecondwarning_volume','snd_roundstart_volume / roundend_volume','voice_modenable','voice_modenable_toggle','voice_toggle_open_mic','voice_loopback','+voicerecord','play / playvol'],
'chat': ['say','say_team','messagemode','messagemode2','player_ping','callvote','listissues','+radialradio / 2 / 3'],
'net': ['status','net_status','net_channels','net_connections_stats','net_showudp','net_option','timeleft','users','sys_info','cpuinfo','cl_ticktiming'],
'capture': ['getpos / getpos_exact','getposcopy / getposcopy_exact','screenshot','png_screenshot','jpeg_screenshot','_record','tv_record','tv_stoprecord'],
'workshop': ['map_workshop','ds_workshop_changelevel','ds_workshop_listmaps','host_workshop_map','host_workshop_collection','print_mapgroup','print_mapgroup_sv','maps','changelevel'],
'server': ['kick / kickid','banid / banip','listid / listip','writeid / writeip','sv_shutdown [DANGER]','tv_status / tv_clients','tv_broadcast_status','mp_disable_autokick','mp_pause_match / mp_unpause_match'],
}
cat_title = dict(command_categories)
for key, lines_data in catalog.items():
    title = next((n for n,a in command_categories if a == f'scmd_cmd_{key}'), key)
    sections=[('', [f'={x}' for x in lines_data])]
    addf('cmd_'+key, menu_body(f'菜单\\全部命令\\{title}', sections, 'scmd_commands', f'scmd_cmd_{key}'), f'scmd_cmd_{key}')

# Weapons menu and subpages.
addf('menu_weapons', menu_body('菜单\\武器与装备', [('', [
    Item(1,'全部武器 [LOCAL/CHEATS]','scmd_weapons_all'), Item(2,'步枪','scmd_weapons_rifle'), Item(3,'狙击枪','scmd_weapons_sniper'),
    Item(4,'冲锋枪','scmd_weapons_smg'), Item(5,'霰弹枪','scmd_weapons_shotgun'), Item(6,'机枪','scmd_weapons_mg'), Item(7,'手枪','scmd_weapons_pistol'),
    Item(8,'投掷物','scmd_weapons_grenade'), Item(9,'装备','scmd_weapons_gear'), Item(10,'特殊物品 [LOCAL/CHEATS]','scmd_weapons_special'),
    Item(11,'快速整套装备','scmd_weapons_pack'), Item(12,'补充当前武器弹药','scmd_give_ammo')
])], 'scmd_menu','scmd_weapons', footer_notes=['=give 类功能通常需要本地 sv_cheats 1']), 'scmd_weapons')

def weapon_page(name, subset, alias):
    items=[Item(i+1, display, weapon_alias[key]) for i,(display,item,key) in enumerate(subset)]
    addf('menu_'+alias, menu_body(f'武器与装备\\{name}', [('',items)], 'scmd_weapons', alias), alias)

weapon_page('步枪', weapons[0:7], 'scmd_weapons_rifle')
weapon_page('狙击枪', weapons[7:11], 'scmd_weapons_sniper')
weapon_page('冲锋枪', weapons[11:18], 'scmd_weapons_smg')
weapon_page('霰弹枪', weapons[18:22], 'scmd_weapons_shotgun')
weapon_page('机枪', weapons[22:24], 'scmd_weapons_mg')
weapon_page('手枪', weapons[24:34], 'scmd_weapons_pistol')
weapon_page('投掷物', weapons[34:40], 'scmd_weapons_grenade')
weapon_page('装备', weapons[40:44], 'scmd_weapons_gear')
weapon_page('特殊物品', weapons[44:47], 'scmd_weapons_special')
# All weapons long page.
addf('menu_weapons_all', menu_body('武器与装备\\全部武器', [('', [Item(i+1,display,weapon_alias[key]) for i,(display,item,key) in enumerate(weapons)])], 'scmd_weapons','scmd_weapons_all', footer_notes=['=长页模式: 一页查看全部可生成物品']), 'scmd_weapons_all')
addf('menu_weapons_pack', menu_body('武器与装备\\快速整套装备', [('',[
    Item(1,'AK + Deagle + 全甲 + 投掷物','scmd_i_pack_ak'),Item(2,'M4A1-S + USP-S + 全甲 + 投掷物','scmd_i_pack_m4s'),
    Item(3,'M4A4 + USP-S + 全甲 + 投掷物','scmd_i_pack_m4'),Item(4,'AWP + Deagle + 全甲','scmd_i_pack_awp'),Item(5,'投掷物包','scmd_i_pack_nades')
])], 'scmd_weapons','scmd_weapons_pack'), 'scmd_weapons_pack')
# Assign command aliases to pack actions after creation.
for fname, alias in [('pack_ak','scmd_i_pack_ak'),('pack_m4s','scmd_i_pack_m4s'),('pack_m4','scmd_i_pack_m4'),('pack_awp','scmd_i_pack_awp'),('pack_nades','scmd_i_pack_nades')]:
    name_to_func[fname].command_alias = alias

# Custom menu.
addf('custom_empty', [pr('[SCMD] 此自定义指令槽尚未设置'), pr('[SCMD] 使用 alias scmd_customN <command> 临时设置'), pr('[SCMD] 永久设置请编辑 Scmd/Custom.cfg')], 'scmd_custom_empty')
addf('menu_custom', menu_body('菜单\\自定义指令', [('', [Item(i,f'执行自定义指令{i}',f'scmd_custom{i}') for i in range(1,9)] + [Item(9,'设置方法','scmd_custom_help'),Item(10,'重新加载 Custom.cfg','scmd_i_reload_custom')])], 'scmd_menu','scmd_custom_menu'), 'scmd_custom_menu')
name_to_func['a_reload_custom'].command_alias='scmd_i_reload_custom'
addf('custom_help', menu_body('自定义指令\\设置方法', [('',[
    '=临时设置示例:', '=alias scmd_custom1 say_team_ready', '=如果需要多条命令请自行在 Custom.cfg 中定义', '', '=永久文件:', '=Scmd/Custom.cfg', '=SCMD 启动时会 execifexists 该文件'
])], 'scmd_custom_menu','scmd_custom_help'), 'scmd_custom_help')

# Practice menu.
addf('menu_practice', menu_body('菜单\\快速跑图', [
    ('初始化',[Item(1,'标准跑图','scmd_practice_standard'),Item(2,'投掷物练习','scmd_practice_grenade'),Item(3,'枪械练习','scmd_practice_aim'),Item(4,'人机练习','scmd_practice_bot'),Item(5,'纯净跑图','scmd_practice_minimal')]),
    ('操作',[Item(6,'重新开始回合','scmd_round_restart'),Item(7,'结束热身','scmd_warmup_end'),Item(8,'练习工具','scmd_practice_tools')]),
], 'scmd_menu','scmd_practice', footer_notes=['=初始化方案绝不会自动绑定按键']), 'scmd_practice')

row_practice_timescale = add_preset_row_renderer('row_practice_timescale','st_timescale',4,'时间流速',['0.1','0.25','0.5','1','2'])
row_practice_trajectory = add_binary_row_renderer('row_practice_trajectory','st_trajectory',7,'投掷物轨迹')
row_practice_impacts = add_binary_row_renderer('row_practice_impacts','st_impacts',10,'弹着点')
row_practice_ammo = add_ammo_row_renderer('row_practice_ammo',12,'无限弹药')
row_practice_god = add_binary_row_renderer('row_practice_god','st_god',14,'无敌')
add_cycle_page_action('practice_timescale','p_timescale','scmd_practice_tools','scmd_i_practice_timescale')
register_help('scmd_i_practice_timescale','host_timescale {数字}','输入 4 循环预设；也可直接输入任意合法数字 [LOCAL/CHEATS]','host_timescale 0.75')
add_toggle_page_action('practice_trajectory','t_trajectory','scmd_practice_tools','scmd_i_practice_trajectory')
add_toggle_page_action('practice_impacts','t_impacts','scmd_practice_tools','scmd_i_practice_impacts')
add_toggle_page_action('practice_ammo','t_ammo','scmd_practice_tools','scmd_i_practice_ammo')
add_toggle_page_action('practice_god','t_god','scmd_practice_tools','scmd_i_practice_god')
def practice_dyn(lines):
    render_row(lines,row_practice_timescale,4,'scmd_i_practice_timescale')
    render_row(lines,row_practice_trajectory,7,'scmd_i_practice_trajectory')
    render_row(lines,row_practice_impacts,10,'scmd_i_practice_impacts')
    render_row(lines,row_practice_ammo,12,'scmd_i_practice_ammo')
    render_row(lines,row_practice_god,14,'scmd_i_practice_god')
addf('menu_practice_tools', menu_body('菜单\\练习工具', [
    ('移动',[Item(1,'切换飞行','scmd_noclip'),Item(2,'显示当前位置','scmd_showpos_once'),Item(3,'复制精确位置','scmd_poscopy'),DynamicItem(4,row_practice_timescale,'scmd_i_practice_timescale','时间流速')]),
    ('投掷物',[Item(6,'重新投掷','scmd_rethrow'),DynamicItem(7,row_practice_trajectory,'scmd_i_practice_trajectory'),Item(9,'清除烟雾 [CHEATS]','scmd_smoke_clear')]),
    ('射击',[DynamicItem(10,row_practice_impacts,'scmd_i_practice_impacts'),DynamicItem(12,row_practice_ammo,'scmd_i_practice_ammo')]),
    ('玩家',[DynamicItem(14,row_practice_god,'scmd_i_practice_god'),Item(15,'治疗','scmd_heal'),Item(16,'自杀/重生测试','scmd_kill')])
], 'scmd_menu','scmd_practice_tools'), 'scmd_practice_tools')

# Bots.
row_bots_stop = add_binary_row_renderer('row_bots_stop','st_bot_stop',5,'冻结全部人机')
row_bots_mimic = add_binary_row_renderer('row_bots_mimic','st_bot_mimic',7,'人机模仿')
add_toggle_page_action('bots_stop','t_bot_stop','scmd_bots','scmd_i_bots_stop')
add_toggle_page_action('bots_mimic','t_bot_mimic','scmd_bots','scmd_i_bots_mimic')
def bots_dyn(lines):
    render_row(lines,row_bots_stop,5,'scmd_i_bots_stop')
    render_row(lines,row_bots_mimic,7,'scmd_i_bots_mimic')
addf('menu_bots', menu_body('菜单\\人机控制', [
    ('生成',[Item(1,'添加T人机','scmd_bot_add_t'),Item(2,'添加CT人机','scmd_bot_add_ct'),Item(3,'添加任意人机','scmd_bot_add'),Item(4,'放置人机','scmd_bot_place')]),
    ('控制',[DynamicItem(5,row_bots_stop,'scmd_i_bots_stop'),DynamicItem(7,row_bots_mimic,'scmd_i_bots_mimic'),Item(9,'仅手枪','scmd_i_bot_pistols'),Item(10,'仅狙击枪','scmd_i_bot_snipers'),Item(11,'仅刀','scmd_i_bot_knives'),Item(12,'允许全部武器','scmd_i_bot_all')]),
    ('清理',[Item(13,'击杀全部人机','scmd_bot_kill'),Item(14,'踢出全部人机','scmd_bot_clear')]),
], 'scmd_menu','scmd_bots'), 'scmd_bots')

for fname, alias in [('a_bot_pistols','scmd_i_bot_pistols'),('a_bot_snipers','scmd_i_bot_snipers'),('a_bot_knives','scmd_i_bot_knives'),('a_bot_all_weapons','scmd_i_bot_all')]: name_to_func[fname].command_alias=alias

# Demo.
for fname, alias in [('a_demo_pause','scmd_i_demo_pause'),('a_demo_resume','scmd_i_demo_resume'),('a_demo_step','scmd_i_demo_step'),('a_demo_ui','scmd_i_demo_ui'),('a_demo_info','scmd_i_demo_info'),('a_demo_list','scmd_i_demo_list'),('a_demo_list2','scmd_i_demo_list2')]: name_to_func[fname].command_alias=alias
row_demo_speed = add_preset_row_renderer('row_demo_speed','st_demo_speed',6,'Demo速度',['0.25','0.5','1','2','4'])
add_cycle_page_action('demo_speed_cycle','p_demo_speed','scmd_demo','scmd_i_demo_speed')
register_help('scmd_i_demo_speed','demo_timescale {数字}','输入 6 循环 Demo 播放速度；也可以手动输入任意合法数字','demo_timescale 1.5')
addf('menu_demo', menu_body('菜单\\Demo与观战', [
    ('播放',[Item(1,'暂停/继续','scmd_demo_pause'),Item(2,'暂停','scmd_i_demo_pause'),Item(3,'继续','scmd_i_demo_resume'),Item(4,'单步1 Tick','scmd_i_demo_step'),Item(5,'打开Demo UI','scmd_i_demo_ui')]),
    ('速度',[DynamicItem(6,row_demo_speed,'scmd_i_demo_speed','Demo速度')]),
    ('信息',[Item(7,'Demo信息','scmd_i_demo_info'),Item(8,'demolist','scmd_i_demo_list'),Item(9,'listdemo','scmd_i_demo_list2')])
], 'scmd_menu','scmd_demo'), 'scmd_demo')

# Map/session.
map_alias_map={
'a_map_maps':'scmd_i_maps','a_map_timeleft':'scmd_i_timeleft','a_map_pause':'scmd_i_pause','a_map_unpause':'scmd_i_unpause','a_map_swapteams':'scmd_i_swapteams','a_map_scramble':'scmd_i_scramble','a_map_workshop':'scmd_i_workshop'}
for fname, alias in map_alias_map.items(): name_to_func[fname].command_alias=alias
addf('menu_map', menu_body('菜单\\地图与会话', [('',[
    Item(1,'列出地图','scmd_i_maps'),Item(2,'加载地图说明','scmd_map_help'),Item(3,'Workshop地图列表','scmd_i_workshop'),Item(4,'连接服务器说明','scmd_connect_help'),
    Item(5,'断开服务器','scmd_disconnect'),Item(6,'比赛剩余时间','scmd_i_timeleft'),Item(7,'暂停','scmd_i_pause'),Item(8,'继续','scmd_i_unpause'),Item(9,'交换双方','scmd_i_swapteams'),Item(10,'打乱队伍','scmd_i_scramble')
])], 'scmd_menu','scmd_map'), 'scmd_map')
addf('map_help', menu_body('地图与会话\\加载地图', [('', ['=控制台用法:', '=map <mapname>', '=changelevel <mapname>', '', '=先使用 maps 查看可用地图'])], 'scmd_map','scmd_map_help'), 'scmd_map_help')
addf('connect_help', menu_body('地图与会话\\连接服务器', [('', ['=控制台用法:', '=connect <address>', '', '=SCMD 不保存服务器IP，也不会自动连接陌生服务器'])], 'scmd_map','scmd_connect_help'), 'scmd_connect_help')

# Display/HUD.
row_display_fps = add_binary_row_renderer('row_display_fps','st_fps',1,'FPS显示')
row_display_hud = add_binary_row_renderer('row_display_hud','st_hud',2,'HUD显示')
row_display_showpos = add_binary_row_renderer('row_display_showpos','st_showpos',3,'位置显示')
row_display_impacts = add_binary_row_renderer('row_display_impacts','st_impacts',4,'弹着点')
row_display_trajectory = add_binary_row_renderer('row_display_trajectory','st_trajectory',5,'投掷物轨迹')
add_toggle_page_action('display_fps','t_fps','scmd_display','scmd_i_display_fps')
add_toggle_page_action('display_hud','t_hud','scmd_display','scmd_i_display_hud')
add_toggle_page_action('display_showpos','t_showpos','scmd_display','scmd_i_display_showpos')
add_toggle_page_action('display_impacts','t_impacts','scmd_display','scmd_i_display_impacts')
add_toggle_page_action('display_trajectory','t_trajectory','scmd_display','scmd_i_display_trajectory')
def display_dyn(lines):
    render_row(lines,row_display_fps,1,'scmd_i_display_fps')
    render_row(lines,row_display_hud,2,'scmd_i_display_hud')
    render_row(lines,row_display_showpos,3,'scmd_i_display_showpos')
    render_row(lines,row_display_impacts,4,'scmd_i_display_impacts')
    render_row(lines,row_display_trajectory,5,'scmd_i_display_trajectory')
addf('menu_display', menu_body('菜单\\显示与HUD', [('',[
    DynamicItem(1,row_display_fps,'scmd_i_display_fps'),DynamicItem(2,row_display_hud,'scmd_i_display_hud'),DynamicItem(3,row_display_showpos,'scmd_i_display_showpos'),DynamicItem(4,row_display_impacts,'scmd_i_display_impacts'),DynamicItem(5,row_display_trajectory,'scmd_i_display_trajectory'),
    Item(6,'网络状态','scmd_display_net'),Item(7,'第一人称','scmd_i_firstperson'),Item(8,'第三人称 [CHEATS]','scmd_i_thirdperson'),Item(9,'切换雷达缩放','scmd_i_radar')
])], 'scmd_menu','scmd_display'), 'scmd_display')

add_action('a_firstperson',['firstperson'], '[SCMD] 第一人称', alias='scmd_i_firstperson')
add_action('a_thirdperson',['thirdperson'], '[SCMD] 第三人称', alias='scmd_i_thirdperson')
add_action('a_radar',['toggleradarscale'], alias='scmd_i_radar')
addf('display_net', menu_body('显示与HUD\\网络状态', [('',[
    Item(1,'net_status','scmd_i_net_status'),Item(2,'net_channels','scmd_i_net_channels'),Item(3,'status','scmd_i_status'),Item(4,'cl_ticktiming','scmd_i_ticktiming')
])], 'scmd_display','scmd_display_net'), 'scmd_display_net')
for nm,com,al in [('net_status','net_status','scmd_i_net_status'),('net_channels','net_channels','scmd_i_net_channels'),('status','status','scmd_i_status'),('ticktiming','cl_ticktiming','scmd_i_ticktiming')]: add_action('a_'+nm,[com],alias=al)

# Crosshair hierarchy.
row_cross_main = add_binary_row_renderer('row_cross_main','st_crosshair',1,'准星显示')
row_cross_style = add_preset_row_renderer('row_cross_style','st_cross_style',2,'准星样式',['0','1','2','3','4','5'])
row_cross_size = add_preset_row_renderer('row_cross_size','st_cross_size',3,'准星大小',['1','2','3','4','5'])
row_cross_thick = add_preset_row_renderer('row_cross_thick','st_cross_thickness',4,'准星粗细',['0.5','1','1.5','2'])
row_cross_gap = add_preset_row_renderer('row_cross_gap','st_cross_gap',5,'准星间距',['-3','-1','0','1','3'])
row_cross_color = add_preset_row_renderer('row_cross_color','st_cross_color',6,'准星颜色',['1','2','3','4','5'])
row_cross_sniper = add_preset_row_renderer('row_cross_sniper','st_sniper_width',8,'狙击准星宽度',['1','2','3','4'])
add_toggle_page_action('cross_main_toggle','t_crosshair','scmd_crosshair_menu','scmd_i_crosshair_toggle')
for name, func, alias, command_name, desc, example in [
    ('cross_style_cycle','p_cross_style','scmd_i_cross_style','cl_crosshairstyle','输入 2 循环准星样式预设','cl_crosshairstyle 4'),
    ('cross_size_cycle','p_cross_size','scmd_i_cross_size','cl_crosshairsize','输入 3 循环准星大小预设','cl_crosshairsize 2.5'),
    ('cross_thick_cycle','p_cross_thickness','scmd_i_cross_thick','cl_crosshairthickness','输入 4 循环准星粗细预设','cl_crosshairthickness 0.5'),
    ('cross_gap_cycle','p_cross_gap','scmd_i_cross_gap','cl_crosshairgap','输入 5 循环准星间距预设','cl_crosshairgap -2'),
    ('cross_color_cycle','p_cross_color','scmd_i_cross_color','cl_crosshaircolor','输入 6 循环准星颜色预设','cl_crosshaircolor 4'),
    ('cross_sniper_cycle','p_sniper_width','scmd_i_cross_sniper','cl_crosshair_sniper_width','输入 8 循环狙击准星宽度预设','cl_crosshair_sniper_width 1'),
]:
    add_cycle_page_action(name,func,'scmd_crosshair_menu',alias)
    register_help(alias,f'{command_name} {{数字}}',desc,example)
def cross_main_dyn(lines):
    render_row(lines,row_cross_main,1,'scmd_i_crosshair_toggle')
    render_row(lines,row_cross_style,2,'scmd_i_cross_style')
    render_row(lines,row_cross_size,3,'scmd_i_cross_size')
    render_row(lines,row_cross_thick,4,'scmd_i_cross_thick')
    render_row(lines,row_cross_gap,5,'scmd_i_cross_gap')
    render_row(lines,row_cross_color,6,'scmd_i_cross_color')
    render_row(lines,row_cross_sniper,8,'scmd_i_cross_sniper')
addf('menu_crosshair', menu_body('菜单\\准星与视角', [('',[
    DynamicItem(1,row_cross_main,'scmd_i_crosshair_toggle','准星显示'),DynamicItem(2,row_cross_style,'scmd_i_cross_style','准星样式'),DynamicItem(3,row_cross_size,'scmd_i_cross_size','准星大小'),DynamicItem(4,row_cross_thick,'scmd_i_cross_thick','准星粗细'),DynamicItem(5,row_cross_gap,'scmd_i_cross_gap','准星间距'),
    DynamicItem(6,row_cross_color,'scmd_i_cross_color','准星颜色'),Item(7,'额外开关','scmd_crosshair_extras'),DynamicItem(8,row_cross_sniper,'scmd_i_cross_sniper','狙击准星宽度'),Item(9,'Viewmodel','scmd_viewmodel')
])], 'scmd_menu','scmd_crosshair_menu'), 'scmd_crosshair_menu')

row_cross_dot = add_binary_row_renderer('row_cross_dot','st_dot',1,'中心点')
row_cross_outline = add_binary_row_renderer('row_cross_outline','st_outline',2,'描边')
row_cross_t = add_binary_row_renderer('row_cross_t','st_tcross',3,'T形准星')
add_toggle_page_action('cross_dot_toggle','t_dot','scmd_crosshair_extras','scmd_i_cross_dot')
add_toggle_page_action('cross_outline_toggle','t_outline','scmd_crosshair_extras','scmd_i_cross_outline')
add_toggle_page_action('cross_t_toggle','t_tcross','scmd_crosshair_extras','scmd_i_cross_t')
def cross_extras_dyn(lines):
    render_row(lines,row_cross_dot,1,'scmd_i_cross_dot')
    render_row(lines,row_cross_outline,2,'scmd_i_cross_outline')
    render_row(lines,row_cross_t,3,'scmd_i_cross_t')
addf('menu_cross_extras', menu_body('准星与视角\\额外开关', [('',[DynamicItem(1,row_cross_dot,'scmd_i_cross_dot'),DynamicItem(2,row_cross_outline,'scmd_i_cross_outline'),DynamicItem(3,row_cross_t,'scmd_i_cross_t')])], 'scmd_crosshair_menu','scmd_crosshair_extras'), 'scmd_crosshair_extras')

row_view_fov = add_preset_row_renderer('row_view_fov','st_view_fov',1,'Viewmodel FOV',['54','60','68'])
row_view_preset = add_preset_row_renderer('row_view_preset','st_view_preset',2,'Viewmodel预设',['1','2','3'])
add_cycle_page_action('view_fov_cycle','p_view_fov','scmd_viewmodel','scmd_i_view_fov')
add_cycle_page_action('view_preset_cycle','p_view_preset','scmd_viewmodel','scmd_i_view_preset')
register_help('scmd_i_view_fov','viewmodel_fov {数字}','输入 1 循环 FOV 预设；也可手动输入允许的数字','viewmodel_fov 68')
register_help('scmd_i_view_preset','viewmodel_presetpos {数字}','输入 2 循环 Viewmodel 位置预设','viewmodel_presetpos 1')
def viewmodel_dyn(lines):
    render_row(lines,row_view_fov,1,'scmd_i_view_fov')
    render_row(lines,row_view_preset,2,'scmd_i_view_preset')
addf('menu_viewmodel', menu_body('准星与视角\\Viewmodel', [('',[
    DynamicItem(1,row_view_fov,'scmd_i_view_fov','Viewmodel FOV'),DynamicItem(2,row_view_preset,'scmd_i_view_preset','Viewmodel预设')
])], 'scmd_crosshair_menu','scmd_viewmodel'), 'scmd_viewmodel')

# Sound menu with inline preset state rows.
row_sound_volume = add_preset_row_renderer('row_sound_volume','st_volume',1,'主音量',['0','0.25','0.5','0.75','1'])
row_sound_menu_music = add_preset_row_renderer('row_sound_menu_music','st_menu_music',2,'菜单音乐',['0','0.25','0.5','1'])
row_sound_mvp = add_preset_row_renderer('row_sound_mvp','st_mvp_music',3,'MVP音乐',['0','0.25','0.5','1'])
row_sound_tensec = add_preset_row_renderer('row_sound_tensec','st_tensec',4,'十秒警告',['0','0.25','0.5','1'])
row_sound_voice = add_binary_row_renderer('row_sound_voice','st_voice',5,'语音接收')
row_sound_loopback = add_binary_row_renderer('row_sound_loopback','st_loopback',6,'麦克风回放')
row_sound_mute = add_binary_row_renderer('row_sound_mute','st_mute_losefocus',7,'失焦时静音')
for name,func,alias,cmdname,desc,ex in [
    ('sound_volume_cycle','p_volume','scmd_i_sound_volume','volume','输入 1 循环主音量预设；可手动输入任意 0..1 数值','volume 0.8'),
    ('sound_menu_music_cycle','p_menu_music','scmd_i_sound_menu_music','snd_menumusic_volume','输入 2 循环菜单音乐音量预设','snd_menumusic_volume 0.3'),
    ('sound_mvp_cycle','p_mvp_music','scmd_i_sound_mvp','snd_mvp_volume','输入 3 循环 MVP 音量预设','snd_mvp_volume 0.5'),
    ('sound_tensec_cycle','p_tensec','scmd_i_sound_tensec','snd_tensecondwarning_volume','输入 4 循环十秒警告音量预设','snd_tensecondwarning_volume 0.5'),
]:
    add_cycle_page_action(name,func,'scmd_sound',alias)
    register_help(alias,f'{cmdname} {{数字}}',desc,ex)
add_toggle_page_action('sound_voice_toggle','t_voice','scmd_sound','scmd_i_sound_voice')
add_toggle_page_action('sound_loopback_toggle','t_loopback','scmd_sound','scmd_i_sound_loopback')
add_toggle_page_action('sound_mute_toggle','t_mute_losefocus','scmd_sound','scmd_i_sound_mute')
def sound_dyn(lines):
    render_row(lines,row_sound_volume,1,'scmd_i_sound_volume')
    render_row(lines,row_sound_menu_music,2,'scmd_i_sound_menu_music')
    render_row(lines,row_sound_mvp,3,'scmd_i_sound_mvp')
    render_row(lines,row_sound_tensec,4,'scmd_i_sound_tensec')
    render_row(lines,row_sound_voice,5,'scmd_i_sound_voice')
    render_row(lines,row_sound_loopback,6,'scmd_i_sound_loopback')
    render_row(lines,row_sound_mute,7,'scmd_i_sound_mute')
addf('menu_sound', menu_body('菜单\\声音与语音', [('',[
    DynamicItem(1,row_sound_volume,'scmd_i_sound_volume','主音量'),DynamicItem(2,row_sound_menu_music,'scmd_i_sound_menu_music','菜单音乐'),DynamicItem(3,row_sound_mvp,'scmd_i_sound_mvp','MVP音乐'),DynamicItem(4,row_sound_tensec,'scmd_i_sound_tensec','十秒警告音量'),
    DynamicItem(5,row_sound_voice,'scmd_i_sound_voice','语音接收'),DynamicItem(6,row_sound_loopback,'scmd_i_sound_loopback','麦克风回放'),DynamicItem(7,row_sound_mute,'scmd_i_sound_mute','失焦静音')
])], 'scmd_menu','scmd_sound'), 'scmd_sound')

# CFG/console pages/actions.
for fname, alias in [('a_key_list','scmd_i_key_list'),('a_write_keys','scmd_i_write_keys'),('a_host_writeconfig','scmd_i_write_config'),('a_differences','scmd_i_differences'),('a_changed','scmd_i_changed'),('a_export_cvarlist','scmd_i_export'),('a_reload_custom','scmd_i_reload_custom2')]:
    name_to_func[fname].command_alias = alias
addf('menu_cfg', menu_body('菜单\\CFG与控制台', [
    ('SCMD',[Item(1,'重新加载SCMD','scmd_reload'),Item(2,'重新加载Custom.cfg','scmd_i_reload_custom2'),Item(3,'打开主菜单','scmd_menu')]),
    ('CFG',[Item(4,'执行CFG说明','scmd_exec_help'),Item(5,'保存当前用户配置','scmd_i_write_config'),Item(6,'保存当前按键绑定','scmd_i_write_keys')]),
    ('控制台',[Item(7,'清空控制台','scmd_clear'),Item(8,'查找命令说明','scmd_find_help'),Item(9,'命令帮助说明','scmd_help_help'),Item(10,'显示非默认ConVar','scmd_i_differences'),Item(11,'显示已修改ConVar','scmd_i_changed'),Item(12,'查看当前按键绑定','scmd_i_key_list'),Item(13,'导出完整命令表','scmd_i_export')])
], 'scmd_menu','scmd_cfg'), 'scmd_cfg')
addf('exec_help', menu_body('CFG与控制台\\执行CFG', [('', ['=控制台用法:', '=exec <name>', '=execifexists <name>', '', '=例如: exec autoexec'])], 'scmd_cfg','scmd_exec_help'), 'scmd_exec_help')
addf('find_help', menu_body('CFG与控制台\\查找命令', [('', ['=控制台用法:', '=find <keyword>', '', '=例如: find crosshair'])], 'scmd_cfg','scmd_find_help'), 'scmd_find_help')
addf('help_help', menu_body('CFG与控制台\\命令帮助', [('', ['=控制台用法:', '=help <command>', '', '=例如: help bot_place'])], 'scmd_cfg','scmd_help_help'), 'scmd_help_help')

# Preferences.
addf('pref_cycle_clear', [
    'if(pref_clear_mode == 0)', '{', '    pref_clear_mode = 1;', '}',
    'else if(pref_clear_mode == 1)', '{', '    pref_clear_mode = 2;', '}',
    'else', '{', '    pref_clear_mode = 0;', '}',
    cmd('scmd_preferences')
], 'scmd_pref_clear')
register_help('scmd_pref_clear','SCMD 内部首选项','循环清屏模式：关闭 / 软清屏 / 原生清屏。原生清屏使用 32ms async settle，适合本地环境','')
addf('pref_toggle_tips', [
    'if(pref_tips)', '{', '    pref_tips = false;', '}', 'else', '{', '    pref_tips = true;', '}', cmd('scmd_preferences')
], 'scmd_pref_tips')
addf('pref_reset', ['pref_clear_mode = 1;','pref_tips = true;',cmd('scmd_preferences')], 'scmd_pref_reset')
row_pref_clear = add_preset_row_renderer('row_pref_clear','pref_clear_mode',1,'清屏模式',['关闭','软清屏','原生'])
# state 0 is a valid first preset here, while generic renderer treats 0 as unknown. Use a custom renderer.
name_to_func.pop('row_pref_clear', None)
funcs[:] = [f for f in funcs if f.name != 'row_pref_clear']
addf('row_pref_clear', [
    'if(pref_clear_mode == 0)','{','    '+pr('=1.清屏模式 [(关闭),软清屏,原生]'),'}',
    'else if(pref_clear_mode == 1)','{','    '+pr('=1.清屏模式 [关闭,(软清屏),原生]'),'}',
    'else','{','    '+pr('=1.清屏模式 [关闭,软清屏,(原生)]'),'}',
])
row_pref_tips = add_bool_row_renderer('row_pref_tips','pref_tips',2,'操作提示')
def pref_dyn(lines):
    render_row(lines,'row_pref_clear',1,'scmd_pref_clear')
    render_row(lines,row_pref_tips,2,'scmd_pref_tips')
addf('menu_preferences', menu_body('菜单\\首选项', [('',[DynamicItem(1,'row_pref_clear','scmd_pref_clear','清屏模式'),DynamicItem(2,row_pref_tips,'scmd_pref_tips','操作提示'),Item(3,'恢复默认首选项','scmd_pref_reset')])], 'scmd_menu','scmd_preferences', footer_notes=['=默认使用软清屏，避免 CS2 原生 clear 时序导致菜单缺字']), 'scmd_preferences')

# About.
addf('menu_about', menu_body('关于SCMD', [('',[
    '=SCMD - Shortcut Command','=','=Started in 2022','=Rebuilt for CS2 in 2026','=','=SCMD 2.0 Beta 3','=Compiler: scmdc 0.13.0','=Simulator: scmdsim','=','=scmd.cc'
])], 'scmd_menu','scmd_about'), 'scmd_about')

# Binding system.
preset_bind_targets = [
    (1,'打开SCMD菜单','scmd_menu'),
    (2,'打开快捷指令','scmd_quick'),
    (3,'打开快速跑图','scmd_practice'),
    (4,'打开练习工具','scmd_practice_tools'),
    (5,'打开人机控制','scmd_bots'),
    (6,'打开武器菜单','scmd_weapons'),
    (7,'切换飞行','scmd_noclip'),
    (8,'重新投掷','scmd_rethrow'),
    (9,'放置人机','scmd_bot_place'),
    (10,'冻结/解除人机','scmd_bot_freeze'),
    (11,'人机模仿','scmd_bot_mimic'),
    (12,'清除人机','scmd_bot_clear'),
    (13,'切换FPS显示','scmd_fps'),
    (14,'切换弹着点','scmd_impacts'),
    (15,'切换投掷轨迹','scmd_trajectory'),
    (16,'切换位置显示','scmd_showpos'),
    (17,'循环无限弹药','scmd_ammo'),
    (18,'切换无敌','scmd_god'),
    (19,'清除烟雾','scmd_smoke_clear'),
    (20,'重新开始回合','scmd_round_restart'),
    (21,'结束热身','scmd_warmup_end'),
    (22,'Demo暂停/继续','scmd_demo_pause'),
    (23,'切换准星显示','scmd_crosshair'),
    (24,'切换语音接收','scmd_voice_toggle'),
]
PRESET_BIND_COUNT = len(preset_bind_targets)
custom_bind_targets = [
    (PRESET_BIND_COUNT + i, f'自定义指令{i}', f'scmd_custom{i}')
    for i in range(1,9)
]
bind_targets = preset_bind_targets + custom_bind_targets
# target select actions
for tid, text, target in bind_targets:
    addf(f'bind_target_{tid}', [f'bind_target = {tid};', cmd('scmd_bind_key')], f'scmd_i_bind_target_{tid}')

addf('menu_bind', menu_body('菜单\\按键与快捷键', [('',[
    Item(1,'绑定预设命令','scmd_bind_preset'),Item(2,'绑定自定义指令','scmd_bind_custom'),Item(3,'查看当前绑定','scmd_i_key_list'),Item(4,'保存当前按键绑定','scmd_i_write_keys'),Item(5,'手动绑定说明','scmd_bind_manual')
])], 'scmd_menu','scmd_bind', footer_notes=['=SCMD 永远不会在安装或跑图时自动绑定按键']), 'scmd_bind')
addf('menu_bind_preset', menu_body('按键与快捷键\\绑定预设命令', [('',[
    Item(tid,text,f'scmd_i_bind_target_{tid}') for tid,text,target in preset_bind_targets
])], 'scmd_bind','scmd_bind_preset'), 'scmd_bind_preset')
addf('menu_bind_custom', menu_body('按键与快捷键\\绑定自定义指令', [('',[
    Item(i, f'自定义指令{i}', f'scmd_i_bind_target_{PRESET_BIND_COUNT+i}') for i in range(1,9)
])], 'scmd_bind','scmd_bind_custom'), 'scmd_bind_custom')
addf('menu_bind_manual', menu_body('按键与快捷键\\手动绑定', [('',[
    '=格式: bind <key> <SCMD命令>', '=例如:', '=bind f6 scmd_noclip', '=bind mouse5 scmd_rethrow', '=bind f7 scmd_bot_place', '', '=绑定系统只使用公开 scmd_* ABI'
])], 'scmd_bind','scmd_bind_manual'), 'scmd_bind_manual')

keys=[('F1','f1'),('F2','f2'),('F3','f3'),('F4','f4'),('F5','f5'),('F6','f6'),('F7','f7'),('F8','f8'),('F9','f9'),('F10','f10'),('F11','f11'),('F12','f12'),('Insert','ins'),('Delete','del'),('Home','home'),('End','end'),('PageUp','pgup'),('PageDown','pgdn'),('Mouse3','mouse3'),('Mouse4','mouse4'),('Mouse5','mouse5')]
# one key action per key, with target dispatch.
for idx_key,(display,keycmd) in enumerate(keys,1):
    lines=[]
    for j,(tid,text,target) in enumerate(bind_targets):
        kw='if' if j==0 else 'else if'
        lines += [f'{kw}(bind_target == {tid})','{','    '+cmd(f'bind {keycmd} {target}'),'}']
    lines += [cmd('scmd_bind'), 'if(pref_tips)', '{', '    '+pr(f'[SCMD] 已绑定 {display}'), '}']
    addf(f'bind_key_{idx_key}', lines, f'scmd_i_bind_key_{idx_key}')

def bindkey_dyn(lines):
    # Selected target label.
    for j,(tid,text,target) in enumerate(bind_targets):
        kw='if' if j==0 else 'else if'
        lines += [f'{kw}(bind_target == {tid})','{','    '+pr(f'=目标: {text}'),'}']
    lines += ['else','{','    '+pr('=目标: 未选择'),'}']
addf('menu_bind_key', menu_body('按键与快捷键\\选择按键', [('',[
    Item(i+1,display,f'scmd_i_bind_key_{i+1}') for i,(display,keycmd) in enumerate(keys)
])], 'scmd_bind','scmd_bind_key', dynamic_builder=bindkey_dyn, footer_notes=['=选择按键会覆盖该键原有绑定','=SCMD 不会自动恢复被覆盖的旧绑定']), 'scmd_bind_key')

# Main registration is added last after aliases are known.
def main_body(idx):
    lines=[comment('Register every SCMD public/internal console entry point to its generated function alias.')]
    for i,f in enumerate(funcs):
        if f.command_alias:
            lines.append(cmd(f'alias {f.command_alias} __scmd_fn{i}'))
    lines += [
        # Custom slots have a safe default and may be overridden by user file.
        cmd('alias scmd_custom1 scmd_custom_empty'),cmd('alias scmd_custom2 scmd_custom_empty'),cmd('alias scmd_custom3 scmd_custom_empty'),cmd('alias scmd_custom4 scmd_custom_empty'),
        cmd('alias scmd_custom5 scmd_custom_empty'),cmd('alias scmd_custom6 scmd_custom_empty'),cmd('alias scmd_custom7 scmd_custom_empty'),cmd('alias scmd_custom8 scmd_custom_empty'),
        cmd('execifexists Scmd/Custom'),
        cmd('scmd_menu'),
    ]
    return lines
addf('main', main_body)

# ---------------------------------------------------------------------------
# Emit generated SCMD source.
# ---------------------------------------------------------------------------
index={f.name:i for i,f in enumerate(funcs)}
source=[]
source.append('// GENERATED SCMD 2.0 BETA 3 SOURCE')
source.append('// Generated by tools/generate_scmd2.py; compile with scmdc, do not hand-edit generated CFG.')
source.append('// Function -> __scmd_fn index map is intentionally deterministic and validated after build.')
source.append('')
source.append(globals_src)
source.append('')
for i,f in enumerate(funcs):
    source.append(f'// fn[{i}] {f.name}' + (f' -> {f.command_alias}' if f.command_alias else ''))
    source.append(f'function {f.name}()')
    source.append('{')
    body = f.body(index) if callable(f.body) else f.body
    for line in body:
        if line in ('{','}') or line.startswith('else') or line.startswith('if(') or line.startswith('else if('):
            source.append('    '+line)
        elif line.startswith('    '):
            source.append('    '+line)
        else:
            source.append('    '+line)
    source.append('}')
    source.append('')

(SRC/'main.scmd').write_text('\n'.join(source),encoding='utf-8',newline='\n')

# Project.
proj='''project "scmd"\n{\n    entry = "src/main.scmd";\n    output = "build";\n    package = "Scmd";\n    bootstrap = true;\n\n    target cs2\n    {\n        console\n        {\n            mode = async;\n            settle = 32ms;\n            tick = 16ms;\n        }\n\n        paging\n        {\n            max_bytes = 4096;\n            max_commands = 40;\n        }\n    }\n}\n'''
(OUT/'scmd.scmdproj').write_text(proj,encoding='utf-8',newline='\n')

custom='''// SCMD 2.0 user custom command slots.\n// Copy this file to Custom.cfg and edit it.\n// Example:\n// alias scmd_custom1 "say hello"\n\n// alias scmd_custom1 ""\n// alias scmd_custom2 ""\n// alias scmd_custom3 ""\n// alias scmd_custom4 ""\n// alias scmd_custom5 ""\n// alias scmd_custom6 ""\n// alias scmd_custom7 ""\n// alias scmd_custom8 ""\n'''
(OUT/'Custom.cfg.example').write_text(custom,encoding='utf-8',newline='\n')

# Smoke script exercises navigation, dynamic rows, long weapon page, custom fallback and binding pages.
smoke='''00\n+1\n1\n+13\n13\n0\n5\n8\n4\n+4\n4\n4\n0\n8\n6\n+6\n6\n0\n11\n2\n+2\n2\n0\n12\n1\n+1\n1\n0\n15\n1\n0\n16\n0\n'''
(OUT/'smoke_console.txt').write_text(smoke,encoding='utf-8',newline='\n')

# Verification helper that confirms aliases point at expected generated fn ids.
verify='''#!/usr/bin/env python3\nfrom pathlib import Path\nimport re, sys\nroot=Path(__file__).resolve().parents[1]\nsrc=(root/'src/main.scmd').read_text(encoding='utf-8')\n# Scan the whole compiled package (pages/, lazy/, bootstrap.cfg, entry.cfg, ...):\n# since 0.11+ the boot-path registration lives in bootstrap.cfg, not pages/.\npkg=root/'build/Scmd'\npages='\\n'.join(p.read_text(encoding='utf-8') for p in sorted(pkg.rglob('*.cfg')))\nfuncs=[]\nfor line in src.splitlines():\n    m=re.match(r'// fn\\[(\\d+)\\] ([A-Za-z0-9_]+)(?: -> ([A-Za-z0-9_]+))?', line)\n    if m: funcs.append((int(m.group(1)),m.group(2),m.group(3)))\nerrors=[]\nfor idx,name,alias in funcs:\n    if f'alias __scmd_fn{idx} ' not in pages:\n        errors.append(f'missing function alias __scmd_fn{idx} ({name})')\n    if alias and f'alias {alias} __scmd_fn{idx}' not in pages:\n        # registration exists inside a generated function body, so search textual body fragment too\n        if f'alias {alias} __scmd_fn{idx};' not in pages and f'alias {alias} __scmd_fn{idx}' not in pages:\n            errors.append(f'missing registration literal for {alias} -> __scmd_fn{idx}')\nif errors:\n    print('VERIFY_FAIL')\n    print('\\n'.join(errors[:50]))\n    sys.exit(1)\nprint(f'VERIFY_PASS functions={len(funcs)} public_entries={sum(1 for _,_,a in funcs if a)}')\n'''
(TOOLS/'verify_generated.py').write_text(verify,encoding='utf-8',newline='\n')

# README / CHANGELOG / docs are maintained separately from generated source.


# Generator already lives in tools/; keep it as the reproducible source of src/main.scmd.

print(f'generated {SRC/"main.scmd"}')
print(f'functions={len(funcs)} source_bytes={(SRC/"main.scmd").stat().st_size}')
