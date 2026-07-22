# 桌面宠物 (Desktop Pet)

透明无边框、始终置顶的 Windows 桌面宠物。左键拖动，点击互动，右键菜单与滚轮调大小。

## 功能

- 透明窗口、无边框、默认置顶；左键拖动位置
- 待机自动摇尾巴、轻轻转头点头
- 点击角色轮流触发：跳跃 / 压扁回弹 / 左右抖动（点击后尾巴会摇得更欢）
- 互动时随机弹出不透明中文对话气泡（位于角色上方，不遮挡猫咪）
- 右键菜单：调整大小、置顶开关、退出
- 鼠标滚轮缩放
- 支持打包为单个 `DesktopPet.exe`，双击即可运行

## 快速运行（开发）

```bash
cd desktop-pet
pip install -r requirements.txt
python main.py
```

## 打包 Windows EXE

在 **Windows** 上安装 [Python 3.10+](https://www.python.org/downloads/)（勾选 Add to PATH），然后双击：

```text
build_windows.bat
```

或手动执行：

```bat
pip install -r requirements.txt
pyinstaller --noconfirm desktop_pet.spec
```

生成文件：`dist\DesktopPet.exe`

也可用仓库内 GitHub Actions 工作流 `.github/workflows/build-desktop-pet.yml` 自动构建 Windows 产物。

## 操作说明

| 操作 | 效果 |
|------|------|
| 左键拖动 | 移动桌宠 |
| 左键点击角色 | 轮流互动 + 中文气泡 |
| 鼠标滚轮 | 放大 / 缩小 |
| 右键菜单 | 大小 / 置顶 / 退出 |

## 目录结构

```text
desktop-pet/
  main.py              # 主程序
  assets/cat.png       # 透明背景精灵图
  desktop_pet.spec     # PyInstaller 配置
  build_windows.bat    # 一键打包
  requirements.txt
```
