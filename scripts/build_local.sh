#!/bin/bash
# 本地打包脚本 - 生成 wheel 和 sdist
# 使用: ./scripts/build_local.sh

set -e

echo "=== iamtrans 本地打包 ==="

# 进入项目根目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "项目目录: $PROJECT_ROOT"

# 清理旧构建
echo "清理旧构建文件..."
rm -rf build/ dist/ *.egg-info src/*.egg-info

# 安装构建工具
echo "安装构建工具..."
pip install --upgrade build twine

# 构建 wheel 和 sdist
echo "构建 wheel 和 sdist..."
python -m build

# 检查构建结果
echo ""
echo "=== 构建结果 ==="
ls -lh dist/

# 检查包有效性
echo ""
echo "=== 检查包有效性 ==="
twine check dist/*.whl dist/*.tar.gz

echo ""
echo "✅ 打包完成！"
echo "文件位置: $PROJECT_ROOT/dist/"
echo ""
echo "下一步："
echo "  - 发布到 PyPI: ./scripts/publish_pypi.sh"
echo "  - 本地测试: pip install dist/*.whl"