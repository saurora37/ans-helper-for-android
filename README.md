# Ans Helper · 安卓离线查题 App

把桌面版 PyQt5 答题辅助软件用 **Kivy 重写**，可打包成安卓 APK。
纯离线：题库数据库 `questions.db`（50 题，单选30+多选20）已打包在应用内。
- 应用名称：Ans Helper
- 图标：`icon.png`（打包时自动生成各分辨率）

## 功能
- 关键词搜题（题目/答案都能搜）
- 按题库分类筛选
- 点击题目卡片展开/收起答案
- 无需联网、无需服务端

## 本地调试（Windows 也能跑）
```bash
pip install kivy
cd android_app
python main.py
```

## 打包成 APK（二选一）

### 方式 A：本机 WSL（需要管理员 + 重启一次）
```powershell
# PowerShell 管理员，装 WSL（会重启电脑）
wsl --install
```
重启后进入 Ubuntu：
```bash
sudo apt update && sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses-dev libtio
pip install buildozer
# 把 android_app 整个目录拷进 WSL，然后：
cd android_app
buildozer android debug
```
首次会下载 Android SDK/NDK（约 1~2 GB，耐心等），成功后 APK 在 `bin/` 目录。

### 方式 B：GitHub Actions 云端打包（不用装 WSL，推荐）
1. 把 `android_app/` 推到 GitHub 仓库。
2. 新建 `.github/workflows/build.yml`：
```yaml
name: build-apk
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install buildozer
      - run: sudo apt update && sudo apt install -y openjdk-17-jdk
      - run: buildozer android debug
      - uses: actions/upload-artifact@v4
        with:
          name: app-debug-apk
          path: bin/*.apk
```
3. push 后在 Actions 页面下载产物 `app-debug-apk` 即为 APK。

## 目录说明
- `main.py` — Kivy 应用源码
- `questions.db` — 已导入的题库（与桌面端共用同一份）
- `buildozer.spec` — 打包配置
