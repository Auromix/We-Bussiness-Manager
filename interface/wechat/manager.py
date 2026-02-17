"""企业微信群聊和用户管理模块

提供高级的群聊和用户管理功能，包括：
- 群聊管理（创建、修改、查询、统计）
- 用户管理（查询、统计）
- 批量操作
"""
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from interface.wechat.wecom_client import WeChatWorkClient


class WeChatGroupManager:
    """企业微信群聊管理器"""
    
    def __init__(self, client: WeChatWorkClient):
        """
        Args:
            client: 企业微信客户端
        """
        self.client = client
        self._group_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_all_groups(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """获取所有群聊列表
        
        Args:
            refresh: 是否强制刷新缓存
            
        Returns:
            群聊列表
        """
        if not refresh and self._group_cache:
            return list(self._group_cache.values())
        
        try:
            groups = self.client.get_all_app_chats()
            
            # 更新缓存
            self._group_cache = {g['chatid']: g for g in groups}
            
            logger.info(f"Loaded {len(groups)} groups")
            return groups
            
        except Exception as e:
            logger.error(f"Failed to get all groups: {e}")
            return []
    
    def get_group_detail(self, chat_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """获取群聊详细信息
        
        Args:
            chat_id: 群聊 ID
            use_cache: 是否使用缓存
            
        Returns:
            群聊详细信息
        """
        if use_cache and chat_id in self._group_cache:
            return self._group_cache[chat_id]
        
        try:
            info = self.client.get_chat_info(chat_id)
            
            # 更新缓存
            if info:
                self._group_cache[chat_id] = info
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get group detail: {e}")
            return {}
    
    def search_groups(self, keyword: str, refresh: bool = False) -> List[Dict[str, Any]]:
        """搜索群聊
        
        Args:
            keyword: 搜索关键词（匹配群名）
            refresh: 是否刷新缓存
            
        Returns:
            匹配的群聊列表
        """
        groups = self.get_all_groups(refresh=refresh)
        
        if not keyword:
            return groups
        
        keyword_lower = keyword.lower()
        matched = [
            g for g in groups 
            if keyword_lower in g.get('name', '').lower()
        ]
        
        logger.info(f"Found {len(matched)} groups matching '{keyword}'")
        return matched
    
    def get_group_statistics(self) -> Dict[str, Any]:
        """获取群聊统计信息
        
        Returns:
            统计信息字典
        """
        groups = self.get_all_groups()
        
        total_members = 0
        group_sizes = []
        
        for group in groups:
            try:
                info = self.get_group_detail(group['chatid'])
                member_count = len(info.get('userlist', []))
                total_members += member_count
                group_sizes.append(member_count)
            except Exception:
                continue
        
        stats = {
            'total_groups': len(groups),
            'total_members': total_members,
            'avg_members_per_group': total_members / len(groups) if groups else 0,
            'max_group_size': max(group_sizes) if group_sizes else 0,
            'min_group_size': min(group_sizes) if group_sizes else 0,
        }
        
        logger.info(f"Group statistics: {stats}")
        return stats
    
    def create_group(self, name: str, owner: str, members: List[str],
                    chat_id: Optional[str] = None) -> Optional[str]:
        """创建群聊
        
        Args:
            name: 群聊名称
            owner: 群主 userid
            members: 群成员 userid 列表
            chat_id: 指定的群聊 ID（可选）
            
        Returns:
            创建的群聊 ID，失败返回 None
        """
        try:
            created_chat_id = self.client.create_app_chat(name, owner, members, chat_id)
            
            # 清除缓存，下次重新加载
            self._group_cache.pop(created_chat_id, None)
            
            logger.info(f"Group '{name}' created: {created_chat_id}")
            return created_chat_id
            
        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            return None
    
    def update_group(self, chat_id: str, name: Optional[str] = None,
                    owner: Optional[str] = None, add_members: Optional[List[str]] = None,
                    remove_members: Optional[List[str]] = None) -> bool:
        """修改群聊信息
        
        Args:
            chat_id: 群聊 ID
            name: 新的群聊名称（可选）
            owner: 新的群主 userid（可选）
            add_members: 要添加的成员列表（可选）
            remove_members: 要删除的成员列表（可选）
            
        Returns:
            是否修改成功
        """
        try:
            success = self.client.update_app_chat(
                chat_id, name, owner, add_members, remove_members
            )
            
            if success:
                # 清除缓存
                self._group_cache.pop(chat_id, None)
                logger.info(f"Group {chat_id} updated")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update group: {e}")
            return False
    
    def batch_send_message(self, chat_ids: List[str], content: str) -> Dict[str, bool]:
        """批量发送消息到多个群聊
        
        Args:
            chat_ids: 群聊 ID 列表
            content: 消息内容
            
        Returns:
            发送结果字典 {chat_id: success}
        """
        results = {}
        
        for chat_id in chat_ids:
            try:
                self.client.send_group_message(chat_id, content)
                results[chat_id] = True
                logger.info(f"Message sent to {chat_id}")
            except Exception as e:
                results[chat_id] = False
                logger.error(f"Failed to send message to {chat_id}: {e}")
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Batch send completed: {success_count}/{len(chat_ids)} successful")
        
        return results
    
    def clear_cache(self):
        """清除缓存"""
        self._group_cache.clear()
        logger.info("Group cache cleared")


class WeChatUserManager:
    """企业微信用户管理器"""
    
    def __init__(self, client: WeChatWorkClient):
        """
        Args:
            client: 企业微信客户端
        """
        self.client = client
        self._user_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_user_info(self, user_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """获取用户信息
        
        Args:
            user_id: 用户 ID
            use_cache: 是否使用缓存
            
        Returns:
            用户信息字典
        """
        if use_cache and user_id in self._user_cache:
            return self._user_cache[user_id]
        
        try:
            info = self.client.get_user_info(user_id)
            
            # 更新缓存
            if info:
                self._user_cache[user_id] = info
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {}
    
    def get_users_info(self, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量获取用户信息
        
        Args:
            user_ids: 用户 ID 列表
            
        Returns:
            用户信息字典 {user_id: info}
        """
        result = {}
        
        for user_id in user_ids:
            try:
                info = self.get_user_info(user_id)
                if info:
                    result[user_id] = info
            except Exception as e:
                logger.warning(f"Failed to get info for user {user_id}: {e}")
        
        logger.info(f"Retrieved info for {len(result)}/{len(user_ids)} users")
        return result
    
    def get_department_users(self, department_id: int, 
                           fetch_child: bool = False) -> List[Dict[str, Any]]:
        """获取部门成员列表
        
        Args:
            department_id: 部门 ID
            fetch_child: 是否递归获取子部门成员
            
        Returns:
            部门成员列表
        """
        try:
            users = self.client.get_department_users(department_id, fetch_child)
            logger.info(f"Retrieved {len(users)} users from department {department_id}")
            return users
            
        except Exception as e:
            logger.error(f"Failed to get department users: {e}")
            return []
    
    def search_users_by_name(self, name: str, department_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """根据名称搜索用户
        
        Args:
            name: 用户名称（支持部分匹配）
            department_id: 限定搜索的部门 ID（可选）
            
        Returns:
            匹配的用户列表
        """
        # 如果指定了部门，先获取部门成员
        if department_id is not None:
            users = self.get_department_users(department_id, fetch_child=True)
        else:
            # 否则从缓存中搜索
            users = [
                self.get_user_info(uid) 
                for uid in self._user_cache.keys()
            ]
        
        # 过滤匹配的用户
        name_lower = name.lower()
        matched = [
            u for u in users 
            if name_lower in u.get('name', '').lower()
        ]
        
        logger.info(f"Found {len(matched)} users matching '{name}'")
        return matched
    
    def clear_cache(self):
        """清除缓存"""
        self._user_cache.clear()
        logger.info("User cache cleared")

