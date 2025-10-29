# RoomMessageQueryPlugin 使用说明

## 功能说明

`room-message-query-plugin` 插件用于查询群聊历史消息，并将查询结果传递给插件链中的下一个插件。

## 工作流程

1. 监听群聊消息，检测触发关键词（默认："查询聊天记录"）
2. 解析查询参数（消息条数或时间范围）
3. 从数据库查询群聊历史消息
4. 将查询结果存储到上下文 (`context.context`) 中
5. 继续执行下一个插件（`should_stop=False`）

## 触发命令

- `查询聊天记录` - 使用默认配置查询
- `查询聊天记录 100` - 查询最近100条消息
- `查询聊天记录 12小时` - 查询最近12小时的消息

## 传递给下一个插件的数据

查询成功后，插件会在 `context.context` 中添加以下数据：

```python
context.context['room_message_query_result'] = {
    'messages': messages,              # 原始消息对象列表
    'formatted_text': result_text,     # 格式化后的文本
    'room_username': room_username,    # 群组username
    'limit': limit,                    # 查询的消息条数限制
    'hours': hours,                    # 查询的时间范围（小时）
    'message_count': len(messages)     # 实际查询到的消息数量
}
```

查询失败时，会在 `context.context` 中添加错误信息：

```python
context.context['room_message_query_error'] = "错误信息"
```

## 下一个插件如何使用这些数据

### 示例 1: 简单使用格式化文本

```python
class MyNextPlugin(Plugin):
    async def handle_message(self, context: PluginExcuteContext) -> None:
        # 检查是否有查询结果
        query_result = context.context.get('room_message_query_result')

        if query_result:
            # 获取格式化的文本
            formatted_text = query_result['formatted_text']
            message_count = query_result['message_count']

            # 进行你的处理，例如发送消息
            self.logger.info(f"收到查询结果，共 {message_count} 条消息")

            # 发送消息给用户
            send_action = SendTextMessageAction(
                target=context.message.room.username,
                content=formatted_text,
                is_chatroom=True
            )
            self.add_rpa_action(send_action)
```

### 示例 2: 处理原始消息对象

```python
class MessageAnalysisPlugin(Plugin):
    async def handle_message(self, context: PluginExcuteContext) -> None:
        query_result = context.context.get('room_message_query_result')

        if query_result:
            messages = query_result['messages']

            # 分析消息
            user_stats = {}
            for msg in messages:
                sender = msg.contact.display_name if msg.contact else "未知"
                user_stats[sender] = user_stats.get(sender, 0) + 1

            # 生成统计报告
            report = "消息统计:\n"
            for user, count in sorted(user_stats.items(), key=lambda x: x[1], reverse=True):
                report += f"{user}: {count}条\n"

            # 发送报告
            send_action = SendTextMessageAction(
                target=context.message.room.username,
                content=report,
                is_chatroom=True
            )
            self.add_rpa_action(send_action)
```

### 示例 3: 使用 AI 处理查询结果

```python
class AIAnalysisPlugin(Plugin):
    async def handle_message(self, context: PluginExcuteContext) -> None:
        query_result = context.context.get('room_message_query_result')

        if query_result:
            formatted_text = query_result['formatted_text']

            # 将聊天记录发送给 AI 进行分析
            ai_response = await self.call_ai_api(
                prompt=f"请分析以下聊天记录:\n{formatted_text}"
            )

            # 发送 AI 分析结果
            send_action = SendTextMessageAction(
                target=context.message.room.username,
                content=f"AI 分析结果:\n{ai_response}",
                is_chatroom=True
            )
            self.add_rpa_action(send_action)
```

## 配置示例

在 `config.yaml` 中配置插件顺序：

```yaml
plugins:
  room-message-query-plugin:
    enabled: true
    priority: 50  # 确保在其他处理插件之前执行
    trigger_keyword: "查询聊天记录"
    default_limit: 50
    default_hours: 24

  my-analysis-plugin:
    enabled: true
    priority: 40  # 优先级低于 room-message-query-plugin
```

## 注意事项

1. **插件执行顺序**: 确保 `room-message-query-plugin` 的优先级高于需要使用查询结果的插件
2. **数据存在性检查**: 下一个插件应该始终检查 `context.context` 中是否存在查询结果
3. **错误处理**: 检查是否存在 `room_message_query_error` 来处理查询失败的情况
4. **资源消耗**: 大量消息查询可能消耗较多资源，建议限制查询范围
5. **继续传递**: 如果你的插件也不发送消息，也可以设置 `should_stop=False` 继续传递给下一个插件
