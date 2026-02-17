"""接口管理器 - 统一管理多个用户接口"""
from typing import Dict, List, Optional

from loguru import logger

from interface.base import Interface


class InterfaceManager:
    """接口管理器
    
    统一管理多个用户接口（微信、Web等），提供统一的启动、停止和消息处理接口
    """
    
    def __init__(self):
        self.interfaces: Dict[str, Interface] = {}
    
    def register(self, interface: Interface):
        """注册接口
        
        Args:
            interface: 接口实例
        """
        name = interface.get_name()
        if name in self.interfaces:
            logger.warning(f"Interface {name} already registered, replacing...")
        self.interfaces[name] = interface
        logger.info(f"Interface {name} registered")
    
    def unregister(self, name: str):
        """注销接口
        
        Args:
            name: 接口名称
        """
        if name in self.interfaces:
            interface = self.interfaces[name]
            if interface.is_running():
                interface.stop()
            del self.interfaces[name]
            logger.info(f"Interface {name} unregistered")
    
    def get_interface(self, name: str) -> Optional[Interface]:
        """获取接口
        
        Args:
            name: 接口名称
            
        Returns:
            接口实例，如果不存在返回 None
        """
        return self.interfaces.get(name)
    
    def start_all(self):
        """启动所有已注册的接口"""
        for name, interface in self.interfaces.items():
            try:
                interface.start()
                logger.info(f"Interface {name} started")
            except Exception as e:
                logger.error(f"Failed to start interface {name}: {e}")
    
    def stop_all(self):
        """停止所有已注册的接口"""
        for name, interface in self.interfaces.items():
            try:
                if interface.is_running():
                    interface.stop()
                    logger.info(f"Interface {name} stopped")
            except Exception as e:
                logger.error(f"Failed to stop interface {name}: {e}")
    
    def start(self, name: str):
        """启动指定接口
        
        Args:
            name: 接口名称
        """
        interface = self.get_interface(name)
        if interface:
            interface.start()
        else:
            logger.warning(f"Interface {name} not found")
    
    def stop(self, name: str):
        """停止指定接口
        
        Args:
            name: 接口名称
        """
        interface = self.get_interface(name)
        if interface:
            interface.stop()
        else:
            logger.warning(f"Interface {name} not found")
    
    def list_interfaces(self) -> List[str]:
        """列出所有已注册的接口名称"""
        return list(self.interfaces.keys())
    
    def get_running_interfaces(self) -> List[str]:
        """获取所有正在运行的接口名称"""
        return [name for name, interface in self.interfaces.items() if interface.is_running()]

