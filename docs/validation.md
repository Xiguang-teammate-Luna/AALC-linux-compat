# 验证记录

日期：2026-11-12。

环境：Fedora 44 KDE Plasma Wayland、XWayland 游戏窗口、Flatpak Steam、GE-Proton11-12-x86_64、Direct3D 11、中文游戏界面，AALC V1.6.1。

## 已完成

- 从上游官方 V1.6.1 包提取启动模块，用兼容启动器启动完整中文界面，窗口标题显示 V1.6.1。
- 升级时复制现有 `config.yaml` 和 `theme_pack_list.yaml`，在 GUI 关闭、正式路径重启后递归比较全部原有字段，原有值无变化；新增默认字段为卡死超时及8项主题包条目。
- 五次 RGB 截图尺寸与 Win32 客户区一致，四组相邻帧均有变化；灰度截图为 L 模式，中文 OCR 可识别真实游戏界面。
- 最小化后通过后台输入模块恢复窗口；窗口无透明／鼠标穿透标记，截图成功。
- Linux 桌面通知发送成功。
- 调用 AALC 原有截图小工具，成功保存1600×900 RGB画面；关闭后桥接状态文件清理，进程退出。
- 原桌面入口对应命令从正式路径重启成功，重复打开恢复已有窗口，图片资源清单检查成功。
- 发布前使用 `prepare.py` 在独立目录从官方程序及 Windows Python 3.13 embeddable ZIP 重建，无旧 `diagnostics/lib` 和源码补充路径；重新通过截图、OCR、最小化恢复、通知和商店运行时布尔配置检查。
- 准备工具集成测试通过：配置及主题权重字节不变，二次安装保留旧兼容目录、运行时路径可重建，未支持版本在写入前被拒绝。

## 范围

V1.6.1 本轮未运行经验本、纽本或完整镜牢通关；此前 V1.6.0 的日常及镜牢记录不作为 V1.6.1 通关证明。本次后台输入验证覆盖模块初始化与恢复激活，没有新增战斗点击验证。

尚待社区验证：其他发行版／显卡／Proton、原生包Steam、原生Wayland窗口、非中文游戏界面、模拟器及计划任务。当前脚本的启动路径明确依赖Flatpak Steam。

## 复现准备工具检查

在仓库内准备好官方包解压目录和Python ZIP后运行：

```sh
AALC_TEST_RELEASE=/path/to/unpacked/AALC \
AALC_TEST_PYTHON_ZIP=/path/to/python-3.13.x-embed-amd64.zip \
  .venv/bin/python -m unittest discover -s tests -v
```

未提供这两个路径时，测试明确跳过，不会下载或运行游戏。
