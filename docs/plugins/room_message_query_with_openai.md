# 使用 RoomMessageQueryPlugin 配合 OpenAI 插件

## 概述

`room-message-query-plugin` 现在完全支持与 `openai-bot-plugin` 配合使用，实现查询历史聊天记录并让 AI 自动分析的功能。

## 工作原理

### 完整流程

```
用户发送: "查询聊天记录"
    ↓
room-message-query-plugin:
  1. 检测触发关键词
  2. 查询数据库获取历史消息
  3. 转换为 JSON 格式（ChatContextPlugin 兼容）
  4. 添加分析提示到末尾
  5. 设置 context['chat_history'] = JSON 字符串
  6. 设置 context['not_for_bot'] = False
    ↓
openai-bot-plugin:
  1. 检查 not_for_bot（False，继续处理）
  2. 读取 context['chat_history']
  3. 解析 JSON
  4. 构建 AI prompt
  5. 调用 OpenAI API
  6. 返回分析结果
    ↓
用户收到: AI 对历史消息的分析
```

### 关键机制

#### 1. JSON 格式兼容

```json
[
  {"speaker_name": "张三", "content": "你好", "is_bot": false},
  {"speaker_name": "李四", "content": "大家好", "is_bot": false},
  {"speaker_name": "用户", "content": "请分析以上聊天记录，总结主要讨论内容和关键信息。", "is_bot": false}
]
```

**注意**: 最后一条是自动添加的分析提示，引导 AI 进行分析。

#### 2. not_for_bot 控制

```python
context.context['not_for_bot'] = False
```

**作用**: 确保 openai-bot-plugin 会处理这个消息，即使原始消息没有 @机器人。

#### 3. 分析提示

默认提示: `"请分析以上聊天记录，总结主要讨论内容和关键信息。"`

可以通过配置自定义。

## 配置示例

### 完整配置

```yaml
# config.yaml

plugins:
  # 查询插件 - 负责查询历史并准备数据
  room-message-query-plugin:
    enabled: true
    priority: 50  # 高优先级，确保先执行
    trigger_keyword: "查询聊天记录"
    default_limit: 50  # 默认查询 50 条消息
    default_hours: 24  # 或默认查询 24 小时内的消息
    analysis_prompt: "请分析以上聊天记录，总结主要讨论内容、关键决策和待办事项。"

  # OpenAI 插件 - 负责 AI 分析
  openai-bot-plugin:
    enabled: true
    priority: 40  # 低优先级，在查询插件之后执行
    api_key: "your-openai-api-key"
    model: "gpt-4"
    # 其他 OpenAI 配置...
```

### 最小配置

```yaml
plugins:
  room-message-query-plugin:
    enabled: true
    priority: 50

  openai-bot-plugin:
    enabled: true
    priority: 40
```

## 使用方式

### 基本用法

在群聊中发送：
```
查询聊天记录
```

AI 将分析最近的聊天记录并返回摘要。

### 指定查询条数

```
查询聊天记录 100
```

查询最近 100 条消息。

### 指定查询时间范围

```
查询聊天记录 12小时
```

查询最近 12 小时的消息。

## 自定义分析提示

### 通过配置自定义

```yaml
room-message-query-plugin:
  analysis_prompt: "请分析聊天记录，重点关注：1）主要话题 2）参与者观点 3）未解决的问题"
```

### 常用提示模板

**会议总结**:
```yaml
analysis_prompt: "请总结这次会议的主要讨论内容、决策结果和行动计划。"
```

**问题收集**:
```yaml
analysis_prompt: "请列出聊天记录中提到的所有问题和疑问。"
```

**待办事项**:
```yaml
analysis_prompt: "请从聊天记录中提取所有待办事项和任务分配。"
```

**情感分析**:
```yaml
analysis_prompt: "请分析聊天记录中的整体氛围和参与者的情绪倾向。"
```

**技术讨论**:
```yaml
analysis_prompt: "请总结技术讨论的核心方案、争议点和最终结论。"
```

## 验证配置

### 1. 检查插件加载

启动 bot 后，查看日志：

```
INFO - plugin_manager:106 - 插件加载完成，执行顺序:
  ... -> room-message-query-plugin -> openai-bot-plugin
```

**验证**: room-message-query-plugin 应该在 openai-bot-plugin 之前。

### 2. 测试查询

在群聊中发送 `查询聊天记录`，观察日志：

```
INFO - room_message_query_plugin:123 - 查询到 18 条消息，已添加分析提示并传递给 AI 插件
DEBUG - room_message_query_plugin:124 - 聊天历史: 18 条历史消息 + 1 条分析提示，not_for_bot=False
INFO - openai_bot_plugin - 开始处理聊天历史...
INFO - openai_bot_plugin - AI 分析完成
```

### 3. 检查返回结果

用户应该收到类似这样的 AI 回复：

```
根据聊天记录分析：

主要讨论内容：
1. 项目进度更新
2. 技术方案讨论
3. 任务分配

关键信息：
- 李四负责前端开发
- 预计下周完成
- 需要协调设计资源

待办事项：
[ ] 李四：完成前端页面
[ ] 张三：准备测试环境
```

## 常见问题

### Q1: AI 没有回复怎么办？

**检查清单**:

1. 确认插件顺序：
   ```
   room-message-query-plugin (priority: 50)
   openai-bot-plugin (priority: 40)
   ```

2. 查看日志是否有：
   ```
   已添加分析提示并传递给 AI 插件
   not_for_bot=False
   ```

3. 确认 openai-bot-plugin 是否被执行

4. 检查 OpenAI API 配置和余额

### Q2: AI 回复的是原始消息而不是分析结果？

**可能原因**: 分析提示没有正确添加。

**解决**: 检查配置中是否设置了 `analysis_prompt`，或使用默认值。

### Q3: 如何让 AI 不分析，只返回原始记录？

**方法 1**: 修改分析提示
```yaml
analysis_prompt: "以下是聊天记录，请简单列出即可，不需要分析。"
```

**方法 2**: 使用纯文本处理插件而不是 AI 插件
```yaml
room-message-query-plugin:
  enabled: true
  priority: 50

room-message-handler-plugin:  # 替代 openai-bot-plugin
  enabled: true
  priority: 40
```

### Q4: 能否同时使用多个分析提示？

**目前不支持**。每次查询只使用一个分析提示。

**变通方案**: 创建多个触发关键词：
```yaml
# 方案A：使用不同的插件实例（需要修改代码）
# 方案B：在配置中添加条件逻辑（需要扩展插件）

# 当前推荐：使用不同的关键词手动切换
# 例如：
# "总结聊天记录" -> 使用总结提示
# "分析问题" -> 使用问题分析提示
```

### Q5: 如何查看传递给 AI 的完整内容？

启用 DEBUG 日志：

```yaml
logging:
  level: DEBUG
```

或在代码中添加：

```python
self.logger.debug(f"chat_history 内容: {chat_history_json[:500]}...")
```

## 高级用法

### 条件触发

根据不同关键词使用不同提示：

```python
# 未来版本可能支持
trigger_configs = {
    "总结聊天": "请总结主要内容",
    "分析问题": "请列出所有问题",
    "提取任务": "请提取所有任务"
}
```

### 多语言支持

```yaml
room-message-query-plugin:
  analysis_prompt: "Please analyze the chat history and provide a summary in English."
```

### 结合其他插件

```yaml
plugins:
  chat-context-plugin:  # 维护实时上下文
    enabled: true
    priority: 1001

  room-message-query-plugin:  # 查询历史
    enabled: true
    priority: 50

  openai-bot-plugin:  # AI 分析
    enabled: true
    priority: 40
```

## 性能优化

### 限制查询范围

```yaml
room-message-query-plugin:
  default_limit: 30  # 减少查询条数
  default_hours: 6   # 缩短时间范围
```

### 缓存机制

未来版本可能支持：
- 查询结果缓存
- 增量查询
- 智能过滤

## 故障排查

### 启用详细日志

```yaml
logging:
  level: DEBUG
  handlers:
    file:
      filename: bot_debug.log
```

### 检查上下文

在 openai-bot-plugin 中添加日志：

```python
self.logger.info(f"上下文keys: {list(context.keys())}")
self.logger.info(f"not_for_bot: {context.get('not_for_bot')}")
self.logger.info(f"chat_history 长度: {len(context.get('chat_history', ''))}")
```

### 测试 JSON 格式

```python
import json
chat_history = json.loads(context.get('chat_history', '[]'))
print(f"消息数量: {len(chat_history)}")
print(f"第一条: {chat_history[0] if chat_history else 'None'}")
print(f"最后一条: {chat_history[-1] if chat_history else 'None'}")
```

## 相关文档

- [JSON 格式详细说明](room_message_query_json_format.md)
- [插件使用指南](room_message_query_plugin_usage.md)
- [问题排查](TROUBLESHOOTING_room_message_query.md)
- [修改日志](CHANGELOG_room_message_query_plugin.md)
