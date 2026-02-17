#!/usr/bin/env python3
"""创建企业微信群聊并获取chatid

使用方法:
    export WECHAT_WORK_CORP_ID="your_corp_id"
    export WECHAT_WORK_SECRET="your_secret"
    export WECHAT_WORK_AGENT_ID="your_agent_id"
    python scripts/create_wechat_group.py
"""
import os
import sys
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from interface.wechat.work_client import WeChatWorkClient


def get_env_or_input(name: str, prompt: str, secret: bool = False) -> str:
    """从环境变量获取，如果没有则提示输入"""
    value = os.getenv(name)
    if value:
        return value
    
    if secret:
        import getpass
        return getpass.getpass(prompt)
    else:
        return input(prompt)


def create_group_chat():
    """创建群聊"""
    print("=" * 60)
    print("企业微信群聊创建工具")
    print("=" * 60)
    print()
    
    # 获取配置
    corp_id = get_env_or_input("WECHAT_WORK_CORP_ID", "请输入企业ID (corp_id): ")
    secret = get_env_or_input("WECHAT_WORK_SECRET", "请输入应用密钥 (secret): ", secret=True)
    agent_id = get_env_or_input("WECHAT_WORK_AGENT_ID", "请输入应用ID (agent_id): ")
    
    if not all([corp_id, secret, agent_id]):
        print("❌ 错误：缺少必要的配置信息")
        return None
    
    print()
    print("正在初始化客户端...")
    try:
        client = WeChatWorkClient(corp_id, secret, agent_id)
        access_token = client._get_access_token()
        print("✅ 连接成功！")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None
    
    print()
    print("请输入群聊信息：")
    group_name = input("群聊名称 (例如: 门店经营群): ").strip()
    if not group_name:
        group_name = "门店经营群"
    
    print()
    print("请输入群主userid（必须是群成员之一）")
    owner = input("群主userid: ").strip()
    
    print()
    print("请输入群成员userid列表（至少2人，用逗号分隔）")
    print("例如: zhangsan,lisi,wangwu")
    members_input = input("群成员userid: ").strip()
    
    if not members_input:
        print("❌ 错误：群成员列表不能为空")
        return None
    
    userlist = [uid.strip() for uid in members_input.split(",") if uid.strip()]
    
    if len(userlist) < 2:
        print("❌ 错误：群成员至少需要2人")
        return None
    
    # 确保群主在成员列表中
    if owner and owner not in userlist:
        print(f"⚠️  警告：群主 {owner} 不在成员列表中，已自动添加")
        userlist.insert(0, owner)
    
    print()
    print("正在创建群聊...")
    print(f"  群聊名称: {group_name}")
    print(f"  群主: {owner if owner else userlist[0]}")
    print(f"  成员数: {len(userlist)}")
    print()
    
    # 创建群聊
    url = "https://qyapi.weixin.qq.com/cgi-bin/appchat/create"
    params = {"access_token": access_token}
    
    data = {
        "name": group_name,
        "owner": owner if owner else userlist[0],
        "userlist": userlist
    }
    
    try:
        response = requests.post(url, params=params, json=data, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            chatid = result.get("chatid")
            print("=" * 60)
            print("✅ 群聊创建成功！")
            print("=" * 60)
            print(f"群聊名称: {group_name}")
            print(f"群聊ID (chatid): {chatid}")
            print()
            print("📝 请将以下内容添加到 .env 文件：")
            print(f"WECHAT_GROUP_IDS={chatid}")
            print()
            
            # 测试发送消息
            print("🧪 测试发送消息...")
            try:
                client.send_group_message(chatid, f"✅ 群聊创建成功！这是来自系统的测试消息。")
                print("✅ 测试消息发送成功！")
            except Exception as e:
                print(f"⚠️  测试消息发送失败: {e}")
                print("   这可能是因为应用权限或网络问题，但群聊已创建成功")
            
            print()
            print("=" * 60)
            return chatid
        else:
            print(f"❌ 创建失败: {result.get('errmsg')} (错误码: {result.get('errcode')})")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def main():
    """主函数"""
    try:
        chatid = create_group_chat()
        if chatid:
            print("✅ 完成！")
            sys.exit(0)
        else:
            print("❌ 创建失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

