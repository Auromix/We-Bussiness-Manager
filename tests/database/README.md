# Database Tests

本目录测试 `database/` 模块（Repository + Facade）当前实现，重点覆盖：

- `DatabaseManager` 门面能力（保存、查询、汇总、插件）
- 三类仓库方法（实体仓库、业务仓库、系统仓库）
- 模型约束和关系（含 `PluginData` 唯一约束）
- 两个业务场景（美发店、健身房）

## 目录说明

- `conftest.py`: 独立临时 SQLite fixture
- `test_database_initialization.py`: 初始化与连接能力
- `test_models.py`: ORM 模型与关系
- `test_repository_methods.py`: 核心仓库方法
- `test_repository_comprehensive.py`: 跨仓库组合能力
- `test_edge_cases.py`: 边界与容错
- `test_hair_salon_scenario.py`: 美发店流程
- `test_gym_scenario.py`: 健身房流程

## 运行

```bash
python -m pytest tests/database -q
```

若根目录 `tests/conftest.py` 引入了与数据库测试无关的依赖，可使用：

```bash
python -m pytest --confcutdir=tests/database tests/database -q
```
