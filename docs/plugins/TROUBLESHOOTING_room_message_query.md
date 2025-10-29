# RoomMessageQueryPlugin 问题排查指南

## 问题：查询结果没有传递给下一个插件

### 症状

日志显示：
```
23:57:53.399 - INFO - room_message_query_plugin:111 - 查询到 18 条消息，已传递给下一个插件
23:57:53.400 - INFO - plugin_manager:133 - 插件处理消息完成
```

但 openai-bot-plugin 或其他后续插件没有处理查询结果。

### 根本原因

已修复的两个关键问题：

#### 1. 格式化错误（已修复）

**错误日志**:
```
WARNING - room_message_query_plugin:272 - 格式化消息时出错: can't concat str to bytes
```

**原因**: 消息内容可能是 bytes 类型，直接切片后与字符串 `"..."` 拼接导致类型错误。

**修复**: 在 `_format_messages` 方法中添加类型检查和转换：
```python
# 确保 content 是字符串类型
if isinstance(content, bytes):
    content = content.decode('utf-8', errors='ignore')
else:
    content = str(content)
```

#### 2. should_stop 标志没有生效（已修复）

**原因**: `PluginExcuteContext.add_response()` 方法没有检查插件响应中的 `should_stop` 标志并更新上下文。

**修复**: 修改 `add_response` 方法：
```python
def add_response(self, value: PluginExcuteResponse):
    self.responses.append(value)
    # 如果插件响应要求停止，更新上下文的 should_stop 标志
    if value.should_stop:
        self.should_stop = True
```

### 为什么 openai-bot-plugin 仍然没有处理

**关键问题**: openai-bot-plugin 可能不会自动读取上下文中的 `room_message_query_result`。

大多数插件默认只处理消息内容本身，不会检查上下文中的额外数据。需要以下任一方案：

## 解决方案

### 方案 1: 使用简单的处理插件（推荐）

使用我们提供的示例处理插件：

1. **配置 room-message-handler-plugin**:
   ```yaml
   # config.yaml
   plugins:
     room-message-query-plugin:
       enabled: true
       priority: 50  # 先执行

     room-message-handler-plugin:
       enabled: true
       priority: 40  # 后执行，读取查询结果并发送
   ```

2. **在 pyproject.toml 中注册插件**:
   ```toml
   [project.entry-points."omni_bot.plugins"]
   room-message-handler-plugin = "examples.room_message_handler_plugin:RoomMessageHandlerPlugin"
   ```

3. **重新安装包**:
   ```bash
   pip install -e .
   ```

### 方案 2: 修改 openai-bot-plugin 支持上下文

如果你想让 openai-bot-plugin 处理查询结果，需要修改它的代码：

```python
class OpenAIBotPlugin(Plugin):
    async def handle_message(self, context: PluginExcuteContext) -> None:
        message = context.get_message()

        # 检查是否有查询结果
        query_result = context.context.get('room_message_query_result')

        if query_result:
            # 有查询结果，使用 AI 分析
            formatted_text = query_result.get('formatted_text', '')

            # 构建 AI 提示词
            prompt = f"""请分析以下群聊记录：

{formatted_text}

请提供：
1. 主要讨论话题
2. 活跃用户
3. 关键信息摘要
"""

            # 调用 AI API
            ai_response = await self.call_openai_api(prompt)

            # 发送 AI 分析结果
            send_action = SendTextMessageAction(
                target=message.room.username,
                content=f"📊 AI 分析结果:\n\n{ai_response}",
                is_chatroom=True
            )
            self.add_rpa_action(send_action)
            return

        # 正常处理消息
        # ... 原有逻辑
```

### 方案 3: 使用测试插件验证

使用我们提供的测试插件确认数据传递正常：

1. **注册测试插件**:
   ```toml
   [project.entry-points."omni_bot.plugins"]
   test-handler-plugin = "examples.test_context_passing:TestHandlerPlugin"
   ```

2. **配置测试插件**:
   ```yaml
   plugins:
     room-message-query-plugin:
       enabled: true
       priority: 50

     test-handler-plugin:
       enabled: true
       priority: 30
   ```

3. **运行测试并查看日志**:
   ```
   ===== TestHandlerPlugin 开始处理 =====
   ✅ 成功接收到查询结果!
     - 消息数量: 18
     - 群组: ...
   ```

## 验证修复

### 1. 检查格式化错误是否消失

运行 bot 后，发送 "查询聊天记录"，检查日志：

**修复前**:
```
WARNING - room_message_query_plugin:272 - 格式化消息时出错: can't concat str to bytes
```

**修复后**:
应该没有这个警告，或者显著减少。

### 2. 检查插件执行流程

启用 debug 日志：

```python
# bot.py 或 config.yaml
logging:
  level: DEBUG
```

应该看到：
```
DEBUG - plugin_manager - 插件 'room-message-query-plugin' 处理完成。
DEBUG - plugin_manager - 插件 'your-next-plugin' 处理完成。
```

### 3. 检查上下文数据

在你的处理插件中添加日志：

```python
async def handle_message(self, context: PluginExcuteContext) -> None:
    self.logger.info(f"上下文keys: {list(context.context.keys())}")
    query_result = context.context.get('room_message_query_result')
    if query_result:
        self.logger.info(f"接收到 {query_result.get('message_count')} 条消息")
```

## 常见问题

### Q1: 为什么插件链没有继续执行？

**检查**:
- 确保 room-message-query-plugin 设置 `should_stop=False`
- 检查是否有其他插件设置了 `should_stop=True`
- 查看插件优先级顺序

### Q2: 为什么下一个插件收不到数据？

**检查**:
- 确认数据已存入上下文（查看日志）
- 确认下一个插件有检查 `context.context['room_message_query_result']`
- 确认插件确实被执行了（查看日志）

### Q3: 如何知道哪个插件先执行？

**查看启动日志**:
```
INFO - plugin_manager:106 - 插件加载完成，执行顺序:
  block-empty-room-plugin -> image-aes-plugin -> self-msg-plugin ->
  room-message-query-plugin -> openai-bot-plugin
```

优先级高的先执行。

## 最佳实践

1. **明确职责**: 查询插件只查询，处理插件负责发送
2. **使用日志**: 在关键点添加日志确认数据流转
3. **测试验证**: 使用测试插件验证数据传递
4. **文档化**: 记录你的插件如何使用上下文数据

## 相关文档

- [RoomMessageQueryPlugin 使用说明](room_message_query_plugin_usage.md)
- [修改日志](CHANGELOG_room_message_query_plugin.md)
- 示例代码: `examples/room_message_handler_plugin.py`
- 测试代码: `examples/test_context_passing.py`
