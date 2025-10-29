"""
示例插件：接收并处理 room-message-query-plugin 的查询结果

这个插件展示了如何接收 room-message-query-plugin 传递的数据，
并将格式化的聊天记录发送回群聊。
"""
from typing import TYPE_CHECKING
from pydantic import BaseModel

from omni_bot_sdk.plugins.core.plugin_interface import (
    Plugin,
    PluginExcuteContext,
    PluginExcuteResponse,
)
from omni_bot_sdk.rpa.action_handlers import SendTextMessageAction

if TYPE_CHECKING:
    from omni_bot_sdk.bot import Bot


class RoomMessageHandlerPluginConfig(BaseModel):
    """
    群聊消息处理插件配置
    """
    enabled: bool = False
    priority: int = 40  # 优先级低于 room-message-query-plugin


class RoomMessageHandlerPlugin(Plugin):
    """
    群聊消息处理插件实现类

    接收 room-message-query-plugin 查询到的消息并发送到群聊
    """

    priority = 40
    name = "room-message-handler-plugin"

    def __init__(self, bot: "Bot" = None):
        super().__init__(bot)
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def get_priority(self) -> int:
        return self.priority

    async def handle_message(self, context: PluginExcuteContext) -> None:
        """
        处理消息的核心方法

        检查上下文中是否有查询结果，如果有则发送到群聊
        """
        # 检查是否有查询结果
        query_result = context.context.get('room_message_query_result')

        if not query_result:
            # 没有查询结果，跳过处理
            return

        # 检查是否有错误
        query_error = context.context.get('room_message_query_error')
        if query_error:
            self.logger.error(f"查询出错: {query_error}")
            error_msg = f"查询聊天记录失败: {query_error}"
            send_action = SendTextMessageAction(
                target=context.message.room.username,
                content=error_msg,
                is_chatroom=True
            )
            self.add_rpa_action(send_action)
            return

        # 获取查询结果
        formatted_text = query_result.get('formatted_text', '')
        message_count = query_result.get('message_count', 0)

        self.logger.info(f"接收到查询结果，共 {message_count} 条消息，准备发送")

        # 发送格式化的聊天记录到群聊
        if formatted_text:
            send_action = SendTextMessageAction(
                target=context.message.room.username,
                content=formatted_text,
                is_chatroom=True
            )
            self.add_rpa_action(send_action)

            # 标记消息已处理
            response = PluginExcuteResponse(
                plugin_name=self.name,
                handled=True,
                should_stop=True,  # 已经处理完成，停止后续插件
                message=context.message
            )
            context.add_response(response)
        else:
            self.logger.warning("查询结果为空，跳过发送")

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "接收并处理 room-message-query-plugin 的查询结果，将聊天记录发送到群聊"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类
        """
        return RoomMessageHandlerPluginConfig
