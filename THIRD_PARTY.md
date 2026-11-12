# 来源与第三方组件

- AALC：[KIYI671/AhabAssistantLimbusCompany](https://github.com/KIYI671/AhabAssistantLimbusCompany)，AGPL-3.0。兼容入口复用其公开模块接口和启动行为；本仓库未打包其程序、冻结代码或素材。
- PyInstaller：安装准备阶段使用其 `CArchiveReader`。具体许可及 bootloader exception 见 [PyInstaller COPYING](https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt)。运行所需加载器由准备工具从用户本机官方 AALC 中提取。
- Python Windows embeddable distribution：由用户从 python.org 下载，其许可证保留在本机发行包中，遵循 [Python license](https://docs.python.org/3/license.html)。
- Pillow、X11／XComposite、Flatpak、Proton、Qt 及 AALC 自带依赖按各自许可使用，不随本仓库重新分发。
- 上游图标、游戏图像／音频和字体许可见上游 README；本仓库不包含这些素材。
