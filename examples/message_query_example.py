"""
示例：如何使用消息查询功能
"""
from datetime import timedelta
from omni_bot_sdk.utils.message_query import query_room_messages, get_room_message_count
from omni_bot_sdk.weixin.message_classes import MessageType

def main():
    # 示例1：获取群聊"测试群"最近1小时的文本消息
    messages = query_room_messages(
        "测试群",
        message_types=[MessageType.Text],
        time_range=timedelta(hours=1)
    )
    print(f"最近1小时的文本消息数量: {len(messages)}")
    for msg in messages:
        print(f"[{msg.str_time}] {msg.contact.display_name}: {msg.content}")
    
    # 示例2：搜索包含特定关键词的消息
    messages = query_room_messages(
        "测试群",
        keywords=["重要", "通知"],
        time_range=timedelta(days=7),
        limit=10
    )
    print(f"\n最近7天包含'重要'或'通知'的消息:")
    for msg in messages:
        print(f"[{msg.str_time}] {msg.contact.display_name}: {msg.content}")
    
    # 示例3：获取特定用户的图片消息数量
    count = get_room_message_count(
        "测试群",
        message_types=[MessageType.Image],
        sender_username="wxid_example",
        time_range=timedelta(days=30)
    )
    print(f"\n用户wxid_example最近30天发送的图片数量: {count}")
    
    # 示例4：分页获取消息
    page_size = 20
    for page in range(3):  # 获取前3页
        messages = query_room_messages(
            "测试群",
            limit=page_size,
            offset=page * page_size
        )
        print(f"\n第{page + 1}页消息:")
        for msg in messages:
            print(f"[{msg.str_time}] {msg.contact.display_name}: {msg.content}")

if __name__ == "__main__":
    main()