#!/usr/bin/env python3
"""列出企业微信群聊并配置生效群聊

功能：
1. 列出所有已知的群聊（从配置或消息回调中收集）
2. 显示群聊详细信息
3. 交互式选择要生效的群聊
4. 更新配置文件

使用方法:
    # 方式1：从环境变量读取配置
    export WECHAT_WORK_CORP_ID="your_corp_id"
    export WECHAT_WORK_SECRET="your_secret"
    export WECHAT_WORK_AGENT_ID="your_agent_id"
    python scripts/list_wechat_groups.py

    # 方式2：从.env文件读取配置
    python scripts/list_wechat_groups.py
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Set

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from interface.wechat.work_client import WeChatWorkClient
from config.settings import settings


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


def load_chatids_from_config() -> Set[str]:
    """从配置文件加载已知的群聊ID"""
    chatids = set()
    
    # 从环境变量或settings加载
    if settings.wechat_group_ids:
        chatids.update(settings.wechat_group_ids.split(','))
    
    # 从历史记录文件加载（如果存在）
    history_file = project_root / "data" / "wechat_chatids.json"
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    chatids.update(data)
                elif isinstance(data, dict) and 'chatids' in data:
                    chatids.update(data['chatids'])
        except Exception as e:
            print(f"⚠️  读取历史记录失败: {e}")
    
    return {cid.strip() for cid in chatids if cid.strip()}


def save_chatids_to_history(chatids: Set[str]):
    """保存群聊ID到历史记录文件"""
    history_file = project_root / "data" / "wechat_chatids.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(list(chatids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  保存历史记录失败: {e}")


def display_chat_info(chat_info: Dict[str, Any], index: int):
    """显示群聊信息"""
    chatid = chat_info.get("chatid", "未知")
    name = chat_info.get("name", "未知群聊")
    owner = chat_info.get("owner", "未知")
    userlist = chat_info.get("userlist", [])
    member_count = len(userlist)
    
    print(f"\n[{index}] {name}")
    print(f"    ID: {chatid}")
    print(f"    群主: {owner}")
    print(f"    成员数: {member_count}")
    if member_count > 0 and member_count <= 10:
        print(f"    成员: {', '.join(userlist)}")
    elif member_count > 10:
        print(f"    成员: {', '.join(userlist[:10])} ... (共{member_count}人)")


def list_and_select_groups():
    """列出群聊并让用户选择"""
    print("=" * 60)
    print("企业微信群聊管理工具")
    print("=" * 60)
    print()
    
    # 获取配置
    corp_id = get_env_or_input("WECHAT_WORK_CORP_ID", "请输入企业ID (corp_id): ")
    secret = get_env_or_input("WECHAT_WORK_SECRET", "请输入应用密钥 (secret): ", secret=True)
    agent_id = get_env_or_input("WECHAT_WORK_AGENT_ID", "请输入应用ID (agent_id): ")
    
    if not all([corp_id, secret, agent_id]):
        print("❌ 错误：缺少必要的配置信息")
        return
    
    print()
    print("正在连接企业微信...")
    try:
        client = WeChatWorkClient(corp_id, secret, agent_id)
        access_token = client._get_access_token()
        print("✅ 连接成功！")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 加载已知的群聊ID
    print()
    print("正在加载群聊列表...")
    known_chatids = load_chatids_from_config()
    
    if not known_chatids:
        print("⚠️  未找到已知的群聊ID")
        print()
        print("提示：")
        print("1. 可以通过消息回调自动收集群聊ID")
        print("2. 可以手动添加群聊ID到 .env 文件：WECHAT_GROUP_IDS=chatid1,chatid2")
        print("3. 可以使用 create_wechat_group.py 创建新群聊")
        print()
        
        # 询问是否要手动输入
        manual_input = input("是否要手动输入群聊ID？(y/n): ").strip().lower()
        if manual_input == 'y':
            chatids_input = input("请输入群聊ID（多个用逗号分隔）: ").strip()
            if chatids_input:
                known_chatids = {cid.strip() for cid in chatids_input.split(',') if cid.strip()}
        else:
            return
    
    print(f"找到 {len(known_chatids)} 个群聊ID")
    
    # 获取群聊信息
    print()
    print("正在获取群聊详细信息...")
    chat_list = client.get_chat_list(list(known_chatids))
    
    if not chat_list:
        print("❌ 无法获取任何群聊信息")
        return
    
    # 显示群聊列表
    print()
    print("=" * 60)
    print("群聊列表")
    print("=" * 60)
    
    valid_chats = []
    for i, chat_info in enumerate(chat_list, 1):
        if "error" not in chat_info:
            display_chat_info(chat_info, i)
            valid_chats.append(chat_info)
        else:
            print(f"\n[{i}] ❌ {chat_info.get('name', '未知群聊')}")
            print(f"    错误: {chat_info.get('error')}")
    
    if not valid_chats:
        print("❌ 没有可用的群聊")
        return
    
    # 让用户选择要生效的群聊
    print()
    print("=" * 60)
    print("选择要生效的群聊")
    print("=" * 60)
    print("输入群聊编号（多个用逗号分隔，例如: 1,3,5）")
    print("输入 'all' 选择所有群聊")
    print("输入 'none' 不选择任何群聊（清空配置）")
    print()
    
    selection = input("请选择: ").strip().lower()
    
    selected_chatids = set()
    if selection == 'all':
        selected_chatids = {chat["chatid"] for chat in valid_chats}
    elif selection == 'none':
        selected_chatids = set()
    else:
        try:
            indices = [int(i.strip()) for i in selection.split(',')]
            for idx in indices:
                if 1 <= idx <= len(valid_chats):
                    selected_chatids.add(valid_chats[idx - 1]["chatid"])
        except ValueError:
            print("❌ 输入格式错误")
            return
    
    # 保存到历史记录
    save_chatids_to_history(known_chatids)
    
    # 更新配置
    print()
    print("=" * 60)
    print("配置更新")
    print("=" * 60)
    
    if selected_chatids:
        chatids_str = ','.join(sorted(selected_chatids))
        print(f"已选择 {len(selected_chatids)} 个群聊：")
        for chatid in sorted(selected_chatids):
            chat_name = next(
                (chat["name"] for chat in valid_chats if chat["chatid"] == chatid),
                chatid
            )
            print(f"  - {chat_name} ({chatid})")
        
        print()
        print("📝 请将以下内容添加到 .env 文件：")
        print(f"WECHAT_GROUP_IDS={chatids_str}")
        
        # 询问是否自动更新.env文件
        env_file = project_root / ".env"
        if env_file.exists():
            auto_update = input("\n是否自动更新 .env 文件？(y/n): ").strip().lower()
            if auto_update == 'y':
                try:
                    # 读取现有配置
                    env_content = env_file.read_text(encoding='utf-8')
                    
                    # 更新或添加 WECHAT_GROUP_IDS
                    lines = env_content.split('\n')
                    updated = False
                    new_lines = []
                    
                    for line in lines:
                        if line.strip().startswith('WECHAT_GROUP_IDS='):
                            new_lines.append(f'WECHAT_GROUP_IDS={chatids_str}')
                            updated = True
                        else:
                            new_lines.append(line)
                    
                    if not updated:
                        new_lines.append(f'WECHAT_GROUP_IDS={chatids_str}')
                    
                    env_file.write_text('\n'.join(new_lines), encoding='utf-8')
                    print("✅ .env 文件已更新！")
                except Exception as e:
                    print(f"⚠️  自动更新失败: {e}")
                    print("请手动更新 .env 文件")
    else:
        print("已清空群聊配置（不限制群聊）")
        print()
        print("📝 如果 .env 文件中有 WECHAT_GROUP_IDS，可以删除该行")


def main():
    """主函数"""
    try:
        list_and_select_groups()
        print()
        print("✅ 完成！")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

