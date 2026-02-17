"""测试接口管理器"""
import pytest
from unittest.mock import Mock, MagicMock

from interface.manager import InterfaceManager
from interface.base import Interface


class MockInterface(Interface):
    """Mock 接口实现"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.start_called = False
        self.stop_called = False
    
    def start(self):
        """启动接口"""
        self.start_called = True
        self.running = True
    
    def stop(self):
        """停止接口"""
        self.stop_called = True
        self.running = False
    
    async def handle_message(self, raw_msg):
        """处理消息"""
        return None
    
    def send_message(self, target: str, content: str):
        """发送消息"""
        pass


class TestInterfaceManager:
    """接口管理器测试"""
    
    def test_init(self):
        """测试初始化"""
        manager = InterfaceManager()
        assert manager.interfaces == {}
    
    def test_register(self):
        """测试注册接口"""
        manager = InterfaceManager()
        interface = MockInterface("test")
        
        manager.register(interface)
        
        assert "test" in manager.interfaces
        assert manager.interfaces["test"] == interface
    
    def test_register_duplicate(self):
        """测试重复注册接口"""
        manager = InterfaceManager()
        interface1 = MockInterface("test")
        interface2 = MockInterface("test")
        
        manager.register(interface1)
        manager.register(interface2)
        
        assert manager.interfaces["test"] == interface2
    
    def test_unregister(self):
        """测试注销接口"""
        manager = InterfaceManager()
        interface = MockInterface("test")
        interface.running = True
        
        manager.register(interface)
        manager.unregister("test")
        
        assert "test" not in manager.interfaces
        assert interface.stop_called
    
    def test_unregister_not_running(self):
        """测试注销未运行的接口"""
        manager = InterfaceManager()
        interface = MockInterface("test")
        interface.running = False
        
        manager.register(interface)
        manager.unregister("test")
        
        assert "test" not in manager.interfaces
        assert not interface.stop_called
    
    def test_get_interface(self):
        """测试获取接口"""
        manager = InterfaceManager()
        interface = MockInterface("test")
        
        manager.register(interface)
        result = manager.get_interface("test")
        
        assert result == interface
    
    def test_get_interface_not_found(self):
        """测试获取不存在的接口"""
        manager = InterfaceManager()
        result = manager.get_interface("nonexistent")
        
        assert result is None
    
    def test_start_all(self):
        """测试启动所有接口"""
        manager = InterfaceManager()
        interface1 = MockInterface("test1")
        interface2 = MockInterface("test2")
        
        manager.register(interface1)
        manager.register(interface2)
        manager.start_all()
        
        assert interface1.start_called
        assert interface2.start_called
        assert interface1.is_running()
        assert interface2.is_running()
    
    def test_start_all_with_exception(self):
        """测试启动所有接口时出现异常"""
        manager = InterfaceManager()
        interface1 = MockInterface("test1")
        interface2 = MockInterface("test2")
        
        # 让 interface2 启动时抛出异常
        def failing_start():
            raise Exception("Start failed")
        
        interface2.start = failing_start
        
        manager.register(interface1)
        manager.register(interface2)
        manager.start_all()
        
        # interface1 应该成功启动
        assert interface1.start_called
        assert interface1.is_running()
    
    def test_stop_all(self):
        """测试停止所有接口"""
        manager = InterfaceManager()
        interface1 = MockInterface("test1")
        interface2 = MockInterface("test2")
        
        interface1.running = True
        interface2.running = True
        
        manager.register(interface1)
        manager.register(interface2)
        manager.stop_all()
        
        assert interface1.stop_called
        assert interface2.stop_called
        assert not interface1.is_running()
        assert not interface2.is_running()
    
    def test_stop_all_not_running(self):
        """测试停止未运行的接口"""
        manager = InterfaceManager()
        interface1 = MockInterface("test1")
        interface2 = MockInterface("test2")
        
        interface1.running = False
        interface2.running = True
        
        manager.register(interface1)
        manager.register(interface2)
        manager.stop_all()
        
        assert not interface1.stop_called
        assert interface2.stop_called
    
    def test_start(self):
        """测试启动指定接口"""
        manager = InterfaceManager()
        interface = MockInterface("test")
        
        manager.register(interface)
        manager.start("test")
        
        assert interface.start_called
        assert interface.is_running()
    
    def test_start_not_found(self):
        """测试启动不存在的接口"""
        manager = InterfaceManager()
        # 不应该抛出异常
        manager.start("nonexistent")
    
    def test_stop(self):
        """测试停止指定接口"""
        manager = InterfaceManager()
        interface = MockInterface("test")
        interface.running = True
        
        manager.register(interface)
        manager.stop("test")
        
        assert interface.stop_called
        assert not interface.is_running()
    
    def test_stop_not_found(self):
        """测试停止不存在的接口"""
        manager = InterfaceManager()
        # 不应该抛出异常
        manager.stop("nonexistent")
    
    def test_list_interfaces(self):
        """测试列出所有接口"""
        manager = InterfaceManager()
        interface1 = MockInterface("test1")
        interface2 = MockInterface("test2")
        
        manager.register(interface1)
        manager.register(interface2)
        
        interfaces = manager.list_interfaces()
        
        assert set(interfaces) == {"test1", "test2"}
    
    def test_get_running_interfaces(self):
        """测试获取正在运行的接口"""
        manager = InterfaceManager()
        interface1 = MockInterface("test1")
        interface2 = MockInterface("test2")
        interface3 = MockInterface("test3")
        
        interface1.running = True
        interface2.running = False
        interface3.running = True
        
        manager.register(interface1)
        manager.register(interface2)
        manager.register(interface3)
        
        running = manager.get_running_interfaces()
        
        assert set(running) == {"test1", "test3"}

