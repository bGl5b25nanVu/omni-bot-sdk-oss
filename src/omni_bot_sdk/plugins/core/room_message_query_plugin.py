"""
群聊消息查询插件

该插件可以响应特定命令，查询指定群组的聊天记录并返回文本格式的结果。
"""
import asyncio
from datetime import timedelta
import json
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel, Field

from omni_bot_sdk.plugins.core.plugin_interface import (
    Plugin,
    PluginExcuteContext,
    PluginExcuteResponse,
)
from omni_bot_sdk.services.functional.message_query import query_room_messages
from omni_bot_sdk.weixin.message_classes import MessageType

if TYPE_CHECKING:
    from omni_bot_sdk.bot import Bot


class RoomMessageQueryPluginConfig(BaseModel):
    """
    群聊消息查询插件配置

    enabled: 是否启用该插件
    priority: 插件优先级，数值越大优先级越高
    trigger_keyword: 触发查询的关键词，例如 "查询聊天记录"
    default_limit: 默认查询消息条数
    default_hours: 默认查询最近几小时的消息（如果不指定limit）
    """

    enabled: bool = False
    priority: int = 50
    trigger_keyword: str = Field(default="查询聊天记录", description="触发查询的关键词")
    default_limit: int = Field(default=50, ge=1, le=500, description="默认查询消息条数")
    default_hours: int = Field(default=24, ge=1, le=720, description="默认查询最近几小时")


class RoomMessageQueryPlugin(Plugin):
    """
    群聊消息查询插件实现类

    该插件监听群聊消息，当检测到触发关键词时，查询该群的历史消息并以文本形式返回。

    命令格式：
    - "查询聊天记录" - 使用默认配置查询
    - "查询聊天记录 100" - 查询最近100条消息
    - "查询聊天记录 12小时" - 查询最近12小时的消息

    属性：
        priority (int): 插件优先级
        name (str): 插件名称标识符
    """

    priority = 50
    name = "room-message-query-plugin"

    def __init__(self, bot: "Bot" = None):
        super().__init__(bot)
        # 动态优先级支持
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def get_priority(self) -> int:
        return self.priority

    async def handle_message(self, plusginExcuteContext: PluginExcuteContext) -> None:
        """
        处理消息的核心方法

        检查消息是否包含触发关键词，如果包含则解析参数并查询群聊记录
        """
        message = plusginExcuteContext.get_message()
        context = plusginExcuteContext.get_context()

        # 只处理文本消息且来自群聊
        if message.local_type != MessageType.Text:
            return

        if not message.room or not hasattr(message, 'content'):
            return

        # 检查是否包含触发关键词
        trigger_keyword = self.get_plugin_config("trigger_keyword")
        if not hasattr(message, 'content') or trigger_keyword not in str(message.content):
            return

        self.logger.info(f"检测到查询请求: {message.content}")

        # 解析查询参数
        limit, hours = self._parse_query_params(str(message.content))

        try:
            # 查询群聊消息
            room_username = message.room.username
            messages = await self._query_room_history(room_username, limit, hours)

            # 格式化输出
            result_text = self._format_messages(messages, room_username, limit, hours)

            # 将查询结果存储到上下文中供下一个插件使用
            context['chat_history'] = result_text

            self.logger.info(f"查询到 {len(messages)} 条消息，{context['chat_history']}已传递给下一个插件")

        except Exception as e:
            self.logger.error(f"查询群聊记录时出错: {e}", exc_info=True)
            # 发生错误时，将错误信息存储到上下文
            context['room_message_query_error'] = str(e)
            plusginExcuteContext.add_error(self.name, str(e))

    def _parse_query_params(self, content: str) -> tuple[Optional[int], Optional[int]]:
        """
        解析查询参数

        Args:
            content: 消息内容

        Returns:
            (limit, hours): 消息条数和时间范围（小时）
        """
        trigger_keyword = self.get_plugin_config("trigger_keyword")
        default_limit = self.get_plugin_config("default_limit")
        default_hours = self.get_plugin_config("default_hours")

        # 移除触发关键词
        params = content.replace(trigger_keyword, "").strip()

        if not params:
            # 使用默认配置
            return default_limit, default_hours

        # 尝试解析参数
        limit = None
        hours = None

        # 检查是否包含"小时"
        if "小时" in params or "h" in params.lower() or "hour" in params.lower():
            # 提取数字
            import re
            numbers = re.findall(r'\d+', params)
            if numbers:
                hours = int(numbers[0])
                limit = None
        else:
            # 假设是消息条数
            import re
            numbers = re.findall(r'\d+', params)
            if numbers:
                limit = int(numbers[0])
                hours = None
            else:
                # 默认配置
                limit = default_limit
                hours = default_hours

        # 如果都没有，使用默认
        if limit is None and hours is None:
            limit = default_limit
            hours = default_hours

        return limit, hours

    async def _query_room_history(
        self,
        room_username: str,
        limit: Optional[int],
        hours: Optional[int]
    ) -> list:
        """
        查询群聊历史记录

        Args:
            room_username: 群组username
            limit: 消息条数限制
            hours: 时间范围（小时）

        Returns:
            消息列表
        """
        time_range = None
        query_limit = limit if limit else 500  # 如果只指定时间，限制最多500条

        if hours:
            time_range = timedelta(hours=hours)

        # 使用message_query服务查询
        messages = query_room_messages(
            room_username,
            time_range=time_range,
            limit=query_limit,
            bot=self.bot
        )

        return messages

    def _format_messages(
        self,
        messages: list,
        room_username: str,
        limit: Optional[int],
        hours: Optional[int]
    ) -> str:
        """
        格式化消息为文本

        Args:
            messages: 消息列表
            room_username: 群组username
            limit: 查询的消息条数
            hours: 查询的时间范围

        Returns:
            格式化后的文本
        """
        if not messages:
            return "未找到符合条件的消息记录"

        # 构建标题
        query_desc = f"最近{limit}条消息" if limit else f"最近{hours}小时的消息"
        lines = [
            f"=== 群聊记录查询结果 ===",
            f"群组: {room_username}",
            f"查询条件: {query_desc}",
            f"共找到 {len(messages)} 条消息",
            "=" * 50,
            ""
        ]

        # 添加消息内容
        for msg in messages:
            try:
                # 获取发送者
                sender = msg.contact.display_name if msg.contact else "未知"

                # 获取消息内容
                if hasattr(msg, 'to_text'):
                    content = msg.to_text()
                else:
                    content = str(msg)

                # 确保 content 是字符串类型
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                else:
                    content = str(content)

                # 格式化时间
                time_str = msg.str_time if hasattr(msg, 'str_time') else ""

                # 限制单条消息长度，避免过长
                if len(content) > 200:
                    content = content[:200] + "..."

                lines.append(f"[{time_str}] {sender}: {content}")

            except Exception as e:
                self.logger.warning(f"格式化消息时出错: {e}")
                continue

        lines.append("")
        lines.append("=" * 50)

        result = "\n".join(lines)

        # 如果结果太长，截断
        max_length = 5000
        if len(result) > max_length:
            result = result[:max_length] + "\n...\n（消息过长已截断）"

        return result

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "群聊消息查询插件，可通过关键词触发查询指定群组的历史聊天记录，并将结果传递给下一个插件"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类
        """
        return RoomMessageQueryPluginConfig
