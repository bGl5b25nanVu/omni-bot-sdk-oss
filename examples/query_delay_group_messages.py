"""
测试查询"迟到组"最近一天的消息
"""
import asyncio
from datetime import timedelta
from omni_bot_sdk.bot import Bot
from omni_bot_sdk.services.functional.message_query import query_room_messages
from omni_bot_sdk.weixin.message_classes import MessageType

async def main():
    # 初始化Bot
    bot = Bot()
    bot.setup()
    
    print("开始查询迟到组最近一天的消息...")
    
    # 查询所有类型的消息
    messages = query_room_messages(
        "迟到组",
        time_range=timedelta(days=1),
        limit=100  # 最多返回100条
    )
    
    print(f"\n找到 {len(messages)} 条消息:")
    print("-" * 50)
    
    for msg in messages:
        # 格式化时间和发送者
        sender = msg.contact.display_name if msg.contact else "未知"

        # 使用to_text()方法获取消息内容
        try:
            content = msg.to_text() if hasattr(msg, 'to_text') else str(msg)
        except Exception as e:
            content = f"[无法解析消息: {e}]"

        print(f"{msg.str_time} | {sender}: {content}")
    
    print("-" * 50)
    
    # 按类型统计消息数量
    message_types = [MessageType.Text, MessageType.Image, MessageType.Video, 
                    MessageType.Audio, MessageType.Emoji]
    
    print("\n按类型统计：")
    for msg_type in message_types:
        count = len([m for m in messages if m.local_type == msg_type])
        print(f"{MessageType.name(msg_type)}: {count}条")
    
    bot.teardown()

if __name__ == "__main__":
    asyncio.run(main())