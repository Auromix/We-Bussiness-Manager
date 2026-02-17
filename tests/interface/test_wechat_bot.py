"""测试企业微信机器人"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from interface.wechat.bot import WeChatBot
from interface.wechat.message_router import WeChatMessageRouter


@pytest.fixture
def mock_router():
    """创建模拟的消息路由器"""
    router = Mock(spec=WeChatMessageRouter)
    router.route = AsyncMock(return_value=("test response", True))
    return router


@pytest.fixture
def wechat_bot(mock_router):
    """创建测试用的微信机器人"""
    return WeChatBot(mock_router, enable_callback=False)


@pytest.fixture
def mock_client():
    """创建模拟的企业微信客户端"""
    client = Mock()
    client.get_bot_id.return_value = "test_bot_id"
    client.get_all_app_chats.return_value = [
        {"chatid": "chat1", "name": "测试群1"},
        {"chatid": "chat2", "name": "测试群2"}
    ]
    client.get_chat_info.return_value = {
        "chatid": "chat1",
        "name": "测试群1",
        "owner": "user1",
        "userlist": ["user1", "user2"]
    }
    client.get_chat_members.return_value = ["user1", "user2"]
    client.send_group_message = Mock()
    client.send_text_message = Mock()
    client.create_app_chat.return_value = "new_chat_id"
    client.update_app_chat.return_value = True
    client.get_user_info.return_value = {
        "userid": "user1",
        "name": "张三",
        "department": [1]
    }
    client.get_department_users.return_value = [
        {"userid": "user1", "name": "张三"}
    ]
    client.upload_temp_media.return_value = "test_media_id"
    client.send_image_message = Mock()
    client.send_file_message = Mock()
    client.send_markdown_message = Mock()
    client.close = Mock()
    return client


class TestWeChatBot:
    """微信机器人测试"""
    
    def test_init(self, mock_router):
        """测试初始化"""
        bot = WeChatBot(mock_router, enable_callback=False)
        assert bot.name == "wechat"
        assert bot.router == mock_router
        assert bot.client is None
        assert not bot.running
    
    @patch('interface.wechat.bot.WeChatWorkClient')
    @patch('interface.wechat.bot.settings')
    def test_start_without_callback(self, mock_settings, mock_client_class, mock_router):
        """测试启动机器人（不启用回调）"""
        mock_settings.wechat_work_corp_id = "corp_id"
        mock_settings.wechat_work_secret = "secret"
        mock_settings.wechat_work_agent_id = "agent_id"
        mock_settings.wechat_work_token = None
        
        mock_client = Mock()
        mock_client.get_bot_id.return_value = "bot_id"
        mock_client_class.return_value = mock_client
        
        bot = WeChatBot(mock_router, enable_callback=False)
        bot.start()
        
        assert bot.running
        assert bot.bot_wxid == "bot_id"
        mock_client_class.assert_called_once()
    
    def test_get_all_groups(self, wechat_bot, mock_client):
        """测试获取所有群聊"""
        wechat_bot.client = mock_client
        
        groups = wechat_bot.get_all_groups()
        
        assert len(groups) == 2
        assert groups[0]["chatid"] == "chat1"
        mock_client.get_all_app_chats.assert_called_once()
    
    def test_get_all_groups_no_client(self, wechat_bot):
        """测试获取所有群聊（客户端未初始化）"""
        groups = wechat_bot.get_all_groups()
        assert groups == []
    
    def test_get_group_info(self, wechat_bot, mock_client):
        """测试获取群聊信息"""
        wechat_bot.client = mock_client
        
        info = wechat_bot.get_group_info("chat1")
        
        assert info["chatid"] == "chat1"
        assert info["name"] == "测试群1"
        mock_client.get_chat_info.assert_called_once_with("chat1")
    
    def test_get_group_members(self, wechat_bot, mock_client):
        """测试获取群成员"""
        wechat_bot.client = mock_client
        
        members = wechat_bot.get_group_members("chat1")
        
        assert len(members) == 2
        assert "user1" in members
        mock_client.get_chat_members.assert_called_once_with("chat1")
    
    @pytest.mark.asyncio
    async def test_handle_message(self, wechat_bot, mock_router):
        """测试处理消息"""
        wechat_bot.running = True
        
        raw_msg = {
            "wechat_msg_id": "msg123",
            "sender_nickname": "测试用户",
            "sender_wechat_id": "user1",
            "content": "测试消息",
            "msg_type": "text",
            "group_id": "chat1",
            "timestamp": datetime.now(),
            "is_at_bot": True
        }
        
        response = await wechat_bot.handle_message(raw_msg)
        
        assert response == "test response"
        mock_router.route.assert_called_once_with(raw_msg)
    
    @pytest.mark.asyncio
    async def test_handle_message_filtered_by_target_group(self, wechat_bot, mock_router):
        """测试处理消息（非目标群）"""
        wechat_bot.running = True
        wechat_bot.target_group_ids = {"chat2"}
        
        raw_msg = {
            "group_id": "chat1",  # 不在目标群列表中
            "content": "测试消息",
            "is_at_bot": True
        }
        
        response = await wechat_bot.handle_message(raw_msg)
        
        assert response is None
        mock_router.route.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_no_response(self, wechat_bot, mock_router):
        """测试处理消息（不需要回复）"""
        wechat_bot.running = True
        mock_router.route = AsyncMock(return_value=("", False))
        
        raw_msg = {
            "group_id": "chat1",
            "content": "测试消息",
            "is_at_bot": False
        }
        
        response = await wechat_bot.handle_message(raw_msg)
        
        assert response is None
    
    def test_send_message(self, wechat_bot, mock_client):
        """测试发送消息"""
        wechat_bot.client = mock_client
        
        wechat_bot.send_message("chat1", "测试消息")
        
        mock_client.send_group_message.assert_called_once_with("chat1", "测试消息")
    
    def test_send_user_message(self, wechat_bot, mock_client):
        """测试发送私聊消息"""
        wechat_bot.client = mock_client
        
        wechat_bot.send_user_message("user1", "测试消息")
        
        mock_client.send_text_message.assert_called_once_with("user1", "测试消息")
    
    def test_send_markdown_message(self, wechat_bot, mock_client):
        """测试发送 Markdown 消息"""
        wechat_bot.client = mock_client
        
        wechat_bot.send_markdown_message("chat1", "# 标题")
        
        mock_client.send_markdown_message.assert_called_once_with("chat1", "# 标题")
    
    def test_send_image(self, wechat_bot, mock_client):
        """测试发送图片"""
        wechat_bot.client = mock_client
        
        wechat_bot.send_image("chat1", "/path/to/image.jpg")
        
        mock_client.upload_temp_media.assert_called_once_with("/path/to/image.jpg", "image")
        mock_client.send_image_message.assert_called_once_with("chat1", "test_media_id")
    
    def test_send_file(self, wechat_bot, mock_client):
        """测试发送文件"""
        wechat_bot.client = mock_client
        
        wechat_bot.send_file("chat1", "/path/to/file.pdf")
        
        mock_client.upload_temp_media.assert_called_once_with("/path/to/file.pdf", "file")
        mock_client.send_file_message.assert_called_once_with("chat1", "test_media_id")
    
    def test_create_group(self, wechat_bot, mock_client):
        """测试创建群聊"""
        wechat_bot.client = mock_client
        
        chat_id = wechat_bot.create_group(
            name="新群聊",
            owner="user1",
            members=["user1", "user2"]
        )
        
        assert chat_id == "new_chat_id"
        mock_client.create_app_chat.assert_called_once()
    
    def test_update_group(self, wechat_bot, mock_client):
        """测试修改群聊"""
        wechat_bot.client = mock_client
        
        success = wechat_bot.update_group(
            chat_id="chat1",
            name="新名称",
            add_members=["user3"]
        )
        
        assert success is True
        mock_client.update_app_chat.assert_called_once()
    
    def test_get_user_info(self, wechat_bot, mock_client):
        """测试获取用户信息"""
        wechat_bot.client = mock_client
        
        info = wechat_bot.get_user_info("user1")
        
        assert info["userid"] == "user1"
        assert info["name"] == "张三"
        mock_client.get_user_info.assert_called_once_with("user1")
    
    def test_get_department_users(self, wechat_bot, mock_client):
        """测试获取部门成员"""
        wechat_bot.client = mock_client
        
        users = wechat_bot.get_department_users(1, fetch_child=True)
        
        assert len(users) == 1
        assert users[0]["userid"] == "user1"
        mock_client.get_department_users.assert_called_once_with(1, True)
    
    def test_stop(self, wechat_bot, mock_client):
        """测试停止机器人"""
        wechat_bot.client = mock_client
        wechat_bot.running = True
        
        wechat_bot.stop()
        
        assert not wechat_bot.running
        mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_convert_wecom_message(self, wechat_bot):
        """测试转换企业微信消息格式"""
        msg_dict = {
            "MsgId": "123456",
            "FromUserName": "user1",
            "Content": "测试消息 @机器人",
            "MsgType": "text",
            "ChatId": "chat1",
            "CreateTime": "1609459200"
        }
        
        converted = wechat_bot._convert_wecom_message(msg_dict)
        
        assert converted["wechat_msg_id"] == "123456"
        assert converted["sender_wechat_id"] == "user1"
        assert converted["content"] == "测试消息 @机器人"
        assert converted["msg_type"] == "text"
        assert converted["group_id"] == "chat1"
        assert converted["is_at_bot"] is True
    
    def test_build_text_reply_xml(self, wechat_bot):
        """测试构建文本回复 XML"""
        original_msg = {
            "ToUserName": "app",
            "FromUserName": "user1"
        }
        
        xml = wechat_bot._build_text_reply_xml(original_msg, "测试回复")
        
        assert "<ToUserName><![CDATA[user1]]></ToUserName>" in xml
        assert "<FromUserName><![CDATA[app]]></FromUserName>" in xml
        assert "<Content><![CDATA[测试回复]]></Content>" in xml
        assert "<MsgType><![CDATA[text]]></MsgType>" in xml

