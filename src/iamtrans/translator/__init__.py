# src/iamtrans/translator/__init__.py
"""翻译引擎模块

封装有道、Google、MyMemory 翻译服务 + 有道词典查询。

设计思路：
- 默认有道翻译 —— 中文用户首选，翻译结果接地气
- 智能语言检测 —— 中文输入自动翻译成英文，英文输入自动翻译成中文
- 词典查询分语言 —— 英文用 ec 字段（音标+词性），中文用 newhh 字段（拼音+例句）

API 无需认证，直接调用：
- 有道翻译: dict.youdao.com/suggest
- 有道词典: dict.youdao.com/jsonapi

Example:
    >>> from iamtrans.translator import TranslatorEngine
    >>> engine = TranslatorEngine('youdao')
    >>> engine.translate('Hello')
    你好
    >>> engine.smart_translate('你好')  # 智能模式：中文→英文
    Hello

    >>> # 词典查询
    >>> result = TranslatorEngine.lookup_dictionary('hello')
    >>> print(result.phonetic)
    UK[həˈləʊ] US[həˈloʊ]
"""
from .engine import (
    TranslatorEngine,
    DictionaryResult,
    ENGINES,
    LANGUAGES,
    DICTIONARY_SOURCES,
    DEFAULT_DICT_SOURCE,
    DEFAULT_ENGINE,
)

__all__ = [
    "TranslatorEngine",
    "DictionaryResult",
    "ENGINES",
    "LANGUAGES",
    "DICTIONARY_SOURCES",
    "DEFAULT_DICT_SOURCE",
    "DEFAULT_ENGINE",
]