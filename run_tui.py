#!/usr/bin/env python3
"""iamtrans - 开发入口"""
import sys
import os

# 添加源码目录到路径
_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if _src not in sys.path:
    sys.path.insert(0, _src)

from iamtrans.main import main

if __name__ == "__main__":
    main()