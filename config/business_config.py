"""
业务配置接口 - 支持可替换的业务配置

用户可以通过修改此文件来自定义自己的业态。
默认业态为理疗馆（健康养生馆）。

自定义方法：
1. 修改 TherapyStoreConfig 中的配置项
2. 或者创建新的 BusinessConfig 子类并替换 business_config 实例
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BusinessConfig(ABC):
    """业务配置抽象基类

    所有业态都应该实现此接口，提供业务相关的配置信息。
    """

    @abstractmethod
    def get_business_name(self) -> str:
        """获取业态名称（如"理疗馆"、"美发店"、"健身房"）"""
        pass

    @abstractmethod
    def get_business_description(self) -> str:
        """获取业态描述"""
        pass

    @abstractmethod
    def get_service_types(self) -> List[Dict[str, Any]]:
        """获取服务类型列表

        Returns:
            [{"name": "推拿按摩", "default_price": 198.0, "category": "therapy"}, ...]
        """
        pass

    @abstractmethod
    def get_products(self) -> List[Dict[str, Any]]:
        """获取产品列表

        Returns:
            [{"name": "艾条", "category": "consumable", "unit_price": 68.0}, ...]
        """
        pass

    @abstractmethod
    def get_staff_roles(self) -> List[Dict[str, Any]]:
        """获取员工角色配置

        Returns:
            [{"title": "高级技师", "commission_rate": 40.0}, ...]
        """
        pass

    @abstractmethod
    def get_default_staff(self) -> List[Dict[str, Any]]:
        """获取默认员工列表

        Returns:
            [{"name": "张师傅", "role": "manager", "commission_rate": 40.0}, ...]
        """
        pass

    @abstractmethod
    def get_membership_types(self) -> List[Dict[str, Any]]:
        """获取会员卡类型

        Returns:
            [{"name": "年卡", "days": 365, "points_per_yuan": 0.1}, ...]
        """
        pass

    @abstractmethod
    def get_channels(self) -> List[Dict[str, Any]]:
        """获取引流渠道列表

        Returns:
            [{"name": "美团", "type": "platform", "commission_rate": 15.0}, ...]
        """
        pass

    @abstractmethod
    def get_llm_system_prompt(self) -> str:
        """获取 LLM 系统提示词"""
        pass

    @abstractmethod
    def get_noise_patterns(self) -> List[str]:
        """获取噪声消息模式"""
        pass

    @abstractmethod
    def get_service_keywords(self) -> List[str]:
        """获取服务关键词"""
        pass

    @abstractmethod
    def get_product_keywords(self) -> List[str]:
        """获取商品关键词"""
        pass

    @abstractmethod
    def get_membership_keywords(self) -> List[str]:
        """获取会员关键词"""
        pass


class TherapyStoreConfig(BusinessConfig):
    """理疗馆（健康养生馆）业务配置

    这是默认的业态配置。用户可以直接修改此类中的配置项来自定义自己的理疗馆。

    自定义示例：
        # 修改服务类型和价格
        修改 get_service_types() 中的列表

        # 修改员工和提成
        修改 get_default_staff() 中的列表

        # 修改产品
        修改 get_products() 中的列表

    如果你经营的不是理疗馆，可以参考此类创建自己的业态配置类，
    然后在文件底部替换 business_config 实例。
    """

    # ============================================================
    # 🔧 用户可自定义区域 - 修改以下配置来定制你的理疗馆
    # ============================================================

    # 店铺名称
    STORE_NAME = "理疗馆"

    # 服务类型及默认价格
    SERVICE_TYPES = [
        {"name": "推拿按摩", "default_price": 198.0, "category": "massage"},
        {"name": "艾灸理疗", "default_price": 168.0, "category": "moxibustion"},
        {"name": "拔罐刮痧", "default_price": 128.0, "category": "cupping"},
        {"name": "足疗", "default_price": 138.0, "category": "foot_therapy"},
        {"name": "头疗", "default_price": 158.0, "category": "head_therapy"},
        {"name": "肩颈调理", "default_price": 188.0, "category": "shoulder_neck"},
        {"name": "全身精油SPA", "default_price": 298.0, "category": "spa"},
        {"name": "中药熏蒸", "default_price": 238.0, "category": "herbal_steam"},
    ]

    # 产品及价格
    PRODUCTS = [
        {"name": "艾条（盒）", "category": "consumable", "unit_price": 68.0},
        {"name": "精油（瓶）", "category": "consumable", "unit_price": 128.0},
        {"name": "刮痧板", "category": "tool", "unit_price": 88.0},
        {"name": "热敷包", "category": "tool", "unit_price": 58.0},
        {"name": "养生茶（盒）", "category": "consumable", "unit_price": 98.0},
        {"name": "颈椎枕", "category": "tool", "unit_price": 168.0},
        {"name": "足浴粉（袋）", "category": "consumable", "unit_price": 38.0},
    ]

    # 员工角色配置
    STAFF_ROLES = [
        {"title": "高级技师", "commission_rate": 40.0, "description": "经验丰富，技术精湛"},
        {"title": "普通技师", "commission_rate": 30.0, "description": "正式技师"},
        {"title": "实习技师", "commission_rate": 20.0, "description": "实习期技师"},
        {"title": "前台", "commission_rate": 0, "description": "前台接待"},
        {"title": "管理员", "commission_rate": 0, "description": "店铺管理"},
    ]

    # 默认员工列表
    DEFAULT_STAFF = [
        {"name": "张师傅", "role": "manager", "commission_rate": 40.0},
        {"name": "李师傅", "role": "staff", "commission_rate": 40.0},
        {"name": "王技师", "role": "staff", "commission_rate": 30.0},
        {"name": "赵技师", "role": "staff", "commission_rate": 30.0},
        {"name": "前台小刘", "role": "staff", "commission_rate": 0},
    ]

    # 会员卡类型
    MEMBERSHIP_TYPES = [
        {"name": "年卡", "days": 365, "points_per_yuan": 0.1},
        {"name": "季卡", "days": 90, "points_per_yuan": 0.1},
        {"name": "月卡", "days": 30, "points_per_yuan": 0.1},
        {"name": "次卡", "days": 365, "points_per_yuan": 0.1},
        {"name": "疗程卡", "days": 180, "points_per_yuan": 0.1},
        {"name": "储值卡", "days": 365, "points_per_yuan": 0.1},
    ]

    # 引流渠道
    CHANNELS = [
        {"name": "美团", "type": "platform", "commission_rate": 15.0},
        {"name": "大众点评", "type": "platform", "commission_rate": 12.0},
        {"name": "朋友推荐", "type": "external", "commission_rate": 10.0},
        {"name": "抖音", "type": "platform", "commission_rate": 18.0},
    ]

    # ============================================================
    # 以下为接口实现，通常不需要修改
    # ============================================================

    def get_business_name(self) -> str:
        return self.STORE_NAME

    def get_business_description(self) -> str:
        return (
            f"这是一家{self.STORE_NAME}（健康养生馆），"
            f"提供推拿按摩、艾灸理疗、拔罐刮痧、足疗、头疗、肩颈调理等养生保健服务，"
            f"同时销售艾条、精油、刮痧板等养生产品。"
        )

    def get_service_types(self) -> List[Dict[str, Any]]:
        return self.SERVICE_TYPES

    def get_products(self) -> List[Dict[str, Any]]:
        return self.PRODUCTS

    def get_staff_roles(self) -> List[Dict[str, Any]]:
        return self.STAFF_ROLES

    def get_default_staff(self) -> List[Dict[str, Any]]:
        return self.DEFAULT_STAFF

    def get_membership_types(self) -> List[Dict[str, Any]]:
        return self.MEMBERSHIP_TYPES

    def get_channels(self) -> List[Dict[str, Any]]:
        return self.CHANNELS

    def get_noise_patterns(self) -> List[str]:
        return [
            r'^接$', r'^好$', r'^运$',
            r'^\[.*表情\]',
            r'^(好的|收到|谢谢|嗯|哦)',
            r'停在|掉头|车子',
            r'@\S+\s*(好的|收到)',
        ]

    def get_service_keywords(self) -> List[str]:
        return [st["name"] for st in self.SERVICE_TYPES]

    def get_product_keywords(self) -> List[str]:
        return [p["name"] for p in self.PRODUCTS]

    def get_membership_keywords(self) -> List[str]:
        return ['开卡', '充值', '会员'] + [mt["name"] for mt in self.MEMBERSHIP_TYPES]

    def get_llm_system_prompt(self) -> str:
        """生成 LLM 系统提示词

        根据配置动态生成，确保提示词与实际业务配置一致。
        """
        # 构建服务类型列表
        service_list = "、".join(
            f"{st['name']}({st['default_price']}元)"
            for st in self.SERVICE_TYPES
        )

        # 构建产品列表
        product_list = "、".join(
            f"{p['name']}({p['unit_price']}元)"
            for p in self.PRODUCTS
        )

        # 构建员工信息
        staff_info = "\n".join(
            f"  - {s['name']}：{'管理员' if s['role'] == 'manager' else '技师'}，提成率{s['commission_rate']}%"
            for s in self.DEFAULT_STAFF
            if s.get("commission_rate", 0) > 0
        )

        # 构建会员卡信息
        membership_info = "、".join(
            f"{mt['name']}({mt['days']}天)"
            for mt in self.MEMBERSHIP_TYPES
        )

        return f"""你是一家{self.STORE_NAME}（健康养生馆）的智能管理助手。你帮助店铺老板/管理者通过自然语言对话处理日常经营事务。

## 你的核心能力

你可以通过调用工具函数来操作数据库，完成以下任务：

### 1. 📋 服务记录管理
- **记录服务收入**：顾客到店消费时，记录服务类型、金额、技师等信息
- **修改服务记录**：修正金额、日期等错误信息
- **删除服务记录**：删除错误录入的记录
- 可用服务类型：{service_list}

### 2. 👥 会员管理
- **开通会员卡**：为顾客办理会员卡（{membership_info}）
- **查询会员信息**：查看顾客的会员卡余额、有效期、积分
- **扣减余额**：会员消费时扣减卡内余额
- **到期提醒**：查看即将到期的会员卡

### 3. 🛒 产品销售
- **记录销售**：记录产品/商品的销售
- **管理库存**：查看库存、入库、出库
- 可用产品：{product_list}

### 4. 👨‍💼 员工管理
- **查看员工**：列出所有在职员工和提成率
- **添加/修改/停用员工**：管理员工信息
- 当前员工及提成：
{staff_info}

### 5. 📊 数据统计
- **日收入统计**：查看某天的服务收入、产品收入、提成、净收入
- **日期范围统计**：查看一段时间的经营数据
- **技师提成统计**：查看技师的服务次数和提成金额
- **顾客消费历史**：查看某位顾客的消费记录

### 6. ⚙️ 业务配置
- **服务类型管理**：添加、修改服务类型和价格
- **产品管理**：添加新产品、修改价格
- **渠道管理**：管理引流渠道
- **业务概览**：查看店铺整体经营概况

## 重要规则

### 操作确认机制
对于**写入操作**（记录收入、开会员卡、删除记录等），你需要：
1. 先向用户确认操作详情（金额、顾客、服务类型等）
2. 用户确认后再执行操作
3. 如果用户说"帮我记一下"、"记录"等，可以理解为用户已确认意图，直接执行

### 数据准确性
- 认真理解用户的自然语言，准确提取关键信息
- 如果信息不完整，主动询问缺少的关键信息（如金额、顾客姓名等）
- 金额必须准确，不能猜测

### 回复风格
- 用中文简洁回复，包含关键数字
- 操作成功后给出清晰的确认信息
- 查询结果用结构化方式展示
- 如果一句话包含多个操作，依次处理

### 智能理解
- "陈阿姨做了推拿，张师傅做的，198元" → 记录服务
- "王女士办年卡3000" → 开通会员卡
- "赵先生买了两盒艾条" → 记录产品销售
- "今天收入多少" → 查询日统计
- "帮我加一个新技师小孙，提成30%" → 添加员工
- "把刚才那笔198的改成168" → 修改记录
"""


# ============================================================
# 全局业务配置实例
# ============================================================
# 如果你需要更换业态（如美发店、健身房），可以：
# 1. 创建新的 BusinessConfig 子类
# 2. 替换下面的实例
#
# 例如：
#   class HairSalonConfig(BusinessConfig):
#       ...
#   business_config = HairSalonConfig()
# ============================================================

business_config: BusinessConfig = TherapyStoreConfig()
