"""测试接口抽象基类"""
import pytest
from typing import Any, Dict, Optional
from unittest.mock import Mock

from interface.base import Interface


class ConcreteInterface(Interface):
    """具体接口实现用于测试"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.start_called = False
        self.stop_called = False
        self.handle_message_called = False
        self.send_message_called = False
    
    def start(self):
        """启动接口"""
        self.start_called = True
        self.running = True
    
    def stop(self):
        """停止接口"""
        self.stop_called = True
        self.running = False
    
    async def handle_message(self, raw_msg: Dict[str, Any]) -> Optional[str]:
        """处理接收到的消息"""
        self.handle_message_called = True
        return "test response"
    
    def send_message(self, target: str, content: str):
        """发送消息"""
        self.send_message_called = True


class TestInterface:
    """接口抽象基类测试"""
    
    def test_init(self):
        """测试初始化"""
        interface = ConcreteInterface("test")
        assert interface.name == "test"
        assert not interface.running
    
    def test_get_name(self):
        """测试获取接口名称"""
        interface = ConcreteInterface("test_interface")
        assert interface.get_name() == "test_interface"
    
    def test_is_running(self):
        """测试检查运行状态"""
        interface = ConcreteInterface("test")
        assert not interface.is_running()
        
        interface.running = True
        assert interface.is_running()
    
    def test_start(self):
        """测试启动接口"""
        interface = ConcreteInterface("test")
        interface.start()
        assert interface.start_called
        assert interface.is_running()
    
    def test_stop(self):
        """测试停止接口"""
        interface = ConcreteInterface("test")
        interface.running = True
        interface.stop()
        assert interface.stop_called
        assert not interface.is_running()
    
    @pytest.mark.asyncio
    async def test_handle_message(self):
        """测试处理消息"""
        interface = ConcreteInterface("test")
        raw_msg = {"content": "test message"}
        response = await interface.handle_message(raw_msg)
        
        assert interface.handle_message_called
        assert response == "test response"
    
    def test_send_message(self):
        """测试发送消息"""
        interface = ConcreteInterface("test")
        interface.send_message("target", "content")
        
        assert interface.send_message_called

