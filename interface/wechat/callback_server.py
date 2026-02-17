
"""企业微信消息回调服务器

接收和处理企业微信的消息回调，包括：
- 消息验证（URL验证）
- 消息解密
- 消息分发
"""
import base64
import hashlib
import struct
import time
import xml.etree.ElementTree as ET
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs

from Crypto.Cipher import AES
from fastapi import FastAPI, Request, Response
from loguru import logger


class WXBizMsgCrypt:
    """企业微信消息加解密类
    
    实现企业微信消息的加密、解密和签名验证
    """
    
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        """
        Args:
            token: 企业微信后台配置的 Token
            encoding_aes_key: 企业微信后台配置的 EncodingAESKey
            corp_id: 企业 ID
        """
        self.token = token
        self.corp_id = corp_id
        # EncodingAESKey 是 43 位字符，需要补 '=' 转为 base64
        self.key = base64.b64decode(encoding_aes_key + '=')
        self.iv = self.key[:16]  # AES 的 IV 为 key 的前 16 字节
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str, 
                        echo_str: str = "") -> bool:
        """验证签名
        
        Args:
            signature: 企业微信加密签名
            timestamp: 时间戳
            nonce: 随机数
            echo_str: 随机字符串（URL验证时使用）
            
        Returns:
            签名是否有效
        """
        try:
            # 按字典序排序
            sort_list = [self.token, timestamp, nonce]
            if echo_str:
                sort_list.append(echo_str)
            sort_list.sort()
            
            # 拼接字符串并计算 SHA1
            s = ''.join(sort_list)
            sha = hashlib.sha1(s.encode('utf-8'))
            expected_signature = sha.hexdigest()
            
            return signature == expected_signature
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def decrypt(self, encrypt_str: str) -> Tuple[str, str]:
        """解密消息
        
        Args:
            encrypt_str: 加密的消息字符串
            
        Returns:
            (解密后的消息, corp_id)
            
        Raises:
            Exception: 解密失败时抛出异常
        """
        try:
            # Base64 解码
            cipher_text = base64.b64decode(encrypt_str)
            
            # AES 解密
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            plain_text = cipher.decrypt(cipher_text)
            
            # 去除补位字符
            pad = plain_text[-1]
            if isinstance(pad, str):
                pad = ord(pad)
            plain_text = plain_text[:-pad]
            
            # 解析消息长度（前16字节是随机字符串，接下来4字节是消息长度）
            content_length = struct.unpack('!I', plain_text[16:20])[0]
            
            # 提取消息内容和 corp_id
            content = plain_text[20:20+content_length].decode('utf-8')
            from_corp_id = plain_text[20+content_length:].decode('utf-8')
            
            # 验证 corp_id
            if from_corp_id != self.corp_id:
                raise Exception(f"Corp ID mismatch: {from_corp_id} != {self.corp_id}")
            
            return content, from_corp_id
            
        except Exception as e:
            logger.error(f"Error decrypting message: {e}")
            raise
    
    def encrypt(self, text: str) -> str:
        """加密消息
        
        Args:
            text: 待加密的消息
            
        Returns:
            加密后的 base64 字符串
        """
        try:
            import random
            import string
            
            # 生成16字节随机字符串
            random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            
            # 消息长度（4字节网络字节序）
            text_bytes = text.encode('utf-8')
            msg_len = struct.pack('!I', len(text_bytes))
            
            # 拼接：随机字符串 + 消息长度 + 消息内容 + corp_id
            corp_id_bytes = self.corp_id.encode('utf-8')
            plain_text = random_str.encode('utf-8') + msg_len + text_bytes + corp_id_bytes
            
            # PKCS7 补位
            block_size = 32
            pad = block_size - len(plain_text) % block_size
            plain_text += bytes([pad] * pad)
            
            # AES 加密
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            cipher_text = cipher.encrypt(plain_text)
            
            # Base64 编码
            return base64.b64encode(cipher_text).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encrypting message: {e}")
            raise


class WeChatCallbackServer:
    """企业微信回调服务器
    
    处理企业微信的消息回调和事件回调
    """
    
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str,
                 host: str = "0.0.0.0", port: int = 8000):
        """
        Args:
            token: 企业微信后台配置的 Token
            encoding_aes_key: 企业微信后台配置的 EncodingAESKey
            corp_id: 企业 ID
            host: 监听地址
            port: 监听端口
        """
        self.crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
        self.host = host
        self.port = port
        self.app = FastAPI(title="WeChat Work Callback Server")
        self.message_handler: Optional[Callable] = None
        self.event_handler: Optional[Callable] = None
        
        # 注册路由
        self._setup_routes()
        logger.info(f"Callback server initialized: {host}:{port}")
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/callback")
        async def verify_url(request: Request):
            """URL 验证（企业微信后台配置时使用）"""
            params = dict(request.query_params)
            msg_signature = params.get('msg_signature', '')
            timestamp = params.get('timestamp', '')
            nonce = params.get('nonce', '')
            echostr = params.get('echostr', '')
            
            logger.info(f"URL verification request: {params}")
            
            # 验证签名
            if not self.crypto.verify_signature(msg_signature, timestamp, nonce, echostr):
                logger.error("Invalid signature")
                return Response(content="Invalid signature", status_code=403)
            
            try:
                # 解密 echostr
                decrypted_echostr, _ = self.crypto.decrypt(echostr)
                logger.info("URL verification successful")
                return Response(content=decrypted_echostr)
            except Exception as e:
                logger.error(f"Error decrypting echostr: {e}")
                return Response(content="Decryption failed", status_code=500)
        
        @self.app.post("/callback")
        async def handle_callback(request: Request):
            """处理消息回调"""
            params = dict(request.query_params)
            msg_signature = params.get('msg_signature', '')
            timestamp = params.get('timestamp', '')
            nonce = params.get('nonce', '')
            
            # 读取请求体
            body = await request.body()
            body_str = body.decode('utf-8')
            
            logger.debug(f"Received callback: signature={msg_signature}, timestamp={timestamp}")
            
            try:
                # 解析 XML
                root = ET.fromstring(body_str)
                encrypt_msg = root.find('Encrypt').text
                
                # 验证签名
                if not self.crypto.verify_signature(msg_signature, timestamp, nonce, encrypt_msg):
                    logger.error("Invalid signature")
                    return Response(content="Invalid signature", status_code=403)
                
                # 解密消息
                decrypted_msg, _ = self.crypto.decrypt(encrypt_msg)
                logger.debug(f"Decrypted message: {decrypted_msg[:100]}...")
                
                # 解析消息
                msg_root = ET.fromstring(decrypted_msg)
                msg_dict = self._parse_xml_to_dict(msg_root)
                
                # 处理消息
                response_msg = await self._handle_message(msg_dict)
                
                # 如果有回复消息，加密后返回
                if response_msg:
                    encrypted_msg = self.crypto.encrypt(response_msg)
                    response_xml = self._build_response_xml(encrypted_msg, timestamp, nonce)
                    return Response(content=response_xml, media_type="application/xml")
                else:
                    return Response(content="success")
                    
            except Exception as e:
                logger.error(f"Error handling callback: {e}")
                return Response(content="Error", status_code=500)
    
    def _parse_xml_to_dict(self, root: ET.Element) -> Dict[str, Any]:
        """将 XML 转换为字典"""
        msg_dict = {}
        for child in root:
            msg_dict[child.tag] = child.text
        return msg_dict
    
    def _build_response_xml(self, encrypt_msg: str, timestamp: str, nonce: str) -> str:
        """构建响应 XML"""
        # 计算签名
        sort_list = [self.crypto.token, timestamp, nonce, encrypt_msg]
        sort_list.sort()
        sha = hashlib.sha1(''.join(sort_list).encode('utf-8'))
        signature = sha.hexdigest()
        
        # 构建 XML
        xml_str = f"""<xml>
<Encrypt><![CDATA[{encrypt_msg}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>"""
        return xml_str
    
    async def _handle_message(self, msg_dict: Dict[str, Any]) -> Optional[str]:
        """处理消息
        
        Args:
            msg_dict: 解析后的消息字典
            
        Returns:
            回复消息的 XML 字符串，如果不需要回复则返回 None
        """
        msg_type = msg_dict.get('MsgType', '')
        
        logger.info(f"Handling message: type={msg_type}, from={msg_dict.get('FromUserName')}")
        
        if msg_type == 'event':
            # 事件消息
            if self.event_handler:
                return await self.event_handler(msg_dict)
        else:
            # 普通消息
            if self.message_handler:
                return await self.message_handler(msg_dict)
        
        return None
    
    def set_message_handler(self, handler: Callable):
        """设置消息处理器
        
        Args:
            handler: 异步函数，接收消息字典，返回回复消息的 XML 字符串或 None
        """
        self.message_handler = handler
        logger.info("Message handler registered")
    
    def set_event_handler(self, handler: Callable):
        """设置事件处理器
        
        Args:
            handler: 异步函数，接收事件字典，返回回复消息的 XML 字符串或 None
        """
        self.event_handler = handler
        logger.info("Event handler registered")
    
    def start(self):
        """启动服务器"""
        import uvicorn
        logger.info(f"Starting callback server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)
    
    async def start_async(self):
        """异步启动服务器（用于在后台运行）"""
        import uvicorn
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        logger.info(f"Starting callback server on {self.host}:{self.port}")
        await server.serve()

