"""业务命令定义 - 项目特定的命令配置

所有业务相关的命令定义都在这里，interface 层只负责命令分发
"""
from typing import Dict, Any


# 命令注册表 - 定义所有可用的命令
COMMANDS: Dict[str, Dict[str, Any]] = {
    # ---- 查询类 ----
    "今日总结": {
        "handler": "daily_summary",
        "args": 0,
        "desc": "生成今日经营数据汇总",
        "business_method": "generate_summary",
        "business_params": {"summary_type": "daily"}
    },
    "库存总结": {
        "handler": "inventory_summary",
        "args": 0,
        "desc": "显示当前库存情况",
        "business_method": "generate_summary",
        "business_params": {"summary_type": "inventory"}
    },
    "会员总结": {
        "handler": "membership_summary",
        "args": 0,
        "desc": "显示会员充值/余额汇总",
        "business_method": "generate_summary",
        "business_params": {"summary_type": "membership"}
    },
    "本月总结": {
        "handler": "monthly_summary",
        "args": 0,
        "desc": "生成本月经营报表",
        "business_method": "generate_summary",
        "business_params": {"summary_type": "monthly"}
    },
    "查询": {
        "handler": "query_records",
        "args": "*",
        "desc": "查询XX老师/查询1月28日",
        "business_method": "query_records"
    },
    
    # ---- 操作类 ----
    "确认": {
        "handler": "confirm_records",
        "args": 0,
        "desc": "确认今日所有待确认记录",
        "business_method": "confirm_records"
    },
    "撤销": {
        "handler": "undo_last",
        "args": "?",
        "desc": "撤销上一条/撤销指定记录",
        "business_method": "undo_last"
    },
    "修改": {
        "handler": "modify_record",
        "args": "*",
        "desc": "修改 #记录ID 金额为XX",
        "business_method": "modify_record"
    },
    
    # ---- 库存管理 ----
    "入库": {
        "handler": "restock",
        "args": "*",
        "desc": "入库 泡脚液 100瓶",
        "business_method": "handle_command",
        "business_params": {"command": "restock"}
    },
    "库存调整": {
        "handler": "adjust_inventory",
        "args": "*",
        "desc": "手动调整库存",
        "business_method": "handle_command",
        "business_params": {"command": "adjust_inventory"}
    },
    
    # ---- 帮助 ----
    "帮助": {
        "handler": "show_help",
        "args": 0,
        "desc": "显示所有可用命令",
        "business_method": None  # 特殊处理，不需要调用业务方法
    },
}


def get_command_config(command: str) -> Dict[str, Any]:
    """获取命令配置"""
    return COMMANDS.get(command, {})


def get_all_commands() -> Dict[str, Dict[str, Any]]:
    """获取所有命令"""
    return COMMANDS.copy()


def get_help_text() -> str:
    """生成帮助文本"""
    help_text = "📖 可用命令：\n\n"
    for cmd, config in COMMANDS.items():
        help_text += f"• {cmd}: {config['desc']}\n"
    return help_text

