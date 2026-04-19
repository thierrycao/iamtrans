# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-20

### Added

**核心功能**
- TUI 浮窗界面，三列紧凑布局（输入 | 词典 | 翻译）
- 有道翻译作为默认引擎，无需 API key，专为中文用户优化
- 智能词典查询：英文单词显示 UK/US 音标 + 词性释义，中文单字显示拼音 + 例句
- 智能翻译：自动检测语言，中文→英文，英文→中文，无需手动切换
- Enter 触发翻译，不换行；异步处理，UI 不卡顿
- 三引擎支持：有道(默认)、Google Translate、MyMemory

**CLI 模式**
- `iamtrans` 启动 TUI（默认浮窗模式）
- `iamtrans Hello World` 简洁翻译输出
- 支持 `--from`、`--to`、`--engine` 参数

**打包发布**
- pip 包支持 (`pip install iamtrans`)
- PyInstaller 跨平台二进制（Linux/macOS/Windows）
- GitHub CI/CD：自动 PyPI 发布 + 二进制构建 + Release
- 本地打包脚本：`scripts/build_local.sh`、`scripts/build_binary.sh`
- 一键发布脚本：`scripts/release.sh`

### Architecture

```
src/iamtrans/
├── translator/engine.py   # 翻译引擎 + 有道词典 API
├── ui/app.py              # Textual TUI 三列布局
└── main.py                # CLI 入口
```

### APIs Used

| 服务 | URL | 用途 |
|------|-----|------|
| 有道翻译 | `dict.youdao.com/suggest` | 翻译结果 |
| 有道词典(英) | `dict.youdao.com/jsonapi?le=eng` | 英文单词释义 |
| 有道词典(中) | `dict.youdao.com/jsonapi?le=ch` | 中文单字释义 |

---

## [Unreleased]

### Planned

- 离线模式：本地词典缓存
- 历史记录：SQLite 存储
- 语音朗读：TTS 支持
- OCR 截图翻译