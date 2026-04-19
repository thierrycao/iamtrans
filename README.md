<div align="center">

# iamtrans

**终端翻译，就该这么用**

Enter 一敲，翻译就到。不换行，不卡顿，不占屏。

[![PyPI](https://img.shields.io/pypi/v/iamtrans?color=blue)](https://pypi.org/project/iamtrans/)
[![Python](https://img.shields.io/pypi/pyversions/iamtrans?color=green)](https://pypi.org/project/iamtrans/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/iamtrans?color=purple)](https://pypi.org/project/iamtrans/)

</div>

---

## 这玩意儿是什么？

一个终端翻译工具。

但它不是那种"输入→等待→输出"的玩意儿。

```bash
$ iamtrans Hello World
你好世界
```

太简单？那就启动浮窗：

```
+----------------------------------------------------------------------+
| +----------+--------------------+--------------------+              |
| | 输入框    | 词典               | 翻译               |              |
| |          |                    |                    |              |
| | Hello    | hello              | 你好               |              |
| |          | UK[...] US[...]    |                    |              |
| | 有道     | [int.] 喂，你好    |                    |              |
| | 翻页     | 例: Hello, how are |                    |              |
| +----------+--------------------+--------------------+              |
| Enter 翻译 | Esc 关闭 | Tab 切换引擎                             |
+----------------------------------------------------------------------+
```

**50字符宽，浮在终端上方**。不挡视线，不占全屏，看着舒服。

---

## 为什么用它？

| 问题 | iamtrans 的答案 |
|------|-----------------|
| Enter 会换行？ | 重写了 TextArea，Enter = 翻译，不换行 |
| 网络请求卡 UI？ | Worker 后台线程，主线程继续响应 |
| 要选语言？ | 检测中文自动翻译成英文，检测英文自动翻译成中文 |
| 要 API key？ | 有道免费接口，用就完事了 |
| 词典只支持英文？ | 中英文都行，有音标有拼音有例句 |

---

## 安装

### pip（推荐）

```bash
pip install iamtrans
```

### 二进制（无需 Python）

从 [Releases](https://github.com/thierrycao/iamtrans/releases) 下载：

| 平台 | 文件 |
|------|------|
| Linux | iamtrans-linux |
| macOS | iamtrans-macos |
| Windows | iamtrans-windows.exe |

```bash
chmod +x iamtrans-macos
./iamtrans-macos
```

### 从源码

```bash
git clone https://github.com/thierrycao/iamtrans.git
cd iamtrans
pip install -e .
```

---

## 使用

### TUI 模式

直接运行，启动浮窗：

```bash
iamtrans
```

**快捷键**：

| 键 | 作用 |
|----|------|
| Enter | 翻译（关键创新点） |
| Esc | 关闭 |
| Tab | 切换引擎 |
| 上/下 | 滚动翻页 |

### 命令行模式

适合脚本调用、管道操作：

```bash
iamtrans Hello World
# -> 你好世界

iamtrans 你好世界
# -> Hello World（自动检测中文，翻译成英文）

iamtrans --to ja Hello
# -> 

iamtrans --list
# -> 列出所有语言
```

---

## 词典功能

**输入英文单词**：

```
hello -> UK[həˈləʊ] US[həˈloʊ]
       [int.] 喂，你好（用于问候）
       例: "Hello, how are you today?"
       [n.] 招呼，问候
```

**输入中文单字**：

```
好 -> 拼音: hào/hǎo
     [形容词] 美；优点多的；令人满意的
     例: 这孩子长得真好
     [动词] 喜爱；喜欢
     例: 这个人好搬弄是非
```

有道词典 `newhh` 字段，多音字、词性、例句都有。

---

## 翻译引擎

| 引擎 | 特点 | 限制 |
|------|------|------|
| youdao | 默认，中文友好 | 无 |
| google | 稳定可靠 | 无 |
| mymemory | 欧洲服务 | 5000 字符/日 |

切换引擎：Tab 键，或 `--engine google`

---

## 技术细节

### 异步处理流程

```
用户输入 -> Enter 键
         -> TranslateTextArea.on_key() 捕获
         -> post_message(TranslateRequest)
         -> run_worker(thread=True) 后台执行
         -> 有道 API -> 网络延迟 300ms
         -> post_message(TranslateResult)
         -> 更新 UI
```

主线程从未停止响应。你的键盘输入，它一直听着。

### 语言检测算法

```python
def detect_language(text):
    # 中文字符：Unicode 区间 \u4e00-\u9fff
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return 'zh-CN'
    
    # 英文：字母占比 > 70%
    alpha_ratio = alpha_chars / total_chars
    return 'en' if alpha_ratio > 0.7 else 'auto'
```

简单，但够用。

### 有道 API 端点

| 用途 | URL | 参数 |
|------|-----|------|
| 翻译 | dict.youdao.com/suggest | q=text&le=eng|ch |
| 英文词典 | dict.youdao.com/jsonapi | q=word&le=eng |
| 中文词典 | dict.youdao.com/jsonapi | q=字&le=ch |

解析 JSON，提取 `ec`（英文）或 `newhh`（中文）字段。

---

## 打包发布

项目自带脚本，一键搞定：

```bash
# 本地打包 wheel + sdist
./scripts/build_local.sh

# 本地二进制
./scripts/build_binary.sh

# 版本管理
./scripts/version.sh bump patch  # 1.0.0 -> 1.0.1

# 一键发布（打包 + tag + GitHub 推送）
./scripts/release.sh 1.0.1
```

推送 tag 后，GitHub Actions 自动：
- 发布到 PyPI
- 构建 Linux/macOS/Windows 二进制
- 创建 GitHub Release

**设置 PyPI Token**：`repo -> Settings -> Secrets -> PYPI_TOKEN`

---

## 项目结构

```
src/iamtrans/
├── main.py           # CLI 入口，参数解析
├── translator/
│   └── engine.py     # 翻译引擎 + 词典 + 语言检测
└── ui/
    └── app.py        # Textual TUI，三列布局，Worker 异步

scripts/              # 打包发布脚本
.github/workflows/    # CI/CD：ci.yml + release.yml
docs/ARCHITECTURE.md  # 技术架构详解
```

---

## 为什么是 Textual？

Textual 是终端 UI 的现代选择：
- 异步友好（Worker API）
- CSS 样式（不用手画边框）
- 事件驱动（Message 消息流）

比 curses 简洁，比 prompt_toolkit 强大。

---

## License

MIT。随便用，随便改，随便发。

---

<div align="center">

**有问题？[开个 Issue](https://github.com/thierrycao/iamtrans/issues)**

**想贡献？[看 CONTRIBUTING.md](CONTRIBUTING.md)**

**想懂技术？[看 ARCHITECTURE.md](docs/ARCHITECTURE.md)**

</div>