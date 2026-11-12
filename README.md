# AALC Linux / Proton compatibility layer

在 Linux 上通过 Steam Proton 运行 Limbus Company 时，使用上游 AALC 的中文界面、OCR 和自动化逻辑，并由 Linux 侧提供真实游戏截图及桌面通知。

当前支持 **AALC V1.6.1 的 Windows x86-64 官方发行包**。这是实验性兼容层，AALC 本体仍运行在 Proton 内。上游项目：[AhabAssistantLimbusCompany](https://github.com/KIYI671/AhabAssistantLimbusCompany)。

## 已验证环境

- Fedora Linux 44、KDE Plasma Wayland 会话，游戏窗口通过 XWayland 显示。
- Flatpak Steam `com.valvesoftware.Steam`。
- GE-Proton11-12-x86_64，游戏使用 Direct3D 11；中文游戏界面。
- AALC V1.6.1；同一路线此前在 V1.6.0 上运行。

V1.6.1 已验证：完整中文界面、实时 RGB／灰度截图、中文 OCR、最小化恢复、后台输入模块的窗口激活、Linux 桌面通知、原生截图小工具，以及保留配置的升级和重启。截图小工具保存了 1600×900 的游戏客户区画面。本轮未执行 V1.6.1 的完整日常或镜牢通关。

原生 Wayland 游戏窗口、原生包 Steam、其他发行版／显卡、模拟器和计划任务不在当前验证范围。截图依赖 X11／XComposite；Wayland 桌面会话可用，不等于支持原生 Wayland 窗口捕获。

## 安装

先确保游戏能从 Steam 正常启动。关闭 AALC 后操作；可以保留游戏运行。

1. 从[上游 V1.6.1 发布页](https://github.com/KIYI671/AhabAssistantLimbusCompany/releases/tag/V1.6.1)下载并解压官方包。Flatpak Steam 用户建议放在其可访问的数据目录：

   ```sh
   mkdir -p "$HOME/.var/app/com.valvesoftware.Steam/data/AALC"
   7z x AALC_V1.6.1.7z -o./unpacked
   cp -a ./unpacked/AALC/. "$HOME/.var/app/com.valvesoftware.Steam/data/AALC/"
   ```

   这里以全新目录为例；已有安装升级请遵循下文，勿直接覆盖。

2. 从 [Python 官方 Windows 下载页](https://www.python.org/downloads/windows/)下载 **Python 3.13 的 Windows embeddable package (64-bit)** ZIP。主版本及次版本必须为 3.13，架构必须为 x86-64；无需运行 Windows 安装程序。

3. 安装宿主依赖：`/usr/bin/python3` 及其 Pillow、libX11、libXcomposite、`notify-send`、Flatpak。Fedora 对应软件包为 `python3-pillow libX11 libXcomposite libnotify flatpak`；准备工具另需 Python venv、pip。然后在本仓库内执行：

   ```sh
   python3 -m venv .venv
   .venv/bin/pip install -r requirements-setup.txt
   .venv/bin/python prepare.py \
     --aalc-dir "$HOME/.var/app/com.valvesoftware.Steam/data/AALC" \
     --python-zip /path/to/python-3.13.x-embed-amd64.zip
   ```

4. 启动：

   ```sh
   /usr/bin/python3 "$HOME/.var/app/com.valvesoftware.Steam/data/AALC/compatibility/launch_aalc.py"
   ```

   启动器自动寻找运行中游戏的 Steam 容器、Proton 工具及前缀；游戏未运行时先请求 Flatpak Steam 启动游戏。AALC 及启动文件必须在该容器可访问的目录中。需要菜单入口时，将此命令作为桌面快捷方式的启动命令；如需关闭终端后继续运行，可使用用户会话管理器：

   ```sh
   systemd-run --user --collect --quiet --property=Type=exec \
     /usr/bin/python3 "$HOME/.var/app/com.valvesoftware.Steam/data/AALC/compatibility/launch_aalc.py"
   ```

重复打开会恢复已有 AALC 窗口。直接运行 `AALC.exe` 不会加载兼容层。

## 升级与配置

先正常关闭 AALC，将现用 **整个安装目录** 留作备份。新版解压至独立目录，将自己的 `config.yaml`、`theme_pack_list.yaml`、`config_backup/` 复制过去，再对新目录运行 `prepare.py`。确认能启动、截图及读取配置后，才替换原安装目录。

准备工具只安装 `compatibility/` 和 `diagnostics/python/`，不改写现有配置；替换前会把这两项原有内容及配置快照保存到 `linux-compat-backup-时间/`。AALC 首次运行会按上游规则补齐新增默认字段。兼容层保持软件本体自动更新关闭、图片资源同步按原配置运行。

每个 AALC 版本需单独验证，准备工具目前只接受 V1.6.1。回退时关闭 AALC，恢复此前整个安装目录；如果升级后又修改过配置，应先单独保留最新配置，再决定是否迁回。无需恢复游戏、汉化或 Proton 前缀。

## 工作方式与问题定位

```text
Linux launch_aalc.py
  ├─ 找到运行中游戏的 Flatpak 实例与 Proton 环境
  ├─ capture_bridge.py → XComposite → 游戏窗口实时帧
  └─ flatpak enter → 同一 Proton 环境 → Windows Python
       └─ 官方冻结模块 + 兼容钩子
            ├─ AALC 原有 Qt 界面、OCR、任务与输入
            ├─ 截图入口 → 127.0.0.1 游戏客户区截图桥
            └─ 通知入口 → Linux notify-send
```

运行细节、补丁边界见 [设计说明](docs/design.md)。验证范围见 [验证记录](docs/validation.md)。

启动日志：安装目录 `logs/linux-launcher.log`；业务日志：`logs/debugLog.log`。截图桥在无法取得画面时返回错误，不用黑图或缓存帧替代。关闭 AALC 后，启动器清理桥接服务及状态文件。

## 参与测试

报告 AALC 版本、发行版、桌面会话、Steam 安装方式、Proton 版本、显卡，以及失败步骤。分享日志前清除用户名、本机路径、账号信息和私人配置。跨环境结果应写明具体功能与实际结果。

## 许可与来源

本仓库按 AGPL-3.0-or-later 发布，保留上游来源及 [LICENSE](LICENSE)。只发布兼容层源码和文档；官方程序、冻结模块、Python 运行时、游戏资源及用户配置在本机准备，不进入本仓库。上游图标及其他素材的许可另依上游声明，详见 [第三方说明](THIRD_PARTY.md)。
