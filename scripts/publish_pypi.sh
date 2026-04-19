#!/bin/bash
# PyPI 发布脚本
# 使用: ./scripts/publish_pypi.sh [test|prod]
# test: 发布到 TestPyPI (测试)
# prod: 发布到 PyPI (正式)
#
# 配置方式：
# 1. ~/.pypirc 文件（推荐）- twine 自动读取
# 2. 环境变量 PYPI_TOKEN / TEST_PYPI_TOKEN

set -e

MODE=${1:-test}

echo "=== iamtrans PyPI 发布 ==="
echo "发布模式: $MODE"

# 进入项目根目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# 检查是否有 dist 文件
if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
    echo "没有 dist 文件，请先运行 ./scripts/build_local.sh"
    exit 1
fi

# 检查配置方式
PYPIRC_FILE="$HOME/.pypirc"
HAS_PYPIRC=false

if [ -f "$PYPIRC_FILE" ]; then
    # 检查 ~/.pypirc 是否包含对应仓库配置
    if [ "$MODE" == "prod" ]; then
        if grep -q "\[pypi\]" "$PYPIRC_FILE" 2>/dev/null; then
            HAS_PYPIRC=true
            echo "使用 ~/.pypirc 配置 (pypi)"
        fi
    else
        if grep -q "\[testpypi\]" "$PYPIRC_FILE" 2>/dev/null; then
            HAS_PYPIRC=true
            echo "使用 ~/.pypirc 配置 (testpypi)"
        fi
    fi
fi

# 如果没有 ~/.pypirc，检查环境变量
if [ "$HAS_PYPIRC" = false ]; then
    if [ "$MODE" == "prod" ]; then
        if [ -z "$PYPI_TOKEN" ]; then
            echo ""
            echo "未配置 PyPI 认证，请选择以下方式之一："
            echo ""
            echo "方式一：创建 ~/.pypirc 文件"
            echo "  cat > ~/.pypirc << 'EOF'"
            echo "  [distutils]"
            echo "  index-servers ="
            echo "      pypi"
            echo "      testpypi"
            echo ""
            echo "  [pypi]"
            echo "  repository = https://upload.pypi.org/legacy/"
            echo "  username = __token__"
            echo "  password = pypi-xxx..."
            echo ""
            echo "  [testpypi]"
            echo "  repository = https://test.pypi.org/legacy/"
            echo "  username = __token__"
            echo "  password = pypi-xxx..."
            echo "  EOF"
            echo ""
            echo "方式二：设置环境变量"
            echo "  export PYPI_TOKEN='your-pypi-token'"
            echo ""
            echo "获取 Token: https://pypi.org/manage/account/token/"
            exit 1
        fi
        echo "使用环境变量 PYPI_TOKEN"
    else
        if [ -z "$TEST_PYPI_TOKEN" ]; then
            echo ""
            echo "未配置 TestPyPI 认证"
            echo "请在 ~/.pypirc 中添加 [testpypi] 配置"
            echo "或设置: export TEST_PYPI_TOKEN='your-token'"
            exit 1
        fi
        echo "使用环境变量 TEST_PYPI_TOKEN"
    fi
fi

# 安装 twine
echo ""
echo "安装 twine..."
pip install --upgrade twine

# 检查包
echo ""
echo "=== 检查包有效性 ==="
twine check dist/*.whl dist/*.tar.gz

# 发布
echo ""
echo "=== 发布到 $MODE ==="

if [ "$HAS_PYPIRC" = true ]; then
    # 使用 ~/.pypirc 配置
    if [ "$MODE" == "prod" ]; then
        twine upload dist/*.whl dist/*.tar.gz --repository pypi
    else
        twine upload dist/*.whl dist/*.tar.gz --repository testpypi
    fi
else
    # 使用环境变量
    if [ "$MODE" == "prod" ]; then
        TWINE_USERNAME=__token__
        TWINE_PASSWORD=$PYPI_TOKEN
        twine upload dist/*.whl dist/*.tar.gz
    else
        TWINE_USERNAME=__token__
        TWINE_PASSWORD=$TEST_PYPI_TOKEN
        twine upload dist/*.whl dist/*.tar.gz --repository-url https://test.pypi.org/legacy/
    fi
fi

echo ""
echo "发布完成！"
echo ""
if [ "$MODE" == "prod" ]; then
    echo "安装: pip install iamtrans"
    echo "主页: https://pypi.org/project/iamtrans/"
else
    echo "测试安装: pip install --index-url https://test.pypi.org/simple/ iamtrans"
    echo "主页: https://test.pypi.org/project/iamtrans/"
fi