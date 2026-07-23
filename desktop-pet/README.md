# 桌面萌宠（视频版）

双击 `DesktopPet.exe` 即可使用，无需安装 Python。

## 一键使用

1. 下载发布包里的 `DesktopPet.exe`
2. 确认这 10 个视频在「下载」文件夹（或放进 exe 同目录的 `videos` 文件夹）：
   - `video.mp4` … `video (9).mp4`
3. 双击 `DesktopPet.exe`

程序会自动选用体积更大的真实素材；若来自「下载」文件夹，还会复制到 exe 旁的 `videos\`，方便以后带走。

## 功能

- 透明窗口、始终置顶；左键拖动
- 点击轮流播放互动动作；右键切换全部动作
- 自动抠背景（绿幕 / 白底 / 黑底 / 自动）
- 滚轮缩放、静音开关

## 素材默认映射

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

映射可在 `assets/videos.json` 修改（开发模式）。

## 开发运行

```bat
cd desktop-pet
pip install -r requirements.txt
python main.py
```

## 打包

```bat
build_windows.bat
```

产物：`dist\DesktopPet.exe`。也可通过 GitHub Actions 工作流自动构建。
