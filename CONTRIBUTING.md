# Contributing Guide | 贡献指南

[English](#english) | [中文](#中文)

---

## English

Thank you for your interest in **BizBot**! We welcome all forms of contributions — bug reports, feature requests, documentation improvements, and code contributions.

### Getting Started

1. **Fork & Clone**

```bash
git clone https://github.com/<your-username>/bizbot.git
cd bizbot
```

2. **Create a Virtual Environment**

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
```

3. **Install in Development Mode**

```bash
pip install -e ".[all,dev]"
```

This installs the package in editable mode with all optional dependencies (web, scheduler) and development tools (pytest, black, isort, mypy).

4. **Set Up Environment**

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

5. **Verify Installation**

```bash
pytest tests/ -v
```

### Making Changes

1. **Create a Branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

2. **Code Style**

We follow [PEP 8](https://peps.python.org/pep-0008/) with a line length of 100 characters.

```bash
# Format code
black .
isort .

# Type checking (optional)
mypy agent/ database/
```

3. **Write Tests**

- New features should include test cases.
- Tests go in the `tests/` directory, mirroring the source structure.
- Run tests with:

```bash
pytest tests/ -v
pytest tests/database/ -v    # Run specific module tests
pytest tests/agent/ -v
```

4. **Commit Messages**

Follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix     | Description          |
|------------|----------------------|
| `feat:`    | New feature          |
| `fix:`     | Bug fix              |
| `docs:`    | Documentation update |
| `style:`   | Code formatting      |
| `refactor:`| Code refactoring     |
| `test:`    | Test-related changes |
| `chore:`   | Build/tooling        |

```bash
git add .
git commit -m "feat: add membership expiry notification"
```

5. **Push & Create Pull Request**

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

### Pull Request Checklist

- [ ] Code follows the project style guide
- [ ] Self-reviewed the code
- [ ] Added/updated tests as needed
- [ ] All tests pass locally
- [ ] Updated documentation if applicable

### Reporting Issues

Before creating an issue:
1. Check if a similar issue already exists
2. Provide clear reproduction steps
3. Include environment info (Python version, OS, etc.)

---

## 中文

感谢您对 **BizBot** 项目的关注！我们欢迎所有形式的贡献——Bug 报告、功能建议、文档改进和代码贡献。

### 快速开始

1. **Fork & 克隆**

```bash
git clone https://github.com/<your-username>/bizbot.git
cd bizbot
```

2. **创建虚拟环境**

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
```

3. **以开发模式安装**

```bash
pip install -e ".[all,dev]"
```

这会以可编辑模式安装包，包含所有可选依赖（web、scheduler）和开发工具（pytest、black、isort、mypy）。

4. **配置环境**

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

5. **验证安装**

```bash
pytest tests/ -v
```

### 开发流程

1. **创建分支**

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

2. **代码规范**

遵循 [PEP 8](https://peps.python.org/pep-0008/) 代码风格，行长度不超过 100 字符。

```bash
# 格式化代码
black .
isort .

# 类型检查（可选）
mypy agent/ database/
```

3. **编写测试**

- 新功能需要包含相应的测试用例
- 测试文件放在 `tests/` 目录中
- 运行测试：

```bash
pytest tests/ -v
pytest tests/database/ -v    # 运行特定模块测试
pytest tests/agent/ -v
```

4. **提交信息**

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

| 前缀       | 说明           |
|------------|----------------|
| `feat:`    | 新功能         |
| `fix:`     | 修复 Bug       |
| `docs:`    | 文档更新       |
| `style:`   | 代码格式调整   |
| `refactor:`| 代码重构       |
| `test:`    | 测试相关       |
| `chore:`   | 构建/工具相关  |

```bash
git add .
git commit -m "feat: 添加会员到期提醒功能"
```

5. **推送并创建 Pull Request**

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

### PR 检查清单

- [ ] 代码遵循项目代码风格
- [ ] 已进行自我代码审查
- [ ] 已添加/更新相关测试
- [ ] 本地所有测试通过
- [ ] 如有需要，已更新文档

### 报告问题

提交 Issue 之前，请：
1. 检查是否已有类似的 Issue
2. 提供清晰的问题描述和复现步骤
3. 包含相关的环境信息（Python 版本、操作系统等）

---

## Getting Help | 获取帮助

- 📖 Read the [documentation](https://github.com/Auromix/bizbot#readme)
- 💬 Open a [GitHub Discussion](https://github.com/Auromix/bizbot/discussions)
- 🐛 Report a [Bug](https://github.com/Auromix/bizbot/issues/new?template=bug_report.md)
- 💡 Request a [Feature](https://github.com/Auromix/bizbot/issues/new?template=feature_request.md)

Thank you for contributing! 🎉 感谢您的贡献！
