# PyPI 首次发布指南

**问题**：首次发布到 PyPI，无法使用 GitHub Trusted Publishing（OIDC）。必须本地先上传一次，才能在 PyPI 上"认领"项目。

本文档详解首次发布流程 + 后续 CI/CD 自动化配置。

---

## 两种认证方式对比

| 方式 | 首次发布 | 后续发布 | 安全性 |
|------|----------|----------|--------|
| **API Token**（传统） | ✅ 可用 | ✅ 可用 | 中（Token 泄露风险） |
| **Trusted Publishing**（OIDC） | ❌ 需先认领项目 | ✅ 最佳 | 高（无需 Token） |

**Trusted Publishing 原理**：PyPI 验证 GitHub OIDC token → 确认 repo 身份 → 允许发布。但前提是项目名称已存在且你拥有权限。

---

## 首次发布流程（本地）

### Step 1：注册 PyPI 账号

1. 登录 https://pypi.org/account/signup/
2. 验证邮箱
3. 完成 2FA（推荐：TOTP authenticator）

### Step 2：创建 API Token

**首次必须用全局 Token**：

1. 登录 PyPI → Account settings → API tokens
2. 点击 **"Add API token"**
3. Scope 选择 **"Entire account (all projects)"** ← 关键！首次发布无法选择特定项目
4. Token name：`first-publish`
5. 点击 "Create token"
6. **立即保存 Token**（格式：`pypi-xxxx...`），只显示一次

```
⚠️ 这个 Token 权限很大（可发布你账号下所有项目）
⚠️ 首次发布后建议删除，换成项目专属 Token
```

### Step 3：本地打包

```bash
# 安装构建工具
pip install build twine

# 清理旧构建
rm -rf build/ dist/ *.egg-info

# 构建 wheel + sdist
python -m build

# 检查结果
ls dist/
# → ttrans-1.0.0-py3-none-any.whl
# → ttrans-1.0.0.tar.gz
```

### Step 4：验证包

```bash
# 检查包有效性
twine check dist/*

# 检查内容（可选）
tar -tzf dist/ttrans-1.0.0.tar.gz
```

### Step 5：上传到 PyPI

```bash
# 方式一：直接上传（Token 写在命令里）
twine upload dist/* --username __token__ --password pypi-xxxx...

# 方式二：使用环境变量（更安全）
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxx...
twine upload dist/*
```

**输出**：

```
Uploading ttrans-1.0.0-py3-none-any.whl 100%
Uploading ttrans-1.0.0.tar.gz 100%

View at:
https://pypi.org/project/TTrans/1.0.0/
```

### Step 6：验证发布成功

```bash
# 尝试安装
pip install TTrans

# 或直接访问
https://pypi.org/project/TTrans/
```

---

## 后续配置：项目专属 Token

首次发布后，项目已存在于 PyPI。现在可以创建项目专属 Token：

1. PyPI → Account settings → API tokens
2. Scope 选择 **"Project: TTrans"** ← 现在能选了
3. 创建 Token：`pypi-yyyy...`
4. **删除首次的全局 Token**（安全最佳实践）

---

## 配置 GitHub CI/CD

### 方案一：API Token（传统）

**设置 GitHub Secret**：

1. GitHub repo → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. Name：`PYPI_TOKEN`
4. Value：`pypi-yyyy...`（项目专属 Token）
5. 点击 "Add secret"

**CI 配置**：

```yaml
- name: Upload to PyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
  run: twine upload dist/*
```

### 方案二：Trusted Publishing（推荐）

**原理**：GitHub → OIDC token → PyPI 验证 → 允许发布。无需存储 API Token。

**配置步骤**：

1. **PyPI 设置**：
   - 登录 PyPI → Account settings → Publishing
   - 点击 "Add a new pending publisher"
   -填写：
     - PyPI Project Name：`TTrans`
     - Owner：`thierrycao`（GitHub 用户名）
     - Repository name：`TTrans`
     - Workflow name：`release.yml`
     - Environment name：`pypi`（可选，但推荐）
   - 点击 "Add"

2. **GitHub 设置**：
   - GitHub repo → Settings → Environments
   - 创建 environment：`pypi`
   - （可选）添加 protection rules：Required reviewers

3. **CI 配置**：

```yaml
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi  # 对应 PyPI 设置的 environment
    permissions:
      id-token: write  # 允许获取 OIDC token
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install build
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # 无需 TWINE_PASSWORD，OIDC 自动认证
```

---

## 流程对比

### 首次发布（必须本地）

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PyPI 注册账号 + 2FA                                      │
│ 2. 创建全局 API Token（Scope: Entire account）              │
│ 3. 本地打包：python -m build                                │
│ 4. 本地上传：twine upload --username __token__              │
│ 5. 验证：pip install TTrans                                 │
│ 6. 删除全局 Token，创建项目专属 Token                        │
│ 7. 设置 GitHub Secret: PYPI_TOKEN                           │
���─────────────────────────────────────────────────────────────┘
```

### 后续发布（CI/CD 自动）

```
┌─────────────────────────────────────────────────────────────┐
│ git push → tag v1.0.1                                       │
│     ↓                                                       │
│ GitHub Actions 触发                                         │
│     ↓                                                       │
│ python -m build → twine upload                              │
│     ↓                                                       │
│ PyPI 更新：https://pypi.org/project/TTrans/                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 常见问题

### Q：为什么首次无法用 Trusted Publishing？

**答**：PyPI 的 Trusted Publishing 要求项目名称已存在。首次发布时项目不存在 → 无法设置 publisher → 必须先本地上传一次 → 项目创建后才能配置 OIDC。

### Q：全局 Token ��全吗？

**答**：不安全。权限是"所有项目"。做法：
- 首次发布后立即删除
- 创建项目专属 Token
- 或直接配置 Trusted Publishing（最安全）

### Q：项目名被占用怎么办？

**答**：
- 检查 https://pypi.org/project/<name>/ 是否存在
- 如果存在且不是你的，只能改名（如 `ttrans-cli`）
- 如果是你的但丢失了权限，联系 PyPI support

### Q：上传失败：403 Forbidden？

**答**：
- Token 权限不足：首次必须用全局 Token
- Token 过期或无效：重新生成
- 项目名被占用且你不是 owner：改名

### Q：twine check 报错？

**答**：
- 检查 `pyproject.toml` 是否符合 PEP 621
- 检查 `license` 字段格式（应为 `"MIT"`，非 `{text = "MIT"}`）
- 检查 `version` 格式（应为 `X.Y.Z`）

---

## 本项目实际流程

### 首次发布 TTrans

```bash
# 1. 创建全局 Token
# PyPI → API tokens → Scope: Entire account

# 2. 本地打包
cd ~/workshop/abc/project/edu/2.tools/2.ai/eftools/ttrans
./scripts/build_local.sh

# 3. 上传
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxx...
twine upload dist/*

# 4. 验证
pip install TTrans
ttrans Hello
# → 你好

# 5. 配置后续自动化
# PyPI → Publishing → Add pending publisher (GitHub OIDC)
# 或 GitHub Secret: PYPI_TOKEN
```

### 后续发布

```bash
# 方式一：本地脚本
./scripts/release.sh 1.0.1

# 方式二：GitHub 自动
git tag v1.0.1
git push origin v1.0.1
# → Actions 自动发布到 PyPI
```

---

## 安全最佳实践

| 实践 | 原因 |
|------|------|
| 首次发布后删除全局 Token | 防止泄露影响所有项目 |
| 使用项目专属 Token | 限制泄露影响范围 |
| 优先使用 Trusted Publishing | 无需存储 Token，OIDC 自动认证 |
| GitHub Environment + Required reviewers | 防止恶意 PR 触发发布 |
| 定期轮换 Token | 降低长期泄露风险 |

---

## 参考资料

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [PEP 621: pyproject.toml metadata](https://peps.python.org/pep-0621/)
- [gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [Twine documentation](https://twine.readthedocs.io/)