# 已修复的问题

## 1. 数据库会话嵌套问题 ✅

**问题**：在 `save_service_record`、`save_product_sale` 等方法中，已经有一个数据库会话，但调用的 `get_or_create_customer`、`get_or_create_employee` 等方法又创建了新的会话，导致会话嵌套问题。

**修复**：
- 修改所有 `get_or_create_*` 方法，添加可选的 `session` 参数
- 当传入 `session` 时，使用传入的会话；否则创建新会话
- 使用 `session.flush()` 而不是 `session.commit()`，让外层会话控制提交
- 更新所有调用这些方法的地方，传入当前会话

## 2. LLM Parser API Key 验证 ✅

**问题**：在 `create_llm_parser` 中，如果配置了 `primary_llm` 但对应的 API Key 为 None，会直接创建解析器导致运行时错误。

**修复**：
- 在创建解析器前检查 API Key 是否存在
- 如果不存在，抛出明确的错误信息
- 对于 fallback，如果 API Key 不存在，记录警告并跳过

## 3. Asyncio 事件循环问题 ✅

**问题**：在 `bot.py` 的 `_message_loop` 中，使用 `asyncio.run()` 在已有事件循环的线程中可能有问题。

**修复**：
- 在新线程中创建独立的事件循环
- 使用 `asyncio.new_event_loop()` 和 `asyncio.set_event_loop()`
- 使用 `loop.run_until_complete()` 而不是 `asyncio.run()`

## 4. Scheduler 事件循环问题 ✅

**问题**：`AsyncIOScheduler` 需要运行在事件循环中，但主程序是同步的。

**修复**：
- 在 `Scheduler.__init__` 中获取或创建事件循环
- 将事件循环传递给 `AsyncIOScheduler`
- 在模拟模式下，运行事件循环以支持 scheduler

## 5. 数据库路径问题 ✅

**问题**：`sqlite:///data/store.db` 需要确保 `data` 目录存在。

**修复**：
- 在 `main.py` 中，在初始化数据库前创建必要的目录
- 使用 `os.makedirs(..., exist_ok=True)` 确保目录存在

## 6. 其他改进

- 改进了错误处理和日志记录
- 确保所有数据库操作在正确的会话中进行
- 优化了事件循环的管理

## 待测试的功能

1. 完整的消息处理流程（从接收到入库）
2. LLM 解析器的 fallback 机制
3. 定时任务的执行
4. 命令处理系统
5. 数据库操作的并发安全性

## 已知限制

1. WeChatFerry 需要 Windows 环境，在 Linux 上会自动切换到模拟模式
2. 某些功能（如确认、撤销、修改记录）标记为"开发中"，需要后续实现
3. 库存管理和会员管理的部分功能需要完善

