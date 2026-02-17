"""企业微信 API 客户端 - 完整版


提供企业微信机器人的完整功能：
- 消息收发（文本、图片、文件等多种类型）
- 群聊管理（创建、修改、查询）
- 用户管理（查询用户信息、部门信息）
- 通讯录管理
"""
import hashlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from loguru import logger


class WeChatWorkClient:
    """企业微信 API 客户端
    
    提供企业微信机器人的核心功能：
    - 获取群聊列表和群聊信息
    - 获取群聊成员信息
    - 发送各种类型的消息（文本、图片、文件等）
    - 接收消息回调
    - 用户和部门管理
    """
    
    def __init__(self, corp_id: str, secret: str, agent_id: str):
        """
        Args:
            corp_id: 企业 ID
            secret: 应用密钥
            agent_id: 应用 ID
        """
        self.corp_id = corp_id
        self.secret = secret
        self.agent_id = agent_id
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.base_url = "https://qyapi.weixin.qq.com"
        logger.info(f"WeChat Work client initialized with agent_id: {agent_id}")
    
    def _get_access_token(self) -> str:
        """获取 access_token"""
        # 如果 token 未过期，直接返回
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # 获取新 token
        url = f"{self.base_url}/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                self.access_token = data.get("access_token")
                # token 有效期 7200 秒，提前 5 分钟刷新
                self.token_expires_at = time.time() + 7200 - 300
                logger.info("WeChat Work access token obtained")
                return self.access_token
            else:
                raise Exception(f"Failed to get access token: {data.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise
    
    def get_bot_id(self) -> str:
        """获取机器人 ID（使用 agent_id）"""
        return self.agent_id
    
    def list_app_chats(self, limit: int = 100, cursor: str = "") -> Dict[str, Any]:
        """获取应用会话列表
        
        Args:
            limit: 每次拉取的数据量，最大1000
            cursor: 用于分页查询的游标，字符串类型，由上一次调用返回
            
        Returns:
            包含群聊列表的字典:
            {
                "chatlist": [{"chatid": "xxx", "name": "群聊名称"}],
                "next_cursor": "下次分页的游标"
            }
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/list"
        params = {
            "access_token": access_token,
            "limit": min(limit, 1000)
        }
        if cursor:
            params["cursor"] = cursor
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                return {
                    "chatlist": result.get("chatlist", []),
                    "next_cursor": result.get("next_cursor", "")
                }
            else:
                logger.error(f"Failed to list app chats: {result.get('errmsg')}")
                return {"chatlist": [], "next_cursor": ""}
                
        except Exception as e:
            logger.error(f"Error listing app chats: {e}")
            return {"chatlist": [], "next_cursor": ""}
    
    def get_all_app_chats(self) -> List[Dict[str, Any]]:
        """获取所有应用会话（自动分页）
        
        Returns:
            所有群聊列表: [{"chatid": "xxx", "name": "群聊名称"}, ...]
        """
        all_chats = []
        cursor = ""
        
        while True:
            result = self.list_app_chats(limit=100, cursor=cursor)
            chatlist = result.get("chatlist", [])
            all_chats.extend(chatlist)
            
            cursor = result.get("next_cursor", "")
            if not cursor:
                break
        
        logger.info(f"Found {len(all_chats)} app chats")
        return all_chats
    
    def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """获取群聊信息
        
        Args:
            chat_id: 群聊 ID (chatid)
            
        Returns:
            群聊信息字典，包含 name, owner, userlist 等
            
        Raises:
            Exception: 获取失败时抛出异常
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/get"
        params = {
            "access_token": access_token,
            "chatid": chat_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                return result.get("chat_info", {})
            else:
                raise Exception(f"Failed to get chat info: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error getting chat info: {e}")
            raise
    
    def get_chat_members(self, chat_id: str) -> List[str]:
        """获取群聊成员列表
        
        Args:
            chat_id: 群聊 ID
            
        Returns:
            成员 userid 列表
        """
        try:
            chat_info = self.get_chat_info(chat_id)
            return chat_info.get("userlist", [])
        except Exception as e:
            logger.error(f"Error getting chat members: {e}")
            return []
    
    def get_chat_list(self, chat_ids: List[str]) -> List[Dict[str, Any]]:
        """批量获取群聊信息
        
        Args:
            chat_ids: 群聊 ID 列表
            
        Returns:
            群聊信息列表，每个元素包含 chatid, name, owner, userlist 等
        """
        chat_list = []
        for chat_id in chat_ids:
            try:
                chat_info = self.get_chat_info(chat_id)
                chat_info["chatid"] = chat_id  # 确保包含 chatid
                chat_list.append(chat_info)
            except Exception as e:
                logger.warning(f"Failed to get info for chat {chat_id}: {e}")
                # 即使获取失败，也添加基本信息
                chat_list.append({
                    "chatid": chat_id,
                    "name": f"未知群聊 ({chat_id})",
                    "error": str(e)
                })
        
        return chat_list
    
    def send_group_message(self, chat_id: str, content: str):
        """发送群消息
        
        Args:
            chat_id: 群聊 ID（企业微信中为 chatid）
            content: 消息内容
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/send"
        params = {"access_token": access_token}
        
        data = {
            "chatid": chat_id,
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"Message sent to group {chat_id}")
            else:
                logger.error(f"Failed to send message: {result.get('errmsg')}")
                raise Exception(f"Send message failed: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def send_text_message(self, user_id: str, content: str):
        """发送文本消息给用户
        
        Args:
            user_id: 用户 ID
            content: 消息内容
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/message/send"
        params = {"access_token": access_token}
        
        data = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {
                "content": content
            }
        }
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"Message sent to user {user_id}")
            else:
                logger.error(f"Failed to send message: {result.get('errmsg')}")
                raise Exception(f"Send message failed: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户信息字典，包含 name, department, mobile, email 等
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/user/get"
        params = {
            "access_token": access_token,
            "userid": user_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                return {
                    "userid": result.get("userid"),
                    "name": result.get("name"),
                    "department": result.get("department", []),
                    "position": result.get("position", ""),
                    "mobile": result.get("mobile", ""),
                    "email": result.get("email", ""),
                    "avatar": result.get("avatar", ""),
                    "status": result.get("status", 1)
                }
            else:
                logger.error(f"Failed to get user info: {result.get('errmsg')}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {}
    
    def get_department_users(self, department_id: int, fetch_child: bool = False) -> List[Dict[str, Any]]:
        """获取部门成员列表
        
        Args:
            department_id: 部门 ID
            fetch_child: 是否递归获取子部门成员
            
        Returns:
            部门成员列表
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/user/simplelist"
        params = {
            "access_token": access_token,
            "department_id": department_id,
            "fetch_child": 1 if fetch_child else 0
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                return result.get("userlist", [])
            else:
                logger.error(f"Failed to get department users: {result.get('errmsg')}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting department users: {e}")
            return []
    
    def create_app_chat(self, name: str, owner: str, userlist: List[str], 
                        chat_id: Optional[str] = None) -> str:
        """创建群聊
        
        Args:
            name: 群聊名称
            owner: 群主 userid
            userlist: 群成员 userid 列表（2-2000人）
            chat_id: 群聊 ID（可选，不指定则自动生成）
            
        Returns:
            创建的群聊 ID
            
        Raises:
            Exception: 创建失败时抛出异常
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/create"
        params = {"access_token": access_token}
        
        data = {
            "name": name,
            "owner": owner,
            "userlist": userlist
        }
        if chat_id:
            data["chatid"] = chat_id
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                created_chatid = result.get("chatid", "")
                logger.info(f"App chat created: {created_chatid}")
                return created_chatid
            else:
                raise Exception(f"Failed to create app chat: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error creating app chat: {e}")
            raise
    
    def update_app_chat(self, chat_id: str, name: Optional[str] = None, 
                        owner: Optional[str] = None, add_user_list: Optional[List[str]] = None,
                        del_user_list: Optional[List[str]] = None) -> bool:
        """修改群聊信息
        
        Args:
            chat_id: 群聊 ID
            name: 新的群聊名称（可选）
            owner: 新的群主 userid（可选）
            add_user_list: 要添加的成员 userid 列表（可选）
            del_user_list: 要删除的成员 userid 列表（可选）
            
        Returns:
            是否修改成功
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/update"
        params = {"access_token": access_token}
        
        data = {"chatid": chat_id}
        if name:
            data["name"] = name
        if owner:
            data["owner"] = owner
        if add_user_list:
            data["add_user_list"] = add_user_list
        if del_user_list:
            data["del_user_list"] = del_user_list
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"App chat {chat_id} updated")
                return True
            else:
                logger.error(f"Failed to update app chat: {result.get('errmsg')}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating app chat: {e}")
            return False
    
    def send_markdown_message(self, chat_id: str, content: str):
        """发送 Markdown 格式消息到群聊
        
        Args:
            chat_id: 群聊 ID
            content: Markdown 格式的消息内容
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/send"
        params = {"access_token": access_token}
        
        data = {
            "chatid": chat_id,
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"Markdown message sent to group {chat_id}")
            else:
                logger.error(f"Failed to send markdown message: {result.get('errmsg')}")
                raise Exception(f"Send message failed: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error sending markdown message: {e}")
            raise
    
    def send_image_message(self, chat_id: str, media_id: str):
        """发送图片消息到群聊
        
        Args:
            chat_id: 群聊 ID
            media_id: 图片的 media_id（通过上传接口获得）
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/send"
        params = {"access_token": access_token}
        
        data = {
            "chatid": chat_id,
            "msgtype": "image",
            "image": {
                "media_id": media_id
            }
        }
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"Image message sent to group {chat_id}")
            else:
                logger.error(f"Failed to send image message: {result.get('errmsg')}")
                raise Exception(f"Send message failed: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error sending image message: {e}")
            raise
    
    def send_file_message(self, chat_id: str, media_id: str):
        """发送文件消息到群聊
        
        Args:
            chat_id: 群聊 ID
            media_id: 文件的 media_id（通过上传接口获得）
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/appchat/send"
        params = {"access_token": access_token}
        
        data = {
            "chatid": chat_id,
            "msgtype": "file",
            "file": {
                "media_id": media_id
            }
        }
        
        try:
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"File message sent to group {chat_id}")
            else:
                logger.error(f"Failed to send file message: {result.get('errmsg')}")
                raise Exception(f"Send message failed: {result.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"Error sending file message: {e}")
            raise
    
    def upload_temp_media(self, file_path: str, media_type: str = "file") -> str:
        """上传临时素材
        
        Args:
            file_path: 文件路径
            media_type: 媒体类型，可选值：image/voice/video/file
            
        Returns:
            media_id
            
        Raises:
            Exception: 上传失败时抛出异常
        """
        access_token = self._get_access_token()
        url = f"{self.base_url}/cgi-bin/media/upload"
        params = {
            "access_token": access_token,
            "type": media_type
        }
        
        try:
            with open(file_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, params=params, files=files, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                if result.get("errcode") == 0 or "media_id" in result:
                    media_id = result.get("media_id", "")
                    logger.info(f"Media uploaded: {media_id}")
                    return media_id
                else:
                    raise Exception(f"Failed to upload media: {result.get('errmsg')}")
                    
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            raise
    
    def close(self):
        """关闭客户端"""
        self.access_token = None
        logger.info("WeChat Work client closed")

