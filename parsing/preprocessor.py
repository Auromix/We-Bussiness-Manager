"""消息预处理器 - 规则引擎，降低 LLM 调用量"""
import re
from datetime import datetime, date
from typing import Optional
from config.business_config import business_config


class MessagePreProcessor:
    """规则引擎：处理明确模式，降低 LLM 调用量"""
    
    def __init__(self, config=None):
        """
        初始化预处理器
        
        Args:
            config: 业务配置实例，如果为 None 则使用默认配置
        """
        self.config = config or business_config
        
        # 从配置中获取噪声模式
        self.NOISE_PATTERNS = self.config.get_noise_patterns()
        
        # 日期提取（支持多种格式）- 这是通用的，不需要配置
        self.DATE_PATTERNS = [
            # "1月26日" / "1月26号"
            (r'(\d{1,2})月(\d{1,2})[日号]', lambda m: f"{m.group(1)}/{m.group(2)}"),
            # "1.28" / "1.27"
            (r'(\d{1,2})\.(\d{1,2})', lambda m: f"{m.group(1)}/{m.group(2)}"),
            # "1/28" / "1|28" / "2|1" (竖线分隔符)
            (r'(\d{1,2})[/|](\d{1,2})', lambda m: f"{m.group(1)}/{m.group(2)}"),
        ]
        
        # 从配置中获取关键词
        self.SERVICE_KEYWORDS = self.config.get_service_keywords()
        self.PRODUCT_KEYWORDS = self.config.get_product_keywords()
        self.MEMBERSHIP_KEYWORDS = self.config.get_membership_keywords()
    
    def is_noise(self, content: str) -> bool:
        """判断是否为噪声消息"""
        content = content.strip()
        if len(content) <= 2 and not any(c.isdigit() for c in content):
            return True
        return any(re.search(p, content) for p in self.NOISE_PATTERNS)
    
    def extract_date(self, content: str, msg_timestamp: datetime) -> Optional[date]:
        """从消息内容提取业务日期"""
        for pattern, formatter in self.DATE_PATTERNS:
            match = re.search(pattern, content)
            if match:
                try:
                    date_str = formatter(match)
                    month, day = map(int, date_str.split('/'))
                    year = msg_timestamp.year
                    # 处理跨年情况（如果月份是12月，日期是1月，可能是下一年）
                    if month == 12 and msg_timestamp.month == 1:
                        year = msg_timestamp.year - 1
                    elif month == 1 and msg_timestamp.month == 12:
                        year = msg_timestamp.year + 1
                    return date(year, month, day)
                except (ValueError, IndexError):
                    continue
        return None
    
    def classify_intent(self, content: str) -> str:
        """粗分类: service / product / membership / correction / unknown"""
        if any(kw in content for kw in self.MEMBERSHIP_KEYWORDS):
            return 'membership'
        if any(kw in content for kw in self.PRODUCT_KEYWORDS):
            return 'product'
        if '错误' in content or '改' in content or '更正' in content:
            return 'correction'
        if any(kw in content for kw in self.SERVICE_KEYWORDS):
            return 'service'
        if re.search(r'\d+元?', content) and re.search(r'.老师', content):
            return 'service'  # 有金额+老师 -> 大概率是服务记录
        return 'unknown'
    
    def extract_amount(self, content: str) -> Optional[float]:
        """简单提取金额（用于快速判断）"""
        # 匹配数字+元，或单独的数字（可能是金额）
        patterns = [
            r'(\d+(?:\.\d+)?)元',
            r'(\d+(?:\.\d+)?)头疗',
            r'头疗(\d+(?:\.\d+)?)',
            r'理疗(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)理疗',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None

