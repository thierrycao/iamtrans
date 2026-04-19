#!/bin/bash
# 一键发布脚本 - 打包 + 发布到 GitHub + PyPI
# 使用: ./scripts/release.sh [version]

set -e

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

NEW_VERSION=${1:-}

echo "=== iamtrans 一键发布 ==="

# 获取当前版本
CURRENT=$(grep 'version = ' pyproject.toml | head -1 | sed 's/version = "//' | sed 's/"//')
echo "当前版本: $CURRENT"

# 如果提供了新版本，先更新
if [ -n "$NEW_VERSION" ]; then
    echo "更新版本到 $NEW_VERSION..."
    ./scripts/version.sh set "$NEW_VERSION"
fi

# 确认发布
VERSION=$(grep 'version = ' pyproject.toml | head -1 | sed 's/version = "//' | sed 's/"//')
echo ""
echo "即将发布版本: $VERSION"
echo ""
echo "步骤:"
echo "  1. 本地打包 (wheel + sdist)"
echo "  2. 创建 Git tag"
echo "  3. 推送到 GitHub (触发 CI/CD)"
echo "  4. GitHub 自动发布到 PyPI"
echo ""
read -p "确认发布? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "取消发布"
    exit 0
fi

# 1. 本地打包
echo ""
echo "=== Step 1: 本地打包 ==="
./scripts/build_local.sh

# 2. 创建 Git commit 和 tag
echo ""
echo "=== Step 2: Git 操作 ==="
git status
if [ -n "$(git status --porcelain)" ]; then
    echo "提交更改..."
    git add -A
    git commit -m "Release v$VERSION"
fi

echo "创建 tag..."
git tag -a "v$VERSION" -m "iamtrans v$VERSION"

# 3. 推送到 GitHub
echo ""
echo "=== Step 3: 推送 GitHub ==="
git push origin main
git push origin "v$VERSION"

echo ""
echo "✅ 发布流程完成！"
echo ""
echo "GitHub Actions 将自动执行:"
echo "  - PyPI 发布"
echo "  - Linux/macOS/Windows 二进制构建"
echo "  - GitHub Release 创建"
echo ""
echo "查看进度: https://github.com/thierrycao/iamtrans/actions"
echo ""
echo "发布后:"
echo "  - PyPI: https://pypi.org/project/iamtrans/"
echo "  - GitHub: https://github.com/thierrycao/iamtrans/releases"