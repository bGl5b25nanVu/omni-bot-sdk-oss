"""
消息查询服务模块。
提供群聊消息的查询和过滤功能。
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Union

from ...models import UserInfo
from ...services.core.database_service import DatabaseService
from ...weixin.message_classes import Message, MessageType
from ...weixin.message_factory import FACTORY_REGISTRY


class MessageQueryService:
    def __init__(self, user_info: UserInfo, db: DatabaseService):
        self.logger = logging.getLogger(__name__)
        self.user_info = user_info
        self.db = db

    def _get_room_by_name_or_id(self, room_identifier: str) -> Optional[dict]:
        """
        通过群名称或群ID获取群信息

        Args:
            room_identifier: 群名称或群ID

        Returns:
            Optional[dict]: 群信息字典（实际上是ChatRoom对象）
        """
        # chat_rooms 是一个字典，键是 username
        chat_rooms = self.db.chat_rooms

        # 打印所有群组信息用于调试（可选）
        # self.logger.debug(f"正在查找群聊: '{room_identifier}'")

        # 先尝试通过 username 直接查找
        if room_identifier in chat_rooms:
            return chat_rooms[room_identifier]

        # 遍历所有房间，使用真正的room.username查找
        for key, room in chat_rooms.items():
            # 检查是否匹配room.username
            if room.username == room_identifier:
                return room

            # 通过真正的username获取联系人信息
            contact = self.db.get_contact_by_username(room.username)
            if contact and contact.display_name == room_identifier:
                return room

        return None

    def query_room_messages(
        self,
        room_identifier: str,
        message_types: Optional[List[MessageType]] = None,
        time_range: Optional[Union[int, timedelta]] = None,
        limit: int = 100,
        offset: int = 0,
        keywords: Optional[List[str]] = None,
        sender_username: Optional[str] = None,
    ) -> List[Message]:
        """
        查询群聊消息

        Args:
            room_identifier: 群名称或群ID
            message_types: 消息类型列表，为None则查询所有类型
            time_range: 时间范围（秒数或timedelta对象），为None则不限制时间
            limit: 返回消息数量限制
            offset: 分页偏移量
            keywords: 关键词列表，消息内容需包含任一关键词
            sender_username: 发送者用户名，为None则查询所有发送者

        Returns:
            List[Message]: 消息对象列表
        """
        room = self._get_room_by_name_or_id(room_identifier)
        if not room:
            self.logger.warning(f"找不到群聊: {room_identifier}")
            return []

        # 计算时间范围
        if isinstance(time_range, timedelta):
            time_range = int(time_range.total_seconds())

        start_time = None
        if time_range:
            start_time = int(datetime.now().timestamp()) - time_range

        # 使用 DatabaseService 的方法获取消息
        # 获取足够多的消息以便后续过滤（limit + offset的2倍以防过滤后不够）
        fetch_count = (limit + offset) * 2
        messages = []

        try:
            # 获取原始消息数据
            raw_messages = self.db.get_messages_by_username(
                room.username,
                count=fetch_count,
                order="desc"
            )

            # 过滤并创建Message对象
            filtered_messages = []
            for msg_tuple in raw_messages:
                # msg_tuple 实际格式通过测试发现：
                # 索引0: LocalId
                # 索引1: MsgSvrID
                # 索引2: IsSender
                # 索引3: 毫秒时间戳
                # 索引4: Type
                # 索引5: CreateTime (秒时间戳)
                # 索引17: DbPath

                msg_type = msg_tuple[4]  # Type
                create_time = msg_tuple[5]  # CreateTime (秒时间戳)
                # sender_id 暂时不确定索引，先设为None
                sender_id = None
                db_path = msg_tuple[17] if len(msg_tuple) > 17 else None  # DbPath

                # 时间过滤
                if start_time and create_time < start_time:
                    continue

                # 消息类型过滤
                if message_types and msg_type not in [t.value for t in message_types]:
                    continue

                # 发送者过滤 (暂时跳过，因为不确定sender_id字段)
                # if sender_username:
                #     sender = self.db.get_contact_by_username(sender_username)
                #     if not sender or sender.id != sender_id:
                #         continue

                # 获取消息工厂
                factory = FACTORY_REGISTRY.get(msg_type, FACTORY_REGISTRY[-1])

                # 获取发送者信息 (暂时设为None)
                contact = None  # self.db.get_contact_by_sender_id(sender_id, db_path)

                # 创建消息对象
                message = factory.create(
                    message=msg_tuple,
                    user_info=self.user_info,
                    db=self.db,
                    contact=contact,
                    room=room
                )

                # 关键词过滤
                if keywords and not any(kw in str(message.content) for kw in keywords):
                    continue

                filtered_messages.append(message)

            # 应用分页
            messages = filtered_messages[offset:offset + limit]

        except Exception as e:
            self.logger.error(f"查询消息时出错: {e}", exc_info=True)
            return []

        return messages

    def get_room_message_count(
        self,
        room_identifier: str,
        message_types: Optional[List[MessageType]] = None,
        time_range: Optional[Union[int, timedelta]] = None,
        sender_username: Optional[str] = None,
    ) -> int:
        """
        获取群聊消息数量

        Args:
            room_identifier: 群名称或群ID
            message_types: 消息类型列表
            time_range: 时间范围（秒数或timedelta对象）
            sender_username: 发送者用户名

        Returns:
            int: 消息数量
        """
        room = self._get_room_by_name_or_id(room_identifier)
        if not room:
            return 0

        # 计算时间范围
        if isinstance(time_range, timedelta):
            time_range = int(time_range.total_seconds())
        
        start_time = None
        if time_range:
            start_time = int(datetime.now().timestamp()) - time_range

        # 构建SQL查询条件
        conditions = []
        params = []

        # 群ID条件
        room_id_md5 = hashlib.md5(room.username.encode()).hexdigest()
        params.append(room_id_md5)
        conditions.append(f"TableName = 'Msg_{room_id_md5}'")

        # 消息类型条件
        if message_types:
            type_conditions = []
            for t in message_types:
                type_conditions.append("Type = ?")
                params.append(t.value)
            if type_conditions:
                conditions.append(f"({' OR '.join(type_conditions)})")

        # 时间范围条件
        if start_time:
            conditions.append("CreateTime >= ?")
            params.append(start_time)

        # 发送者条件
        if sender_username:
            sender = self.db.get_contact_by_username(sender_username)
            if sender:
                conditions.append("RealSenderId = ?")
                params.append(sender.id)
            else:
                return 0

        # 构建完整SQL
        where_clause = " AND ".join(conditions)
        sql = f"""
        SELECT COUNT(*) as count
        FROM MessageIndex
        WHERE {where_clause}
        """

        try:
            cursor = self.db.cursor
            cursor.execute(sql, params)
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"获取消息数量时出错: {e}", exc_info=True)
            return 0