#!/usr/bin/env python3
"""
PushPlus OpenAPI 客户端
提供 AccessKey 管理、消息接口、用户接口、消息Token接口、群组接口等功能

使用说明:
1. 首先调用 get_access_key() 获取 AccessKey（有效期2小时）
2. 使用 AccessKey 调用其他接口，需要在请求头中设置 access-key

环境变量:
- PUSHPLUS_USER_TOKEN: 用户 Token（用于获取 AccessKey）
- PUSHPLUS_SECRET_KEY: 用户 SecretKey（用于获取 AccessKey）
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


# OpenAPI 基础地址
OPENAPI_BASE_URL = "https://www.pushplus.plus/api"

# 环境变量名
ENV_USER_TOKEN = "PUSHPLUS_USER_TOKEN"
ENV_SECRET_KEY = "PUSHPLUS_SECRET_KEY"
MAX_PAGE_SIZE = 50
MAX_TOPIC_QRCODE_SECOND = 2592000


def get_access_key(user_token: Optional[str] = None, secret_key: Optional[str] = None) -> Dict[str, Any]:
    """
    获取 AccessKey（有效期2小时）
    
    Args:
        user_token: 用户 Token（如不提供，从环境变量 PUSHPLUS_USER_TOKEN 获取）
        secret_key: 用户 SecretKey（如不提供，从环境变量 PUSHPLUS_SECRET_KEY 获取）
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": {
                "accessKey": "d7b******62f",
                "expiresIn": 7200
            }
        }
    """
    # 从环境变量获取（如果未提供）
    token = user_token or os.environ.get(ENV_USER_TOKEN)
    secret = secret_key or os.environ.get(ENV_SECRET_KEY)
    
    if not token or not secret:
        raise ValueError("请提供 user_token 和 secret_key，或设置环境变量 PUSHPLUS_USER_TOKEN 和 PUSHPLUS_SECRET_KEY")
    
    url = f"{OPENAPI_BASE_URL}/common/openApi/getAccessKey"
    payload = {
        "token": token,
        "secretKey": secret
    }
    
    return _make_request(url, payload)


def _validate_non_empty_text(field_name: str, value: Optional[str]) -> str:
    """校验必填文本参数"""
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} 不能为空")
    return str(value).strip()


def _validate_positive_int(field_name: str, value: int, minimum: int = 1) -> int:
    """校验正整数参数"""
    if not isinstance(value, int):
        raise ValueError(f"{field_name} 必须为整数")
    if value < minimum:
        raise ValueError(f"{field_name} 必须大于等于 {minimum}")
    return value


def _validate_page_params(current: int, page_size: int) -> None:
    """校验分页参数"""
    _validate_positive_int("current", current)
    _validate_positive_int("page_size", page_size)
    if page_size > MAX_PAGE_SIZE:
        raise ValueError(f"page_size 不能大于 {MAX_PAGE_SIZE}")


# ==================== 消息接口 ====================

def list_messages(access_key: str, current: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    获取消息列表
    
    Args:
        access_key: AccessKey
        current: 当前页码，默认1
        page_size: 每页大小，最大50，默认20
        
    Returns:
        消息列表数据
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    _validate_page_params(current, page_size)

    url = f"{OPENAPI_BASE_URL}/open/message/list"
    payload = {
        "current": current,
        "pageSize": page_size
    }
    
    return _make_request(url, payload, validated_access_key)


def get_message_result(access_key: str, short_code: str) -> Dict[str, Any]:
    """
    查询消息发送结果
    
    Args:
        access_key: AccessKey
        short_code: 消息短链码
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": {
                "status": 2,
                "errorMessage": "",
                "updateTime": "2021-12-08 12:19:02"
            }
        }
        status: 0-未投递，1-发送中，2-已发送，3-发送失败
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_short_code = _validate_non_empty_text("short_code", short_code)
    return _make_request(
        f"{OPENAPI_BASE_URL}/open/message/sendMessageResult?shortCode={validated_short_code}",
        method="GET",
        access_key=validated_access_key
    )


def delete_message(access_key: str, short_code: str) -> Dict[str, Any]:
    """
    删除消息
    
    注：删除后所有接收人均无法查看，且无法撤销。
    
    Args:
        access_key: AccessKey
        short_code: 消息短链码
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": "删除成功"
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_short_code = _validate_non_empty_text("short_code", short_code)
    url = f"{OPENAPI_BASE_URL}/open/message/deleteMessage?shortCode={validated_short_code}"
    
    return _make_request(url, method="DELETE", access_key=validated_access_key)


# ==================== 用户接口 ====================

def get_user_token(access_key: str) -> Dict[str, Any]:
    """
    获取用户 Token
    
    Args:
        access_key: AccessKey
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": "604******f0b"
        }
    """
    url = f"{OPENAPI_BASE_URL}/open/user/token"
    
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    return _make_request(url, method="GET", access_key=validated_access_key)


def get_user_info(access_key: str) -> Dict[str, Any]:
    """
    获取个人资料详情
    
    Args:
        access_key: AccessKey
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": {
                "openId": "o0a******A3Y",
                "nickName": "昵称",
                "headImgUrl": "头像URL",
                "userSex": 1,
                "token": "604******f0b",
                "phoneNumber": "13******4",
                "email": "admin@xxx.com",
                "emailStatus": 1,
                "birthday": "1990-01-01",
                "points": 2
            }
        }
    """
    url = f"{OPENAPI_BASE_URL}/open/user/myInfo"
    
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    return _make_request(url, method="GET", access_key=validated_access_key)


def get_limit_time(access_key: str) -> Dict[str, Any]:
    """
    获取解封剩余时间
    
    Args:
        access_key: AccessKey
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": {
                "sendLimit": 1,
                "userLimitTime": ""
            }
        }
        sendLimit: 1-无限制，2-短期限制，3-永久限制
    """
    url = f"{OPENAPI_BASE_URL}/open/user/userLimitTime"
    
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    return _make_request(url, method="GET", access_key=validated_access_key)


def get_send_count(access_key: str) -> Dict[str, Any]:
    """
    查询当日消息接口请求次数
    
    Args:
        access_key: AccessKey
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": {
                "wechatSendCount": 283,
                "cpSendCount": 0,
                "webhookSendCount": 19,
                "mailSendCount": 0
            }
        }
    """
    url = f"{OPENAPI_BASE_URL}/open/user/sendCount"
    
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    return _make_request(url, method="GET", access_key=validated_access_key)


# ==================== 消息Token接口 ====================

def list_tokens(access_key: str, current: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    获取消息 Token 列表
    
    Args:
        access_key: AccessKey
        current: 当前页码，默认1
        page_size: 每页大小，最大50，默认20
        
    Returns:
        消息 Token 列表
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    _validate_page_params(current, page_size)

    url = f"{OPENAPI_BASE_URL}/open/token/list"
    payload = {
        "current": current,
        "pageSize": page_size
    }
    
    return _make_request(url, payload, validated_access_key)


def add_token(access_key: str, name: str, expire_time: Optional[str] = None) -> Dict[str, Any]:
    """
    新增消息 Token
    
    Args:
        access_key: AccessKey
        name: 令牌名称
        expire_time: 过期时间，格式 "2035-05-09 22:34:00"，默认 "2999-12-31"
        
    Returns:
        {
            "code": 200,
            "msg": "执行成功",
            "data": "837******46e2"  # 新建的消息 Token
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_name = _validate_non_empty_text("name", name)
    url = f"{OPENAPI_BASE_URL}/open/token/add"
    payload = {
        "name": validated_name
    }
    if expire_time:
        payload["expireTime"] = expire_time
    
    return _make_request(url, payload, validated_access_key)


def edit_token(access_key: str, token_id: int, name: str, expire_time: Optional[str] = None) -> Dict[str, Any]:
    """
    修改消息 Token
    
    Args:
        access_key: AccessKey
        token_id: 消息 Token 编号
        name: 令牌名称
        expire_time: 过期时间，格式 "2035-05-09 22:34:00"
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": "修改成功"
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_token_id = _validate_positive_int("token_id", token_id)
    validated_name = _validate_non_empty_text("name", name)
    url = f"{OPENAPI_BASE_URL}/open/token/edit"
    payload = {
        "id": validated_token_id,
        "name": validated_name
    }
    if expire_time:
        payload["expireTime"] = expire_time
    
    return _make_request(url, payload, validated_access_key)


def delete_token(access_key: str, token_id: int) -> Dict[str, Any]:
    """
    删除消息 Token
    
    Args:
        access_key: AccessKey
        token_id: 消息 Token 编号
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": "删除成功"
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_token_id = _validate_positive_int("token_id", token_id)
    url = f"{OPENAPI_BASE_URL}/open/token/deleteToken?id={validated_token_id}"
    
    return _make_request(url, method="DELETE", access_key=validated_access_key)


# ==================== 群组接口 ====================

def list_topics(access_key: str, topic_type: int = 0, current: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    获取群组列表
    
    Args:
        access_key: AccessKey
        topic_type: 群组类型，0-我创建的，1-我加入的，默认0
        current: 当前页码，默认1
        page_size: 每页大小，最大50，默认20
        
    Returns:
        群组列表
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    _validate_page_params(current, page_size)
    if topic_type not in (0, 1):
        raise ValueError("topic_type 仅支持 0（我创建的）或 1（我加入的）")

    url = f"{OPENAPI_BASE_URL}/open/topic/list"
    payload = {
        "current": current,
        "pageSize": page_size,
        "params": {
            "topicType": topic_type
        }
    }
    
    return _make_request(url, payload, validated_access_key)


def get_topic_detail(access_key: str, topic_id: int) -> Dict[str, Any]:
    """
    获取群组详情（我创建的群组）
    
    Args:
        access_key: AccessKey
        topic_id: 群组编号
        
    Returns:
        群组详情
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_topic_id = _validate_positive_int("topic_id", topic_id)
    url = f"{OPENAPI_BASE_URL}/open/topic/detail?topicId={validated_topic_id}"
    
    return _make_request(url, method="GET", access_key=validated_access_key)


def add_topic(
    access_key: str,
    topic_code: str,
    topic_name: str,
    contact: str,
    introduction: str,
    receipt_message: Optional[str] = None,
    app_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    新增群组
    
    Args:
        access_key: AccessKey
        topic_code: 群组编码
        topic_name: 群组名称
        contact: 联系方式
        introduction: 群组简介
        receipt_message: 加入后回复内容（可选）
        app_id: 微信公众号 Id（可选，默认使用 pushplus 公众号）
        
    Returns:
        {
            "code": 200,
            "msg": "执行成功",
            "data": 2  # 新建群组的群组编号
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_topic_code = _validate_non_empty_text("topic_code", topic_code)
    validated_topic_name = _validate_non_empty_text("topic_name", topic_name)
    validated_contact = _validate_non_empty_text("contact", contact)
    validated_introduction = _validate_non_empty_text("introduction", introduction)
    url = f"{OPENAPI_BASE_URL}/open/topic/add"
    payload = {
        "topicCode": validated_topic_code,
        "topicName": validated_topic_name,
        "contact": validated_contact,
        "introduction": validated_introduction
    }
    if receipt_message:
        payload["receiptMessage"] = receipt_message
    if app_id:
        payload["appId"] = app_id
    
    return _make_request(url, payload, validated_access_key)


def get_topic_qrcode(
    access_key: str,
    topic_id: int,
    second: int = 604800,
    scan_count: int = -1
) -> Dict[str, Any]:
    """
    获取群组二维码
    
    Args:
        access_key: AccessKey
        topic_id: 群组编号
        second: 二维码有效期（单位秒），默认7天（604800秒），最长30天
        scan_count: 可扫码次数，范围1-999次，-1代表无限次
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": {
                "qrCodeImgUrl": "https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=...",
                "forever": 0  # 0-临时二维码，1-永久二维码
            }
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_topic_id = _validate_positive_int("topic_id", topic_id)
    validated_second = _validate_positive_int("second", second)
    if validated_second > MAX_TOPIC_QRCODE_SECOND:
        raise ValueError(f"second 不能大于 {MAX_TOPIC_QRCODE_SECOND}")
    if not isinstance(scan_count, int):
        raise ValueError("scan_count 必须为整数")
    if scan_count != -1 and not 1 <= scan_count <= 999:
        raise ValueError("scan_count 仅支持 -1 或 1-999")
    url = f"{OPENAPI_BASE_URL}/open/topic/qrCode?topicId={validated_topic_id}&second={validated_second}&scanCount={scan_count}"
    
    return _make_request(url, method="GET", access_key=validated_access_key)


def exit_topic(access_key: str, topic_id: int) -> Dict[str, Any]:
    """
    退出群组
    
    Args:
        access_key: AccessKey
        topic_id: 群组编号
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": "退订成功"
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_topic_id = _validate_positive_int("topic_id", topic_id)
    url = f"{OPENAPI_BASE_URL}/open/topic/exitTopic?topicId={validated_topic_id}"
    
    return _make_request(url, method="GET", access_key=validated_access_key)


def delete_topic(access_key: str, topic_id: int) -> Dict[str, Any]:
    """
    删除群组
    
    Args:
        access_key: AccessKey
        topic_id: 群组编号
        
    Returns:
        {
            "code": 200,
            "msg": "请求成功",
            "data": "群组删除成功"
        }
    """
    validated_access_key = _validate_non_empty_text("access_key", access_key)
    validated_topic_id = _validate_positive_int("topic_id", topic_id)
    url = f"{OPENAPI_BASE_URL}/open/topic/delete?topicId={validated_topic_id}"
    
    return _make_request(url, method="GET", access_key=validated_access_key)


# ==================== 内部工具函数 ====================

def _make_request(
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    access_key: Optional[str] = None,
    method: str = "POST"
) -> Dict[str, Any]:
    """
    发送 HTTP 请求（内部函数）
    
    Args:
        url: 请求 URL
        payload: 请求体数据（POST/PUT 请求）
        access_key: AccessKey（用于在请求头中设置）
        method: 请求方法，默认 POST
        
    Returns:
        API 返回的 JSON 数据
    """
    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PushPlus-OpenAPI-Python/1.0"
    }
    
    # 设置 AccessKey
    if access_key:
        headers["access-key"] = access_key
    
    # 准备请求数据
    data = None
    if payload and method in ["POST", "PUT"]:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    
    # 创建请求
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP 错误: {e.code}"
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            error_msg += f" - {error_body.get('msg', '')}"
        except:
            pass
        raise Exception(error_msg)
    except urllib.error.URLError as e:
        raise Exception(f"URL 错误: {e.reason}")
    except Exception as e:
        raise Exception(f"请求失败: {str(e)}")


# ==================== 便捷函数 ====================

def get_access_key_from_env() -> Dict[str, Any]:
    """
    从环境变量获取 AccessKey
    
    需要设置环境变量:
    - PUSHPLUS_USER_TOKEN
    - PUSHPLUS_SECRET_KEY
    
    Returns:
        AccessKey 响应数据
    """
    return get_access_key()


if __name__ == "__main__":
    # 简单测试
    print("PushPlus OpenAPI 客户端")
    print("请使用以下函数：")
    print("- get_access_key(user_token, secret_key) - 获取 AccessKey")
    print("- list_messages(access_key) - 消息列表")
    print("- get_message_result(access_key, short_code) - 查询发送结果")
    print("- get_user_info(access_key) - 用户信息")
    print("- list_tokens(access_key) - 消息Token列表")
    print("- list_topics(access_key) - 群组列表")
