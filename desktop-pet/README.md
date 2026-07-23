# 桌面萌宠（视频版）

透明无边框、始终置顶的 Windows 桌面萌宠。使用你提供的 10 段 MP4 作为动作素材。

## 功能

- 透明窗口 + 自动抠背景（绿幕 / 白底 / 黑底 / 自动取角落色）
- 左键拖动位置；点击角色轮流播放互动动作
- 右键菜单：切换全部动作、调大小、抠像模式、置顶、静音、退出
- 滚轮缩放
- 待机时在「待机 / 张望」间自动切换
- 支持打包为单个 `DesktopPet.exe`

## 素材对应关系

把 Downloads 里的视频导入后，默认映射如下（可在 `assets/videos.json` 改）：

| 文件 | 动作 |
|------|------|
| `video.mp4` | 待机 |
| `video (1).mp4` | 张望 |
| `video (2).mp4` | 走路 |
| `video (3).mp4` | 奔跑 |
| `video (4).mp4` | 坐下 |
| `video (5).mp4` | 睡觉 |
| `video (6).mp4` | 吃东西 |
| `video (7).mp4` | 开心 |
| `video (8).mp4` | 被摸 |
| `video (9).mp4` | 特殊 |

## 快速开始（Windows）

1. 安装 [Python 3.10+](https://www.python.org/downloads/)（勾选 Add to PATH）
2. 导入素材（任选其一）：

```bat
cd desktop-pet
scripts\import_videos.bat
```

或手动：

```bat
python scripts\import_videos.py --from "C:\Users\1\Downloads"
```

3. 安装依赖并运行：

```bat
pip install -r requirements.txt
python main.py
```

也可双击 `run.bat`。

## 打包 EXE

```bat
build_windows.bat
```

产物：`dist\DesktopPet.exe`（会打包进 `assets/videos/` 下的视频）。

也可用 GitHub Actions：`.github/workflows/build-desktop-pet.yml`。

## 操作说明

| 操作 | 效果 |
|------|------|
| 左键拖动 | 移动桌宠 |
| 左键点击 | 轮流：被摸 → 开心 → 吃东西 → 特殊 → 坐下 |
| 鼠标滚轮 | 放大 / 缩小 |
| 右键菜单 | 动作 / 大小 / 抠像 / 置顶 / 声音 / 退出 |

## 抠像说明

若角色周围有纯色背景，右键 → **背景抠像**：

- **自动（推荐）**：采样画面四角颜色做透明
- **绿幕 / 白底 / 黑底**：强制指定背景色
- **关闭**：保留原视频背景

阈值可在 `assets/videos.json` 的 `chroma_threshold` 调整（越大抠得越狠）。

## 目录结构

```text
desktop-pet/
  main.py
  assets/videos.json      # 动作映射与对话
  assets/videos/*.mp4     # 你的 10 段素材
  scripts/import_videos.* # 从 Downloads 导入
  desktop_pet.spec
  requirements.txt
```
