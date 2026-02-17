"""测试企业微信 API 客户端"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from interface.wechat.wecom_client import WeChatWorkClient


@pytest.fixture
def wecom_client():
    """创建测试用的企业微信客户端"""
    return WeChatWorkClient(
        corp_id="test_corp_id",
        secret="test_secret",
        agent_id="test_agent_id"
    )


@pytest.fixture
def mock_response():
    """创建模拟的响应对象"""
    mock = Mock()
    mock.raise_for_status = Mock()
    return mock


class TestWeChatWorkClient:
    """企业微信客户端测试"""
    
    def test_init(self, wecom_client):
        """测试初始化"""
        assert wecom_client.corp_id == "test_corp_id"
        assert wecom_client.secret == "test_secret"
        assert wecom_client.agent_id == "test_agent_id"
        assert wecom_client.access_token is None
        assert wecom_client.token_expires_at == 0
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_access_token_success(self, mock_get, wecom_client, mock_response):
        """测试获取 access token 成功"""
        mock_response.json.return_value = {
            "errcode": 0,
            "access_token": "test_token",
            "expires_in": 7200
        }
        mock_get.return_value = mock_response
        
        token = wecom_client._get_access_token()
        
        assert token == "test_token"
        assert wecom_client.access_token == "test_token"
        assert wecom_client.token_expires_at > 0
        mock_get.assert_called_once()
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_access_token_cached(self, mock_get, wecom_client):
        """测试 access token 缓存"""
        import time
        wecom_client.access_token = "cached_token"
        wecom_client.token_expires_at = time.time() + 3600
        
        token = wecom_client._get_access_token()
        
        assert token == "cached_token"
        mock_get.assert_not_called()
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_access_token_failure(self, mock_get, wecom_client, mock_response):
        """测试获取 access token 失败"""
        mock_response.json.return_value = {
            "errcode": 40013,
            "errmsg": "invalid corpid"
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            wecom_client._get_access_token()
        
        assert "invalid corpid" in str(exc_info.value)
    
    def test_get_bot_id(self, wecom_client):
        """测试获取机器人 ID"""
        bot_id = wecom_client.get_bot_id()
        assert bot_id == "test_agent_id"
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_list_app_chats_success(self, mock_get, wecom_client, mock_response):
        """测试获取群聊列表成功"""
        mock_response.json.return_value = {
            "errcode": 0,
            "chatlist": [
                {"chatid": "chat1", "name": "测试群1"},
                {"chatid": "chat2", "name": "测试群2"}
            ],
            "next_cursor": "cursor123"
        }
        mock_get.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            result = wecom_client.list_app_chats(limit=100, cursor="")
        
        assert len(result["chatlist"]) == 2
        assert result["next_cursor"] == "cursor123"
        assert result["chatlist"][0]["chatid"] == "chat1"
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_list_app_chats_failure(self, mock_get, wecom_client, mock_response):
        """测试获取群聊列表失败"""
        mock_response.json.return_value = {
            "errcode": 60011,
            "errmsg": "no privilege"
        }
        mock_get.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            result = wecom_client.list_app_chats()
        
        assert result["chatlist"] == []
        assert result["next_cursor"] == ""
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_all_app_chats(self, mock_get, wecom_client, mock_response):
        """测试获取所有群聊（分页）"""
        # 模拟两次请求：第一次有 next_cursor，第二次没有
        responses = [
            {
                "errcode": 0,
                "chatlist": [{"chatid": "chat1"}],
                "next_cursor": "cursor1"
            },
            {
                "errcode": 0,
                "chatlist": [{"chatid": "chat2"}],
                "next_cursor": ""
            }
        ]
        mock_response.json.side_effect = responses
        mock_get.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            result = wecom_client.get_all_app_chats()
        
        assert len(result) == 2
        assert result[0]["chatid"] == "chat1"
        assert result[1]["chatid"] == "chat2"
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_chat_info_success(self, mock_get, wecom_client, mock_response):
        """测试获取群聊信息成功"""
        mock_response.json.return_value = {
            "errcode": 0,
            "chat_info": {
                "chatid": "chat1",
                "name": "测试群",
                "owner": "user1",
                "userlist": ["user1", "user2", "user3"]
            }
        }
        mock_get.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            info = wecom_client.get_chat_info("chat1")
        
        assert info["chatid"] == "chat1"
        assert info["name"] == "测试群"
        assert len(info["userlist"]) == 3
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_chat_members(self, mock_get, wecom_client, mock_response):
        """测试获取群成员"""
        mock_response.json.return_value = {
            "errcode": 0,
            "chat_info": {
                "userlist": ["user1", "user2", "user3"]
            }
        }
        mock_get.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            members = wecom_client.get_chat_members("chat1")
        
        assert len(members) == 3
        assert "user1" in members
    
    @patch('interface.wechat.wecom_client.requests.post')
    def test_send_group_message_success(self, mock_post, wecom_client, mock_response):
        """测试发送群消息成功"""
        mock_response.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            wecom_client.send_group_message("chat1", "测试消息")
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["chatid"] == "chat1"
        assert call_args[1]["json"]["text"]["content"] == "测试消息"
    
    @patch('interface.wechat.wecom_client.requests.post')
    def test_send_group_message_failure(self, mock_post, wecom_client, mock_response):
        """测试发送群消息失败"""
        mock_response.json.return_value = {
            "errcode": 60020,
            "errmsg": "chatid not found"
        }
        mock_post.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            with pytest.raises(Exception) as exc_info:
                wecom_client.send_group_message("chat1", "测试消息")
        
        assert "chatid not found" in str(exc_info.value)
    
    @patch('interface.wechat.wecom_client.requests.post')
    def test_send_text_message(self, mock_post, wecom_client, mock_response):
        """测试发送文本消息给用户"""
        mock_response.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            wecom_client.send_text_message("user1", "测试消息")
        
        call_args = mock_post.call_args
        assert call_args[1]["json"]["touser"] == "user1"
        assert call_args[1]["json"]["text"]["content"] == "测试消息"
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_user_info(self, mock_get, wecom_client, mock_response):
        """测试获取用户信息"""
        mock_response.json.return_value = {
            "errcode": 0,
            "userid": "user1",
            "name": "张三",
            "department": [1],
            "position": "工程师",
            "mobile": "13800138000",
            "email": "zhangsan@company.com"
        }
        mock_get.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            info = wecom_client.get_user_info("user1")
        
        assert info["userid"] == "user1"
        assert info["name"] == "张三"
        assert info["position"] == "工程师"
    
    @patch('interface.wechat.wecom_client.requests.get')
    def test_get_department_users(self, mock_get, wecom_client, mock_response):
        """测试获取部门成员"""
        mock_response.json.return_value = {
            "errcode": 0,
            "userlist": [
                {"userid": "user1", "name": "张三"},
                {"userid": "user2", "name": "李四"}
            ]
        }
        mock_get.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            users = wecom_client.get_department_users(1, fetch_child=True)
        
        assert len(users) == 2
        assert users[0]["userid"] == "user1"
    
    @patch('interface.wechat.wecom_client.requests.post')
    def test_create_app_chat(self, mock_post, wecom_client, mock_response):
        """测试创建群聊"""
        mock_response.json.return_value = {
            "errcode": 0,
            "chatid": "new_chat"
        }
        mock_post.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            chat_id = wecom_client.create_app_chat(
                name="新群聊",
                owner="user1",
                userlist=["user1", "user2"]
            )
        
        assert chat_id == "new_chat"
    
    @patch('interface.wechat.wecom_client.requests.post')
    def test_update_app_chat(self, mock_post, wecom_client, mock_response):
        """测试修改群聊"""
        mock_response.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            success = wecom_client.update_app_chat(
                chat_id="chat1",
                name="新名称",
                add_user_list=["user3"]
            )
        
        assert success is True
    
    @patch('interface.wechat.wecom_client.requests.post')
    def test_send_markdown_message(self, mock_post, wecom_client, mock_response):
        """测试发送 Markdown 消息"""
        mock_response.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_response
        
        with patch.object(wecom_client, '_get_access_token', return_value="test_token"):
            wecom_client.send_markdown_message("chat1", "# 标题\n内容")
        
        call_args = mock_post.call_args
        assert call_args[1]["json"]["msgtype"] == "markdown"
    
    def test_close(self, wecom_client):
        """测试关闭客户端"""
        wecom_client.access_token = "test_token"
        wecom_client.close()
        assert wecom_client.access_token is None

