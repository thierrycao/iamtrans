"""iamtrans 浮窗翻译工具 - 三列精炼设计

界面布局（50字符宽度，紧凑不占屏）：

┌──────────────────────────────────────────────────┐
│ ┌─────────┬──────────────┬──────────────┐       │
│ │ 输入框   │ 词典卡片     │ 翻译结果     │       │
│ │ (16宽)  │ (自动宽度)   │ (自动宽度)   │       │
│ │         │              │              │       │
│ │ 智能翻译 │ 📖 hello     │ 你好         │       │
│ │ 🔧有道   │ UK[...] US[] │              │       │
│ │ ↑↓翻页   │ [n.] 释义    │              │       │
│ └─────────┴──────────────┴──────────────┘       │
└──────────────────────────────────────────────────┘

技术要点：
1. TranslateTextArea: 重写 on_key，Enter 触发翻译而非换行
2. Worker 异步: run_worker(thread=True) 在后台执行翻译，UI 不卡顿
3. Message 消息流: TranslateRequest → _worker_translate → TranslateResult → _show_results
4. Reactive 状态: engine/source/target 自动同步到界面

为什么是三列？
- 左列固定宽度，输入区稳定
- 中右列自动宽度，内容自适应
- 词典和翻译并列，一目了然

基于 Textual 框架构建，终端 UI 的最佳选择。
"""
import json
import urllib.request
import urllib.error
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import TextArea, Static, Label, Button
from textual.binding import Binding
from textual.reactive import reactive
from textual.events import Key
from textual.message import Message
from textual.screen import Screen

from ..translator import TranslatorEngine, DictionaryResult, ENGINES, LANGUAGES, DEFAULT_ENGINE


# ==================== 自定义消息 ====================

class TranslateRequest(Message):
    """翻译请求消息"""
    def __init__(self, text: str):
        super().__init__()
        self.text = text


class TranslateResult(Message):
    """翻译结果消息"""
    def __init__(self, text: str, translation: str, dict_result, error: str = None):
        super().__init__()
        self.text = text
        self.translation = translation
        self.dict_result = dict_result
        self.error = error


class TranslateTextArea(TextArea):
    """翻译输入框 - Enter触发翻译而非换行"""

    DEFAULT_CSS = """
    TranslateTextArea {
        height: 2;
        border: none;
        background: $surface;
        padding: 0;
    }
    """

    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text.strip()
            if text:
                self.clear()
                self.post_message(TranslateRequest(text))


# ==================== 三列结果面板 ====================

class TripleColumnScreen(Screen):
    """三列精炼浮窗界面"""

    DEFAULT_CSS = """
    TripleColumnScreen {
        layout: horizontal;
        height: auto;
        max-height: 10;
        width: 50;  /* 只占一半宽度 */
        padding: 0;
        background: $surface;
    }

    TripleColumnScreen:inline {
        border: round $primary;
        background: $surface-darken-2;
    }

    /* 左列：输入+语言 */
    #left-column {
        width: 16;
        height: auto;
        padding: 1;
        background: $panel-darken-1;
        border-right: solid $primary;
    }

    #input-box {
        height: 2;
        border: none;
        background: $surface;
        margin-bottom: 1;
    }

    .lang-select {
        height: 1;
        color: $text-muted;
        padding: 0;
        margin: 0;
    }

    .engine-btn {
        height: 1;
        color: $accent;
        background: $accent 15%;
        padding: 0 1;
        margin-top: 1;
    }

    /* 中列：词典 */
    #dict-column {
        width: 1fr;
        height: auto;
        min-height: 6;
        max-height: 6;
        padding: 0 1;
        overflow-y: auto;
        border-right: solid $primary;
    }

    .dict-word {
        color: $accent;
        text-style: bold;
        height: 1;
    }

    .dict-phonetic {
        color: $text-muted;
        height: 1;
    }

    .dict-item {
        color: $text;
        height: 1;
        padding: 0;
        margin: 0;
    }

    .dict-pos {
        color: $accent;
        background: $accent 15%;
        padding: 0;
    }

    .dict-example {
        color: $success;
        height: 1;
    }

    /* 右列：翻译 */
    #trans-column {
        width: 1fr;
        height: auto;
        min-height: 6;
        max-height: 6;
        padding: 0 1;
        overflow-y: auto;
    }

    .trans-text {
        color: $text;
        height: auto;
        max-height: 6;
    }

    .empty-hint {
        color: $text-muted;
        height: 1;
    }

    /* 底部状态栏 */
    #status-bar {
        dock: bottom;
        height: 1;
        width: 100%;
        background: $primary 30%;
        padding: 0 1;
    }

    .hint-text {
        color: $text-muted;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "app.quit", "关闭"),
        Binding("tab", "cycle_engine", "引擎"),
        Binding("up", "scroll_up", "上页"),
        Binding("down", "scroll_down", "下页"),
    ]

    engine: reactive[str] = reactive(DEFAULT_ENGINE)
    source: reactive[str] = reactive('auto')
    target: reactive[str] = reactive('zh-CN')

    def __init__(self):
        super().__init__()
        self.translator = TranslatorEngine(self.engine)

    def compose(self) -> ComposeResult:
        # 左列：输入框 + 语言/引擎选择
        yield Vertical(
            TranslateTextArea(id="input-box"),
            Label("智能翻译", classes="lang-select", id="lang-label"),
            Label(f"🔧 {ENGINES[self.engine][:6]}", classes="engine-btn", id="engine-label"),
            Label("↑↓翻页 Esc退", classes="hint-text"),
            id="left-column"
        )

        # 中列：词典结果
        yield Vertical(
            Label("词典", classes="empty-hint"),
            id="dict-column"
        )

        # 右列：翻译结果
        yield Vertical(
            Label("翻译", classes="empty-hint"),
            id="trans-column"
        )

    def on_mount(self):
        self.query_one("#input-box", TranslateTextArea).focus()

    def on_translate_request(self, message: TranslateRequest) -> None:
        """处理翻译请求"""
        # 显示加载指示
        self._show_loading()
        # 使用 worker 在后台线程运行
        def do_translate():
            self._worker_translate(message.text)
        self.run_worker(do_translate, thread=True, name="translate")

    def on_translate_result(self, message: TranslateResult) -> None:
        """处理翻译结果消息 - 更新UI"""
        self._show_results(message.text, message.translation, message.dict_result, message.error)

    def _show_loading(self):
        """显示加载指示"""
        dict_col = self.query_one("#dict-column", Vertical)
        trans_col = self.query_one("#trans-column", Vertical)
        for child in list(dict_col.children):
            child.remove()
        for child in list(trans_col.children):
            child.remove()
        dict_col.mount(Label("⏳ 查询���...", classes="empty-hint"))
        trans_col.mount(Label("⏳ 翻译中...", classes="empty-hint"))

    def _worker_translate(self, text: str):
        """后台翻译 worker（在线程中运行）"""
        try:
            # 翻译（智能模式）
            result = self._safe_translate(text)

            # 词典查询（智能检测语言，支持中英文）
            dict_result = None
            if TranslatorEngine.is_single_word(text):
                dict_result = TranslatorEngine.lookup_dictionary(text)

            # 发送结果消息
            self.post_message(TranslateResult(text, result, dict_result, None))
        except Exception as e:
            err_msg = str(e)[:30]
            self.post_message(TranslateResult(text, "", None, err_msg))

    def _safe_translate(self, text: str) -> str:
        """安全的同步翻译（智能模式）"""
        try:
            # 使用智能翻译：自动检测语言并切换目标
            return self.translator.smart_translate(text, self.target)
        except Exception:
            return ""

    def _show_results(self, text: str, translation: str, dict_result, error: str):
        """显示结果"""
        dict_col = self.query_one("#dict-column", Vertical)
        trans_col = self.query_one("#trans-column", Vertical)

        # 清空旧内容
        for child in list(dict_col.children):
            child.remove()
        for child in list(trans_col.children):
            child.remove()

        if error:
            trans_col.mount(Label(f"❌ {error}", classes="empty-hint"))
            dict_col.mount(Label("—", classes="empty-hint"))
        else:
            # 显示翻译结果
            trans_col.mount(Label(translation, classes="trans-text"))

            # 显示词典结果
            if dict_result and dict_result.has_content():
                phonetic = dict_result.phonetic or ""
                dict_col.mount(Label(f"📖 {dict_result.word} {phonetic}", classes="dict-word"))
                for defn in dict_result.definitions[:5]:
                    pos = defn.get('partOfSpeech', '')[:4]
                    def_text = defn.get('definition', '')[:40]
                    dict_col.mount(Label(f"[{pos}] {def_text}", classes="dict-item"))
                    if defn.get('example'):
                        ex = defn.get('example', '')[:35]
                        dict_col.mount(Label(f"💡{ex}", classes="dict-example"))
            else:
                dict_col.mount(Label("—", classes="empty-hint"))

    def action_cycle_engine(self):
        engines = list(ENGINES.keys())
        self.engine = engines[(engines.index(self.engine) + 1) % len(engines)]
        self.translator = TranslatorEngine(self.engine)
        self.query_one("#engine-label", Label).update(f"🔧 {ENGINES[self.engine][:6]}")

    def action_scroll_up(self):
        dict_col = self.query_one("#dict-column", Vertical)
        trans_col = self.query_one("#trans-column", Vertical)
        dict_col.scroll_relative(y=-3, animate=False)
        trans_col.scroll_relative(y=-3, animate=False)

    def action_scroll_down(self):
        dict_col = self.query_one("#dict-column", Vertical)
        trans_col = self.query_one("#trans-column", Vertical)
        dict_col.scroll_relative(y=3, animate=False)
        trans_col.scroll_relative(y=3, animate=False)


# ==================== 主应用 ====================

class IAmTransFloatApp(App):
    """iamtrans 浮窗翻译应用"""

    CSS = """
    App {
        background: transparent;
    }

    App:inline {
        background: $surface-darken-3;
    }
    """

    def on_mount(self):
        self.push_screen(TripleColumnScreen())

    def run_inline(self):
        """以浮窗模式运行"""
        self.run(inline=True)