关联 #416。看到此前讨论停在共享 Wine／Proton 环境后仍然截到黑图，我们在 Linux Steam 环境中完成了一条可运行的兼容路径，想补充实现与实测结果，并讨论上游愿意接纳的接入形式。

## 当前结果与环境

- AALC：官方 V1.6.1 Windows x86-64 包。
- 系统：Fedora 44、KDE Plasma Wayland；游戏窗口为 XWayland。
- Steam：Flatpak `com.valvesoftware.Steam`。
- Proton：GE-Proton11-12-x86_64；游戏为 Direct3D 11、中文界面。
- 已验证完整中文 GUI、实时 RGB／灰度截图、中文 OCR、最小化后的窗口恢复、Linux 通知和 AALC 原有截图小工具。小工具实际保存1600×900游戏客户区画面。
- 已从 V1.6.0 迁移到 V1.6.1，关闭及重新启动后比较配置与主题权重，全部原有值保留。
- V1.6.1 本轮没有执行完整日常或镜牢通关。其他发行版、显卡及原生Wayland窗口尚待测试。

## 实现方式

```text
Linux启动器
  ├─ 从运行中游戏定位Flatpak实例、Proton工具与前缀
  ├─ XComposite读取游戏窗口，启动本机截图／通知桥
  └─ flatpak enter → 游戏正在使用的Proton环境 → Windows Python
       └─ 官方AALC冻结模块 + 兼容钩子
            ├─ 保留上游GUI、OCR、任务、配置、输入
            ├─ 截图入口替换为宿主提供的游戏客户区画面
            └─ 通知转给Linux notify-send
```

1. **共享运行环境**：复用运行中游戏的Proton和Wine前缀，避免独立Wine环境找不到游戏窗口。无需修改游戏或汉化。
2. **修复截图黑图**：在Linux宿主以XComposite读取XWayland游戏窗口，通过仅监听`127.0.0.1`的HTTP桥交给Windows PIL，核对并裁剪到客户区。保留AALC原有的高层截图调度、锁和模拟器分支；取图失败时返回错误，不用缓存帧或黑图冒充成功。
3. **Qt界面**：在Windows Python进程内部设置`QT_QPA_PLATFORMTHEME=windows`，解决本机主题／中文界面显示问题。只在宿主设置环境变量未能达到同样效果。
4. **窗口恢复**：后台输入恢复最小化游戏时，不把窗口设成透明或鼠标穿透。
5. **通知与生命周期**：通知交给Linux `notify-send`；启动器随AALC清理截图桥，并支持重复打开恢复已有窗口。

当前做法从用户本机官方程序提取PyInstaller启动成员，利用Windows Python 3.13复用官方依赖。它依赖打包内部结构和具体AALC版本，适合作为已验证的兼容方案；长期希望通过明确的后端入口减少这种依赖。

## 与平台适配分开的业务补丁

本机还保留了周常侧栏模板失败时的限定区域OCR兜底，以及商店第二体系0／1配置的运行时布尔转换和无效合成提示保护。它们会单独列出供审查，不作为Linux支持的必要条件。V1.6.0的楼层／观测饰品旧补丁已在升级V1.6.1时删除，改用新版官方实现。

## 希望讨论的上游接入方式

是否愿意先接纳以下任一部分？

- Steam／Proton运行文档及独立启动入口。
- 明确可替换的截图、通知后端；允许在Wine中选择窗口恢复策略。
- 按平台适配和业务修复分别提交小范围PR。

兼容层源码、安装准备工具和升级／回退说明见独立仓库：[AALC-linux-compat](https://github.com/Xiguang-teammate-Luna/AALC-linux-compat)。仓库仅包含适配源码和文档，不分发官方程序、冻结模块、用户配置或游戏素材。

目前定位为“Linux Steam／Proton兼容层”。愿意依据维护者意见调整接入形式，并与 #416 已有探索衔接。
