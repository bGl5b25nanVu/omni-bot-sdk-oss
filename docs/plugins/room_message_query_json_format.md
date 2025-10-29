# RoomMessageQueryPlugin JSON 格式说明

## 概述

`room-message-query-plugin` 现在将查询到的聊天记录转换为与 `ChatContextPlugin` 完全兼容的 JSON 格式，存储在 `context.context['chat_history']` 中。

这样 `openai-bot-plugin` 和其他期望标准聊天历史格式的插件可以直接使用。

## JSON 格式

### 格式结构

```json
[
  {
    "speaker_name": "张三",
    "content": "大家好，今天讨论什么？",
    "is_bot": false
  },
  {
    "speaker_name": "AI助手",
    "content": "你好！有什么可以帮你的吗？",
    "is_bot": true
  },
  {
    "speaker_name": "李四",
    "content": "我们来讨论一下新项目吧",
    "is_bot": false
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `speaker_name` | string | 发送者的显示名称 |
| `content` | string | 消息内容（纯文本） |
| `is_bot` | boolean | 是否是 bot 自己发送的消息 |

### 存储位置

```python
context.context['chat_history']  # JSON 字符串
```

## 与 ChatContextPlugin 的兼容性

### 格式对比

**ChatContextPlugin 生成的格式**:
```python
{
    "speaker_name": sender,
    "content": str(content or ""),
    "is_bot": message.is_self,
}
```

**RoomMessageQueryPlugin 生成的格式**:
```python
{
    "speaker_name": speaker_name,
    "content": content,
    "is_bot": is_bot
}
```

✅ **完全兼容！** 两个插件生成的格式完全相同，可以互换使用。

## 使用示例

### 查询并分析

当用户在群聊中发送 "查询聊天记录" 后：

1. **room-message-query-plugin** 查询数据库
2. 转换为 JSON 格式
3. 存入 `context.context['chat_history']`
4. **openai-bot-plugin** 读取并分析

### 在插件中读取

```python
class YourPlugin(Plugin):
    async def handle_message(self, context: PluginExcuteContext) -> None:
        # 读取 JSON 格式的聊天历史
        chat_history_json = context.context.get('chat_history')

        if chat_history_json:
            import json
            chat_history = json.loads(chat_history_json)

            # 遍历所有消息
            for msg in chat_history:
                speaker = msg['speaker_name']
                content = msg['content']
                is_bot = msg['is_bot']

                print(f"{speaker}: {content}")
```

## 完整示例

### 输入

用户发送: `查询聊天记录 10`

### 查询结果（数据库）

```python
[
  Message(contact=Contact(display_name="张三"), content="你好", is_self=False),
  Message(contact=Contact(display_name="李四"), content="大家好", is_self=False),
  Message(contact=Contact(display_name="AI助手"), content="有什么可以帮你？", is_self=True),
]
```

### 转换后（JSON）

```json
[
  {
    "speaker_name": "张三",
    "content": "你好",
    "is_bot": false
  },
  {
    "speaker_name": "李四",
    "content": "大家好",
    "is_bot": false
  },
  {
    "speaker_name": "AI助手",
    "content": "有什么可以帮你？",
    "is_bot": true
  }
]
```

### 存储

```python
context.context['chat_history'] = '[{"speaker_name":"张三","content":"你好","is_bot":false},...'
```

### OpenAI Bot 处理

openai-bot-plugin 会自动：
1. 读取 `context.context['chat_history']`
2. 解析 JSON
3. 构建 prompt 发送给 AI
4. 返回分析结果

## 日志输出

### 成功日志

```
INFO - room_message_query_plugin:106 - 查询到 18 条消息，已转换为 JSON 格式并传递给下一个插件
DEBUG - room_message_query_plugin:107 - 聊天历史格式: 18 条消息
```

### 调试验证

启用 DEBUG 日志查看详细格式：

```yaml
# config.yaml
logging:
  level: DEBUG
```

然后在代码中添加：

```python
self.logger.debug(f"chat_history 内容: {chat_history_json[:200]}...")
```

## 与旧格式的对比

### 旧格式（纯文本）

```
=== 群聊记录查询结果 ===
群组: xxx@chatroom
查询条件: 最近50条消息
共找到 18 条消息
==================================================

[2025-10-29 23:57] 张三: 你好
[2025-10-29 23:58] 李四: 大家好
...
```

**问题**:
- openai-bot-plugin 无法解析
- 格式不统一
- 难以程序化处理

### 新格式（JSON）

```json
[
  {"speaker_name": "张三", "content": "你好", "is_bot": false},
  {"speaker_name": "李四", "content": "大家好", "is_bot": false}
]
```

**优势**:
- ✅ 与 ChatContextPlugin 格式一致
- ✅ openai-bot-plugin 可直接使用
- ✅ 易于程序化处理
- ✅ 支持结构化分析

## 常见问题

### Q1: 为什么不保留文本格式？

A: 为了与 openai-bot-plugin 兼容，必须使用 JSON 格式。如果需要文本格式用于其他用途，可以在下游插件中转换。

### Q2: 如何获取旧的文本格式？

A: 可以自己转换：

```python
import json

chat_history_json = context.context.get('chat_history')
chat_history = json.loads(chat_history_json)

# 转换为文本
text_lines = []
for msg in chat_history:
    text_lines.append(f"{msg['speaker_name']}: {msg['content']}")

text_format = "\n".join(text_lines)
```

### Q3: 如何验证格式是否正确？

A: 检查日志中是否有：
- ✅ "已转换为 JSON 格式并传递给下一个插件"
- ✅ openai-bot-plugin 的处理日志
- ❌ 没有 JSON 解析错误

## 配置示例

```yaml
# config.yaml
plugins:
  room-message-query-plugin:
    enabled: true
    priority: 50  # 高优先级，先执行
    trigger_keyword: "查询聊天记录"
    default_limit: 50
    default_hours: 24

  openai-bot-plugin:
    enabled: true
    priority: 40  # 低优先级，后执行
    # openai-bot-plugin 会自动读取 chat_history
```

## 技术细节

### 编码处理

代码会自动处理各种编码情况：

```python
# 如果内容是 bytes
if isinstance(content, bytes):
    content = content.decode('utf-8', errors='ignore')

# 如果内容是 None
content = str(content or "")
```

### 错误处理

如果某条消息转换失败：
- 记录警告日志
- 跳过该消息
- 继续处理其他消息

### JSON 序列化

使用 `ensure_ascii=False` 保持中文可读：

```python
json.dumps(chat_history_array, ensure_ascii=False)
```

输出：
```json
[{"speaker_name":"张三","content":"你好","is_bot":false}]
```

而不是：
```json
[{"speaker_name":"\u5f20\u4e09","content":"\u4f60\u597d","is_bot":false}]
```
