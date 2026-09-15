# SCMD 2.0 武器与装备完整菜单

## 全部武器长页

这个页面故意允许很长，满足喜欢“一页看完所有武器”的用户。
分类页面仍然保留。

```text
================================
=|SCMD 2.0:\武器与装备\全部武器
================================
=步枪:
=1.AK-47
=2.M4A4
=3.M4A1-S
=4.Galil AR
=5.FAMAS
=6.AUG
=7.SG 553

=狙击枪:
=8.AWP
=9.SSG 08
=10.G3SG1
=11.SCAR-20

=冲锋枪:
=12.MAC-10
=13.MP9
=14.MP7
=15.MP5-SD
=16.UMP-45
=17.P90
=18.PP-Bizon

=霰弹枪:
=19.Nova
=20.XM1014
=21.MAG-7
=22.Sawed-Off

=机枪:
=23.M249
=24.Negev

=手枪:
=25.Glock-18
=26.USP-S
=27.P2000
=28.P250
=29.Dual Berettas
=30.Five-SeveN
=31.Tec-9
=32.CZ75-Auto
=33.Desert Eagle
=34.R8 Revolver

=投掷物:
=35.HE Grenade
=36.Flashbang
=37.Smoke Grenade
=38.Molotov
=39.Incendiary Grenade
=40.Decoy

=装备:
=41.Zeus x27
=42.Kevlar
=43.Kevlar + Helmet
=44.Defuse Kit

=特殊 [LOCAL/CHEATS]:
=45.Knife
=46.C4
=47.Healthshot
================================
=0.返回
=00.刷新
================================
```

## `give` / item 名称建议

| 显示名 | item name |
|---|---|
| AK-47 | `weapon_ak47` |
| M4A4 | `weapon_m4a1` |
| M4A1-S | `weapon_m4a1_silencer` |
| Galil AR | `weapon_galilar` |
| FAMAS | `weapon_famas` |
| AUG | `weapon_aug` |
| SG 553 | `weapon_sg556` |
| AWP | `weapon_awp` |
| SSG 08 | `weapon_ssg08` |
| G3SG1 | `weapon_g3sg1` |
| SCAR-20 | `weapon_scar20` |
| MAC-10 | `weapon_mac10` |
| MP9 | `weapon_mp9` |
| MP7 | `weapon_mp7` |
| MP5-SD | `weapon_mp5sd` |
| UMP-45 | `weapon_ump45` |
| P90 | `weapon_p90` |
| PP-Bizon | `weapon_bizon` |
| Nova | `weapon_nova` |
| XM1014 | `weapon_xm1014` |
| MAG-7 | `weapon_mag7` |
| Sawed-Off | `weapon_sawedoff` |
| M249 | `weapon_m249` |
| Negev | `weapon_negev` |
| Glock-18 | `weapon_glock` |
| USP-S | `weapon_usp_silencer` |
| P2000 | `weapon_hkp2000` |
| P250 | `weapon_p250` |
| Dual Berettas | `weapon_elite` |
| Five-SeveN | `weapon_fiveseven` |
| Tec-9 | `weapon_tec9` |
| CZ75-Auto | `weapon_cz75a` |
| Desert Eagle | `weapon_deagle` |
| R8 Revolver | `weapon_revolver` |
| HE | `weapon_hegrenade` |
| Flashbang | `weapon_flashbang` |
| Smoke | `weapon_smokegrenade` |
| Molotov | `weapon_molotov` |
| Incendiary | `weapon_incgrenade` |
| Decoy | `weapon_decoy` |
| Zeus | `weapon_taser` |
| Kevlar | `item_kevlar` |
| Kevlar + Helmet | `item_assaultsuit` |
| Defuse Kit | `item_defuser` |
| Knife | `weapon_knife` |
| C4 | `weapon_c4` |
| Healthshot | `weapon_healthshot` |

实际 `give` 需要当前环境允许；SCMD 页面应标注 `[LOCAL/CHEATS]`，不能假装在线匹配中也能用。

## 快速整套装备

建议预设：
- 全甲 + AK + Deagle + 全套常用投掷物
- 全甲 + M4A1-S + USP-S + 全套常用投掷物
- 全甲 + M4A4 + USP-S + 全套常用投掷物
- AWP + Deagle + 全甲
- 纯投掷物包
- 清爽练习包（主武器 + 全甲 + 烟闪火雷）

这些只作为用户主动选择的动作，不在跑图初始化时强制给枪。
