#!/usr/bin/env python
"""测试企业微信配置

用于验证企业微信配置是否正确
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from config.settings import settings
from interface.wechat.wecom_client import WeChatWorkClient


def test_config():
    """测试配置"""
    logger.info("=== 企业微信配置测试 ===\n")
    
    # 1. 检查配置
    logger.info("1️⃣  检查配置...")
    
    if not settings.wechat_work_corp_id:
        logger.error("❌ WECHAT_WORK_CORP_ID 未配置")
        return False
    logger.info(f"✅ Corp ID: {settings.wechat_work_corp_id}")
    
    if not settings.wechat_work_secret:
        logger.error("❌ WECHAT_WORK_SECRET 未配置")
        return False
    logger.info(f"✅ Secret: {'*' * 20}")
    
    if not settings.wechat_work_agent_id:
        logger.error("❌ WECHAT_WORK_AGENT_ID 未配置")
        return False
    logger.info(f"✅ Agent ID: {settings.wechat_work_agent_id}\n")
    
    # 2. 创建客户端
    logger.info("2️⃣  创建客户端...")
    try:
        client = WeChatWorkClient(
            corp_id=settings.wechat_work_corp_id,
            secret=settings.wechat_work_secret,
            agent_id=settings.wechat_work_agent_id
        )
        logger.info("✅ 客户端创建成功\n")
    except Exception as e:
        logger.error(f"❌ 客户端创建失败: {e}")
        return False
    
    # 3. 测试获取 access_token
    logger.info("3️⃣  测试获取 Access Token...")
    try:
        token = client._get_access_token()
        logger.info(f"✅ Access Token 获取成功: {token[:20]}...\n")
    except Exception as e:
        logger.error(f"❌ Access Token 获取失败: {e}")
        logger.info("\n💡 可能的原因:")
        logger.info("  1. Corp ID 或 Secret 配置错误")
        logger.info("  2. 网络无法访问 qyapi.weixin.qq.com")
        logger.info("  3. 应用已被停用")
        return False
    
    # 4. 测试获取群聊列表
    logger.info("4️⃣  测试获取群聊列表...")
    try:
        groups = client.get_all_app_chats()
        logger.info(f"✅ 获取成功，找到 {len(groups)} 个群聊")
        
        if groups:
            logger.info("\n📋 群聊列表（最多显示 5 个）:")
            for i, group in enumerate(groups[:5], 1):
                logger.info(f"  {i}. {group.get('name')} ({group.get('chatid')})")
        else:
            logger.warning("⚠️  没有找到任何群聊")
            logger.info("\n💡 提示:")
            logger.info("  可以使用 scripts/create_wechat_group.py 创建测试群聊")
        
        logger.info("")
    except Exception as e:
        logger.error(f"❌ 获取群聊列表失败: {e}")
        logger.info("\n💡 可能的原因:")
        logger.info("  1. 应用没有群聊管理权限")
        logger.info("  2. Access Token 无效")
        return False
    
    # 5. 测试获取用户信息（可选）
    if groups:
        logger.info("5️⃣  测试获取群聊详细信息...")
        try:
            first_group = groups[0]
            chat_id = first_group['chatid']
            info = client.get_chat_info(chat_id)
            
            logger.info(f"✅ 获取成功")
            logger.info(f"\n📋 群聊详情: {info.get('name')}")
            logger.info(f"  群主: {info.get('owner')}")
            logger.info(f"  成员数: {len(info.get('userlist', []))}")
            logger.info(f"  成员列表: {info.get('userlist', [])}")
            logger.info("")
        except Exception as e:
            logger.error(f"❌ 获取群聊详情失败: {e}")
    
    # 6. 检查回调配置
    logger.info("6️⃣  检查回调配置...")
    
    if settings.wechat_work_token and settings.wechat_work_encoding_aes_key:
        logger.info(f"✅ Token: {settings.wechat_work_token[:10]}...")
        logger.info(f"✅ EncodingAESKey: {settings.wechat_work_encoding_aes_key[:10]}...")
        logger.info(f"✅ 回调服务配置: http://{settings.wechat_http_host}:{settings.wechat_http_port}/callback")
    else:
        logger.warning("⚠️  回调配置未设置（如果不需要接收消息可以忽略）")
        logger.info("\n💡 提示:")
        logger.info("  如需接收消息，请配置:")
        logger.info("  - WECHAT_WORK_TOKEN")
        logger.info("  - WECHAT_WORK_ENCODING_AES_KEY")
    
    logger.info("")
    
    # 7. 总结
    logger.info("=" * 50)
    logger.info("🎉 配置测试完成！")
    logger.info("")
    logger.info("✅ 所有必需配置正常")
    logger.info("")
    logger.info("下一步:")
    logger.info("  1. 运行 python examples/wechat/basic_usage.py 查看基础示例")
    logger.info("  2. 运行 python examples/wechat/advanced_usage.py 查看高级功能")
    logger.info("  3. 运行 python main.py 启动完整的机器人")
    logger.info("")
    logger.info("📖 查看文档:")
    logger.info("  - interface/QUICK_START.md - 快速开始")
    logger.info("  - interface/wechat/README.md - 功能文档")
    logger.info("  - interface/wechat/SETUP_GUIDE.md - 配置指南")
    logger.info("=" * 50)
    
    return True


def main():
    """主函数"""
    try:
        success = test_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n👋 测试已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

