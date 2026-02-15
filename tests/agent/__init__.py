"""Agent 模块测试套件。

本测试套件提供了对 agent 模块的全面测试，包括：
- FunctionRegistry: 函数注册表测试
- ToolExecutor: 工具执行器测试
- Discovery: 函数自动发现和注册测试
- Agent: Agent 核心类测试
- Providers: LLM 提供商测试（支持 mock 和真实 API）

测试支持：
- Mock 测试：使用 mock 对象模拟 LLM 响应
- 真实 API 测试：可以通过环境变量配置 API Key 和模型类型进行真实测试
"""
