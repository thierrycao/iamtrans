# src/iamtrans/ui/__init__.py
"""TUI 用户界面模块

三列浮窗设计，灵感来自现代 AI 应用：

┌──────────────────────────────────────────────────┐
│ 输入框 | 词典卡片 | 翻译结果                      │
│        |          |                               │
│ 智能翻译 | 📖 hello | 你好                        │
│ 🔧有道  | UK[...]  |                              │
│ ↑↓翻页  | [n.] 释义 |                             │
└──────────────────────────────────────────────────┘

核心设计：
- TranslateTextArea: Enter 翻译，不换行
- TripleColumnScreen: 三列布局，左输入/中词典/右翻译
- Worker 异步: 网络请求不阻塞 UI
- Message 消息: TranslateRequest → TranslateResult

快捷键：
- Enter: 翻译
- Tab: 切换引擎
- ↑↓: 滚动翻页
- Esc: 关闭

基于 Textual 框架，终端 UI 的现代选择。
"""
from .app import IAmTransFloatApp, TripleColumnScreen

__all__ = ["IAmTransFloatApp", "TripleColumnScreen"]