"""
消息查询工具类。
提供便捷的消息查询接口。
"""
from datetime import datetime, timedelta
from typing import List, Optional, Union

from ..weixin.message_classes import Message, MessageType
from ..services.functional.message_query_service import MessageQueryService


def query_room_messages(
    room_identifier: str,
    message_types: Optional[List[MessageType]] = None,
    time_range: Optional[Union[int, timedelta]] = None,
    limit: int = 100,
    offset: int = 0,
    keywords: Optional[List[str]] = None,
    sender_username: Optional[str] = None,
    service: Optional[MessageQueryService] = None,
) -> List[Message]:
    """
    查询群聊消息的便捷方法

    Args:
        room_identifier: 群名称或群ID
        message_types: 消息类型列表，为None则查询所有类型
        time_range: 时间范围（秒数或timedelta对象），为None则不限制时间
        limit: 返回消息数量限制
        offset: 分页偏移量
        keywords: 关键词列表，消息内容需包含任一关键词
        sender_username: 发送者用户名，为None则查询所有发送者
        service: 消息查询服务实例，如果不提供则使用当前活动的Bot实例

    Returns:
        List[Message]: 消息对象列表

    Examples:
        >>> # 查询群"测试群"最近1小时的文本消息
        >>> messages = query_room_messages(
        ...     "测试群",
        ...     message_types=[MessageType.Text],
        ...     time_range=timedelta(hours=1)
        ... )
        
        >>> # 查询指定用户在群中的图片消息
        >>> messages = query_room_messages(
        ...     "测试群",
        ...     message_types=[MessageType.Image],
        ...     sender_username="wxid_abc123"
        ... )
        
        >>> # 搜索包含关键词的消息
        >>> messages = query_room_messages(
        ...     "测试群",
        ...     keywords=["关键词1", "关键词2"],
        ...     time_range=timedelta(days=7)
        ... )
    """
    if not service:
        from ..bot import Bot
        current_bot = Bot.get_current_instance()
        if not current_bot:
            raise RuntimeError("No active Bot instance found")
        service = current_bot.get_service(MessageQueryService)

    return service.query_room_messages(
        room_identifier=room_identifier,
        message_types=message_types,
        time_range=time_range,
        limit=limit,
        offset=offset,
        keywords=keywords,
        sender_username=sender_username,
    )


def get_room_message_count(
    room_identifier: str,
    message_types: Optional[List[MessageType]] = None,
    time_range: Optional[Union[int, timedelta]] = None,
    sender_username: Optional[str] = None,
    service: Optional[MessageQueryService] = None,
) -> int:
    """
    获取群聊消息数量的便捷方法

    Args:
        room_identifier: 群名称或群ID
        message_types: 消息类型列表
        time_range: 时间范围（秒数或timedelta对象）
        sender_username: 发送者用户名
        service: 消息查询服务实例，如果不提供则使用当前活动的Bot实例

    Returns:
        int: 消息数量

    Examples:
        >>> # 获取群"测试群"最近24小时的所有消息数量
        >>> count = get_room_message_count(
        ...     "测试群",
        ...     time_range=timedelta(days=1)
        ... )
        
        >>> # 获取指定用户的消息数量
        >>> count = get_room_message_count(
        ...     "测试群",
        ...     sender_username="wxid_abc123"
        ... )
    """
    if not service:
        from ..bot import Bot
        current_bot = Bot.get_current_instance()
        if not current_bot:
            raise RuntimeError("No active Bot instance found")
        service = current_bot.get_service(MessageQueryService)

    return service.get_room_message_count(
        room_identifier=room_identifier,
        message_types=message_types,
        time_range=time_range,
        sender_username=sender_username,
    )