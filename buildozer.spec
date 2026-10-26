# Buildozer 打包配置：学生手册题库（安卓离线查题）
# 用法（在 Linux/WSL 内）： pip install buildozer; buildozer android debug

[app]
title = Ans Helper
package.name = handbookqa
package.domain = org.handbook.qa

source.dir = .
# 带上 .py、题库数据库和图标
source.include_exts = py,db,png

version = 1.0

requirements = python3,kivy

# 应用图标（512x512 PNG，构建时自动生成各分辨率）
icon.filename = %(source.dir)s/icon.png

# 竖屏
orientation = portrait

# 题库数据库在首次运行时复制到可写目录，需存储权限
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# 架构
android.archs = arm64-v8a, armeabi-v7a

# 去掉代码里的调试日志
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
