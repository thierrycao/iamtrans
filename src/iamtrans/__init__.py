# src/iamtrans/__init__.py
"""iamtrans - Terminal Translation Tool

一个终端翻译工具，三列浮窗设计，有道词典加持。

为什么用 iamtrans？
- Enter 翻译，不换行 —— 你的键盘会感谢你
- 有道词典智能查词 —— 英文单词有音标，中文单字有拼音
- 异步处理，UI 不卡 —— 网络请求不阻塞界面
- 无需 API key —— 有道免费接口，用就完事了

Example:
    >>> import iamtrans
    >>> iamtrans.main(['Hello', 'World'])
    你好世界

    >>> # 或直接运行 TUI
    >>> iamtrans.main()  # 启动浮窗界面
"""
__version__ = "1.0.0"

from .main import main

__all__ = ["main", "__version__"]