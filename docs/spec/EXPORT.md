# 导出 CS2 命令 / 按键 / 配置

## 你记得的“导出全部命令”大概率就是这个

```text
cvarlist log scmd_cvarlist
```

`cvarlist` 本身用于列出 ConVar / ConCommand；CS2 目前的实用做法中，
`log <filename>` 参数可让列表直接写出到文件，而不是依赖 `condump`。

如果只执行：

```text
cvarlist
```

则只是输出到 Console。

SCMD 2.0 的“导出完整命令表”页面应该显示这条命令和输出文件查找提示，
而不是在 CFG 内塞几千条命令快照。

## 查看当前按键绑定

```text
key_listboundkeys
```

查找某个命令绑定在哪个键：

```text
key_findbinding <command>
```

保存当前按键绑定：

```text
writekeybindings
```

## 保存用户配置

```text
host_writeconfig
```

## 查看非默认 ConVar

```text
differences
```

或：

```text
print_changed_convars
```

## SCMD 的策略

- “全部命令”菜单：内置一份精选、分类、可读的实用目录。
- “原始全集”：让用户用 `cvarlist log ...` 导出当前游戏自己注册的完整表。
- 这样 Valve 更新以后，用户永远能拿到自己版本的真实全集，而 SCMD 菜单不需要塞 3000+ 个垃圾开发命令。
