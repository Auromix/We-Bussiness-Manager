"""接口抽象基类 - 定义统一的接口协议"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Interface(ABC):
    """接口抽象基类
    
    所有用户接口（微信、Web等）都应该实现这个接口
    这样可以统一管理多个接口，并且易于扩展
    """
    
    def __init__(self, name: str):
        """
        Args:
            name: 接口名称（如 'wechat', 'web'）
        """
        self.name = name
        self.running = False
    
    @abstractmethod
    def start(self):
        """启动接口"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止接口"""
        pass
    
    @abstractmethod
    async def handle_message(self, raw_msg: Dict[str, Any]) -> Optional[str]:
        """处理接收到的消息
        
        Args:
            raw_msg: 原始消息字典，格式由具体接口定义
            
        Returns:
            如果需要回复，返回回复内容；否则返回 None
        """
        pass
    
    @abstractmethod
    def send_message(self, target: str, content: str):
        """发送消息
        
        Args:
            target: 目标标识（如群ID、用户ID等）
            content: 消息内容
        """
        pass
    
    def is_running(self) -> bool:
        """检查接口是否正在运行"""
        return self.running
    
    def get_name(self) -> str:
        """获取接口名称"""
        return self.name

