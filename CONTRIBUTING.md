# Contributing to iamtrans

欢迎贡献代码、报告问题、提出建议。

## 开发环境

```bash
# 克隆仓库
git clone https://github.com/thierrycao/iamtrans.git
cd iamtrans

# 安装开发依赖
pip install -e ".[dev]"

# 本地运行
python run_tui.py
```

## 项目结构

```
iamtrans/
├── src/iamtrans/           # 源码
│   ├── main.py           # CLI 入口
│   ├── translator/       # 翻译引擎 + 词典
│   └── ui/               # TUI 界面
├── scripts/              # 打包发布脚本
├── docs/                 # 技术文档
├── .github/workflows/    # CI/CD
└── tests/                # 测试（待添加）
```

## 代码风格

- Python 3.8+ 兼容
- 类型注解（type hints）
- docstring 使用 Google 风格
- 函数名 snake_case，类名 PascalCase

### Docstring 示例

```python
def translate(text: str, source: str = 'auto') -> str:
    """翻译文本

    Args:
        text: 要翻译的文本
        source: 源语言代码，默认 auto 自动检测

    Returns:
        翻译后的文本

    Raises:
        ValueError: 文本为空
        Exception: 网络请求失败
    """
```

## 添加新引擎

1. 在 `engine.py` 的 `ENGINES` 字典添加引擎名
2. 实现 `_translate_<engine>(text, source, target)` 方法
3. 在 `translate()` 方法添加分支调用
4. 更新 `__init__.py` 导出（如有新常量）
5. 更新 README.md 和 CHANGELOG.md

## 添加新词典源

1. 在 `engine.py` 的 `DICTIONARY_SOURCES` 字典添加源名
2. 实现 `_lookup_<source>(word)` 方法，返回 `DictionaryResult`
3. 在 `lookup_dictionary()` 方法添加分支调用
4. 更新文档

## 测试

目前测试覆盖有限，欢迎补充：

```bash
# 运行测试（待实现）
pytest tests/
```

测试重点：
- 语言检测准确性
- 翻译结果解析
- 词典数据结构
- 异步处理流程

## 打包测试

```bash
# 本地打包
./scripts/build_local.sh

# 安装测试
pip install dist/*.whl
iamtrans Hello  # 应输出翻译结果
```

## 提交 PR

1. Fork 仓库
2. 创建分支：`git checkout -b feature/new-engine`
3. 提交改动：`git commit -m 'Add DeepL engine support'`
4. 推送分支：`git push origin feature/new-engine`
5. 创建 Pull Request

**PR 检查清单**：
- [ ] 代码风格一致
- [ ] 添加类型注解
- [ ] 更新 docstring
- [ ] 更新 CHANGELOG.md
- [ ] 本地测试通过

## 报告问题

在 [Issues](https://github.com/thierrycao/iamtrans/issues) 提交：

- 描述问题（预期的行为 vs 实际行为）
- 提供复现步骤
- 附上错误信息或截图
- 说明操作系统和 Python 版本

---

感谢你的贡献！