"""
提供消息查询的便捷工具函数。
"""
from datetime import timedelta
from typing import List, Optional

from ...bot import Bot
from ...weixin.message_classes import Message, MessageType


def query_room_messages(
    room_identifier: str,
    message_types: Optional[List[MessageType]] = None,
    time_range: Optional[timedelta] = None,
    limit: int = 100,
    offset: int = 0,
    keywords: Optional[List[str]] = None,
    sender_username: Optional[str] = None,
    bot: Optional[Bot] = None
) -> List[Message]:
    """
    查询群聊消息的便捷方法

    Args:
        room_identifier: 群名称或群ID
        message_types: 消息类型列表，为None则查询所有类型
        time_range: 时间范围
        limit: 返回消息数量限制
        offset: 分页偏移量
        keywords: 关键词列表，消息内容需包含任一关键词
        sender_username: 发送者用户名，为None则查询所有发送者
        bot: Bot实例，如果不提供则使用当前活动的Bot实例

    Returns:
        List[Message]: 消息对象列表
    """
    if not bot:
        bot = Bot.get_current_instance()
        if not bot:
            raise RuntimeError("No active Bot instance found")

    # 获取消息查询服务
    service = bot.get_service('MessageQueryService')
    if not service:
        raise RuntimeError("MessageQueryService not found")

    return service.query_room_messages(
        room_identifier=room_identifier,
        message_types=message_types,
        time_range=time_range,
        limit=limit,
        offset=offset,
        keywords=keywords,
        sender_username=sender_username
    )