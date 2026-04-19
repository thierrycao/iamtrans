# iamtrans 技术架构

一个终端翻译工具的技术解剖。

## 设计哲学

**问题**：市面翻译工具要么全屏占屏，要么功能臃肿，要么 API 要钱。

**方案**：
- 浮窗设计：50字符宽度，不挡视线，不占全屏
- 有道免费接口：无需 API key，中文用户友好
- 智能检测：输入中文翻译成英文，输入英文翻译成中文，不用选语言
- 异步处理：网络请求在后台，UI 不卡顿

## 核心模块

### 1. 翻译引擎 (`translator/engine.py`)

```python
class TranslatorEngine:
    def translate(text, source='auto', target='zh-CN') -> str
    def smart_translate(text) -> str  # 自动检测语言并切换目标
    def lookup_dictionary(word) -> DictionaryResult
```

**有道 API 调用策略**：

| 场景 | API | 参数 |
|------|-----|------|
| 翻译 | `suggest?q=text&le=eng|ch&doctype=json` | `le` 根据检测语言切换 |
| 英文词典 | `jsonapi?q=word&le=eng` | 解析 `ec` 字段 |
| 中文词典 | `jsonapi?q=字&le=ch` | 解析 `newhh` 字段 |

**智能语言检测**：
```python
def detect_language(text):
    # 中文字符检测：\u4e00-\u9fff
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return 'zh-CN'
    # 英文检测：字母占比 > 70%
    alpha_ratio = alpha_chars / total_chars
    return 'en' if alpha_ratio > 0.7 else 'auto'
```

### 2. TUI 界面 (`ui/app.py`)

**三列布局**：

```
TripleColumnScreen (Screen)
├── Vertical (#left-column, width: 16)
│   ├── TranslateTextArea (#input-box)
│   ├── Label (#lang-label)
│   ├── Label (#engine-label)
│   └── Label (.hint-text)
├── Vertical (#dict-column, width: 1fr)
│   └── Label/Static (词典内容)
└── Vertical (#trans-column, width: 1fr)
    └── Label/Static (翻译内容)
```

**异步处理流程**：

```
用户输入 -> TranslateTextArea.on_key(Enter)
         -> post_message(TranslateRequest)
         -> TripleColumnScreen.on_translate_request
         -> run_worker(_worker_translate, thread=True)
         -> 网络请求（后台线程）
         -> post_message(TranslateResult)
         -> TripleColumnScreen.on_translate_result
         -> _show_results (更新 UI)
```

**为什么用 Worker？**

Textual 的 Worker API 可以：
1. 在后台线程执行同步函数（`thread=True`）
2. 不阻塞主线程事件循环
3. 通过 Message 机制安全传递结果

如果直接调用 `_safe_translate()`，UI 会卡住几秒（网络延迟）。用 Worker 后，用户可以继续操作界面。

### 3. CLI 入口 (`main.py`)

```python
def main(args=None):
    # 无参数 -> TUI 模式
    # 有参数 -> 简洁模式
```

**参数处理优先级**：
1. `--list` -> 列出语言/引擎
2. `text` 或 `--text-arg` -> 简洁翻译
3. 默认 -> 启动 TUI

## 依赖关系

```
main.py
  ├── translator/engine.py (翻译/词典)
  └── ui/app.py (TUI 界面)
       └── translator/engine.py (词典查询)

外部依赖：
  ├── textual (TUI 框架)
  ├── rich (终端美化)
  └── deep-translator (Google/MyMemory 封装)
```

## 数据流

### 翻译流程

```
输入 "Hello"
  -> detect_language("Hello") = 'en'
  -> smart_translate(text, target='zh-CN')
  -> translate(text, source='auto', target='zh-CN')
  -> _translate_youdao(text)
  -> https://dict.youdao.com/suggest?le=eng&doctype=json
  -> 解析 entries[0]['explain']
  -> "你好"
```

### 词典流程（英文）

```
输入 "hello"
  -> is_single_word("hello") = True
  -> lookup_dictionary("hello")
  -> detect_language("hello") = 'en'
  -> le = 'eng'
  -> https://dict.youdao.com/jsonapi?le=eng
  -> 解析 ec.word[0]:
      -> ukphone, usphone -> phonetic
      -> trs[].tr[].l.i -> definitions
  -> DictionaryResult(
       phonetic="UK[həˈləʊ] US[həˈloʊ]",
       definitions=[{"partOfSpeech": "int.", "definition": "喂，你好"}]
     )
```

### 词典流程（中文）

```
输入 "好"
  -> is_single_word("好") = True
  -> lookup_dictionary("好")
  -> detect_language("好") = 'zh-CN'
  -> le = 'ch'
  -> https://dict.youdao.com/jsonapi?le=ch
  -> 解析 newhh.dataList:
      -> pinyin -> phonetic
      -> sense[].def -> definitions
  -> DictionaryResult(
       phonetic="拼音: hào/hǎo",
       definitions=[{"partOfSpeech": "hǎo·形容词", "definition": "美；优点多的"}]
     )
```

## 打包发布

### pip 包

```bash
python -m build  # 生成 wheel + sdist
twine upload dist/*  # 发布到 PyPI
```

**pyproject.toml 关键配置**：
```toml
[project.scripts]
iamtrans = "iamtrans:main"  # 入口点

[tool.setuptools.packages.find]
where = ["src"]  # 源码目录
```

### PyInstaller 二进制

```bash
pyinstaller iamtrans.spec  # 单文件可执行
```

**隐藏导入**（必须声明，否则打包失败）：
```python
hiddenimports=[
    'iamtrans', 'iamtrans.main', 'iamtrans.translator', 'iamtrans.ui',
    'textual', 'textual.app', 'textual.widgets',
    'deep_translator', 'deep_translator.google_translator',
]
```

### GitHub CI/CD

```
push tag 'v*'
  -> release.yml 触发
  -> build-pypi: python -m build -> twine upload
  -> build-linux: pyinstaller -> iamtrans-linux
  -> build-macos: pyinstaller -> iamtrans-macos
  -> build-windows: pyinstaller -> iamtrans-windows.exe
  -> release: 创建 GitHub Release，上传所有文件
```

## 性能考量

**网络延迟**：
- 有道 API 响应：200-500ms
- Google Translate：300-800ms（deep-translator 封装）
- MyMemory：400-1000ms

**异步必要性**：
500ms 延迟如果不异步，UI 会卡住半秒，用户体验极差。Worker 后台执行，主线程继续响应键盘输入。

**内存占用**：
- TUI 运行：约 30MB（Textual + rich）
- PyInstaller 二进制：约 15MB（压缩后）

## 未来扩展

**离线模式**：
- 本地 SQLite 缓存翻译结果
- 离线词典（如 CC-CEDICT）

**语音朗读**：
- macOS: `say` 命令
- Linux: `espeak`
- TTS API: 百度/讯飞

**OCR 截图**：
- macOS: Swift 截图 + Vision OCR
- 跨平台: Tesseract + Pillow

---

技术选型总结：
- Textual：终端 UI，现代风格，异步友好
- 有道 API：免费，中文优化，词典丰富
- PyInstaller：单文件分发，用户无需安装 Python
- GitHub Actions：自动化发布，跨平台构建