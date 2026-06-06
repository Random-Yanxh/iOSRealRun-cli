# GUI 打包说明

本项目的 GUI 入口是 `gui.py`。Windows 打包使用 PyInstaller 的 onefile 模式，产物目录中包含：

- `iOSRealRun-GUI.exe`
- `config.yaml`
- `*route.txt`
- `DeveloperDiskImage`
- `libimobiledevice\win`

## Windows 本地打包

在项目根目录执行：

```powershell
.\build_gui_windows.ps1
```

打包完成后产物在：

```text
dist\iOSRealRun-GUI\iOSRealRun-GUI.exe
```

把整个 `dist\iOSRealRun-GUI` 文件夹发给测试人员即可。`iOSRealRun-GUI.exe` 已包含 Python 运行时，但设备连接工具、路线文件、配置文件和 DeveloperDiskImage 仍需要和 exe 放在同一个产物目录中。

## 使用前提

Windows 测试机仍需要有可用的 iOS 设备驱动。通常安装 iTunes 后即可。
