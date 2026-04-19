"""iamtrans CLI 主入口

两种模式，随你选：

1. TUI 模式（默认）—— 三列浮窗，词典卡片，赏心悦目
   $ iamtrans

2. 简洁模式 —— 一行命令，一行输出，适合脚本调用
   $ iamtrans Hello World
   你好世界

参数虽多，但大部分时候你不需要用：
- 默认源语言 auto（自动检测）
- 默认目标语言 zh-CN
- 默认引擎 youdao（有道，中文用户友好）

Example:
    # 启动 TUI
    >>> main()

    # 简洁翻译
    >>> main(['Hello'])
    你好

    # 指定引擎和语言
    >>> main(['Hello', '--engine', 'google', '--to', 'ja'])
    こんにちは
"""
import argparse
import sys
from typing import Optional, List

from .translator import TranslatorEngine, ENGINES, LANGUAGES
from .ui.app import IAmTransFloatApp


def main(args: Optional[List[str]] = None):
    """主入口函数

    Args:
        args: 命令行参数（默认使用 sys.argv）
    """
    parser = argparse.ArgumentParser(
        prog='iamtrans',
        description='iamtrans - 终端翻译工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  iamtrans                    启动 TUI 交互界面
  iamtrans Hello World        简洁模式翻译
  iamtrans --text "Hello" --to zh-CN  指定目标语言
  iamtrans --engine mymemory  使用 MyMemory 引擎
  iamtrans --from en --to ja  指定源语言和目标语言

快捷键 (TUI模式):
  Enter     翻译
  Ctrl+Q    退出
  Ctrl+L    清空
  Ctrl+S    交换语言
  Ctrl+E    切换引擎
  Tab       切换焦点
'''
    )

    # 直接翻译参数
    parser.add_argument(
        'text',
        nargs='*',
        help='要翻译的文本（简洁模式）'
    )

    parser.add_argument(
        '-t', '--text-arg',
        dest='text_arg',
        help='要翻译的文本（使用参数指定）'
    )

    parser.add_argument(
        '-f', '--from',
        dest='source',
        default='auto',
        choices=list(LANGUAGES.keys()),
        help='源语言 (默认: auto 自动检测)'
    )

    parser.add_argument(
        '-to', '--to',
        dest='target',
        default='zh-CN',
        choices=[k for k in LANGUAGES.keys() if k != 'auto'],
        help='目标语言 (默认: zh-CN)'
    )

    parser.add_argument(
        '-e', '--engine',
        dest='engine',
        default='google',
        choices=list(ENGINES.keys()),
        help=f'翻译引擎 (默认: google)'
    )

    parser.add_argument(
        '-l', '--list',
        dest='list_langs',
        action='store_true',
        help='列出支持的语言'
    )

    parser.add_argument(
        '--inline',
        action='store_true',
        default=True,
        help='浮窗模式运行（终端上方小窗口，默认启用）'
    )

    parser.add_argument(
        '--no-inline',
        action='store_false',
        dest='inline',
        help='全屏模式运行'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    parsed = parser.parse_args(args)

    # 列出语言
    if parsed.list_langs:
        print("支持的语言:")
        for code, name in LANGUAGES.items():
            print(f"  {code}: {name}")
        print("\n支持的引擎:")
        for code, name in ENGINES.items():
            print(f"  {code}: {name}")
        return

    # 合并文本参数
    text = parsed.text_arg or (parsed.text if parsed.text else None)
    if text:
        # 简洁模式：直接翻译
        text = ' '.join(text) if isinstance(text, list) else text
        try:
            translator = TranslatorEngine(parsed.engine)
            result = translator.translate(text, parsed.source, parsed.target)
            print(result)
        except Exception as e:
            print(f"翻译失败: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 默认模式：启动 TUI（浮窗模式）
        app = IAmTransFloatApp()
        if parsed.inline:
            app.run_inline()
        else:
            app.run()


if __name__ == "__main__":
    main()