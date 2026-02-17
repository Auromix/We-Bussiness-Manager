#!/usr/bin/env python3
"""从消息回调中收集群聊ID

这个脚本可以帮助你从消息回调中自动收集群聊ID。
需要配置消息回调服务器，当有群聊消息时，会自动收集chatid。

使用方法:
    1. 配置消息回调（参考 WECHAT_WORK_SETUP.md）
    2. 运行此脚本启动回调服务器
    3. 在群聊中发送消息，chatid会自动收集
    4. 使用 list_wechat_groups.py 查看和管理收集到的群聊
"""
import os
import sys
import json
from pathlib import Path
from typing import Set
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("❌ 需要安装 fastapi 和 uvicorn")
    print("运行: pip install fastapi uvicorn")
    sys.exit(1)


app = FastAPI(title="WeChat ChatID Collector")
CHATIDS_FILE = project_root / "data" / "wechat_chatids.json"


def load_chatids() -> Set[str]:
    """加载已收集的群聊ID"""
    if not CHATIDS_FILE.exists():
        return set()
    
    try:
        with open(CHATIDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            elif isinstance(data, dict) and 'chatids' in data:
                return set(data['chatids'])
            return set()
    except Exception:
        return set()


def save_chatids(chatids: Set[str]):
    """保存群聊ID"""
    CHATIDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(CHATIDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(chatids), f, ensure_ascii=False, indent=2)


@app.post("/wechat/callback")
async def wechat_callback(request: Request):
    """接收企业微信消息回调"""
    try:
        data = await request.json()
        
        # 检查是否是群聊消息
        chat_id = data.get("ChatId") or data.get("chatid")
        
        if chat_id:
            chatids = load_chatids()
            if chat_id not in chatids:
                chatids.add(chat_id)
                save_chatids(chatids)
                
                chat_name = data.get("ChatName", "未知群聊")
                print(f"✅ 收集到新群聊: {chat_name} ({chat_id})")
                print(f"   当前已收集 {len(chatids)} 个群聊")
        
        # 返回成功响应（企业微信要求）
        return JSONResponse({
            "errcode": 0,
            "errmsg": "ok"
        })
        
    except Exception as e:
        print(f"❌ 处理回调失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"errcode": -1, "errmsg": str(e)}
        )


@app.get("/wechat/chatids")
async def list_chatids():
    """查看已收集的群聊ID"""
    chatids = load_chatids()
    return {
        "count": len(chatids),
        "chatids": list(chatids)
    }


@app.get("/")
async def root():
    """根路径"""
    chatids = load_chatids()
    return {
        "service": "WeChat ChatID Collector",
        "collected_chatids": len(chatids),
        "endpoints": {
            "POST /wechat/callback": "接收企业微信消息回调",
            "GET /wechat/chatids": "查看已收集的群聊ID"
        }
    }


def main():
    """主函数"""
    print("=" * 60)
    print("企业微信群聊ID收集服务")
    print("=" * 60)
    print()
    print("此服务会监听企业微信消息回调，自动收集群聊ID")
    print()
    print("使用说明：")
    print("1. 确保已配置企业微信消息回调URL")
    print("2. 回调URL应指向: http://your-server:8000/wechat/callback")
    print("3. 在群聊中发送消息，chatid会自动收集")
    print("4. 访问 http://localhost:8000/wechat/chatids 查看已收集的群聊")
    print("5. 使用 list_wechat_groups.py 管理收集到的群聊")
    print()
    
    chatids = load_chatids()
    print(f"当前已收集 {len(chatids)} 个群聊ID")
    print()
    print("启动服务器...")
    print("访问 http://localhost:8000 查看服务状态")
    print("按 Ctrl+C 停止服务")
    print()
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n\n服务已停止")
        chatids = load_chatids()
        if chatids:
            print(f"\n已收集 {len(chatids)} 个群聊ID")
            print("运行以下命令查看和管理群聊：")
            print("  python scripts/list_wechat_groups.py")


if __name__ == "__main__":
    main()

