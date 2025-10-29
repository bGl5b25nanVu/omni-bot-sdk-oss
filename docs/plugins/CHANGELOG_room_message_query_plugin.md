# RoomMessageQueryPlugin 修改日志

## 2025-10-29 重大功能调整

### 修改概述

将 `room-message-query-plugin` 从直接发送消息的插件调整为数据传递插件，遵循单一职责原则。

### 主要修改

#### 1. 移除 RPA 操作
- **删除**: `SendTextMessageAction` 导入和使用
- **原因**: 插件职责应该是查询数据，而不是发送消息

#### 2. 数据传递机制
- **新增**: 通过 `context.context` 传递查询结果给下一个插件
- **传递数据结构**:
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

#### 3. 插件链继续执行
- **设置**: `should_stop=False`
- **效果**: 允许后续插件处理查询结果

#### 4. 错误处理优化
- **新增**: 错误信息存储到上下文
  ```python
  context.context['room_message_query_error'] = str(e)
  ```
- **移除**: 错误时的 RPA 发送操作

### 修改后的工作流程

```
用户发送触发词 "查询聊天记录"
    ↓
room-message-query-plugin 查询数据库
    ↓
将查询结果存入 context.context
    ↓
设置 should_stop=False
    ↓
下一个插件接收并处理数据
    ↓
下一个插件决定如何处理（发送、分析等）
```

### 配置建议

需要配置两个插件配合使用：

```yaml
plugins:
  # 查询插件 - 负责查询数据
  room-message-query-plugin:
    enabled: true
    priority: 50  # 较高优先级，先执行
    trigger_keyword: "查询聊天记录"
    default_limit: 50
    default_hours: 24

  # 处理插件 - 负责发送或处理数据
  # 可以是以下任意一个：

  # 选项1: 使用示例的简单发送插件
  room-message-handler-plugin:
    enabled: true
    priority: 40  # 较低优先级，后执行

  # 选项2: 使用 OpenAI 插件进行 AI 分析
  openai-bot-plugin:
    enabled: true
    priority: 40
    # OpenAI 会读取 context 中的查询结果并进行分析
```

### 优势

1. **职责分离**: 查询和展示逻辑分离
2. **灵活性**: 可以轻松替换处理插件
3. **可扩展**: 支持多种处理方式（AI 分析、统计、格式化等）
4. **可组合**: 可以多个插件依次处理同一份数据

### 兼容性

**破坏性变更**: 是

- 如果之前依赖此插件直接发送消息，需要额外配置一个处理插件
- 建议使用提供的 `room-message-handler-plugin` 示例插件

### 示例插件

已创建示例插件展示如何使用查询结果：

- **位置**: `examples/room_message_handler_plugin.py`
- **功能**: 接收查询结果并发送到群聊
- **用途**: 作为参考实现或直接使用

### 文档

新增详细使用文档：

- **位置**: `docs/plugins/room_message_query_plugin_usage.md`
- **内容**:
  - 数据结构说明
  - 多个使用示例
  - 配置指南
  - 最佳实践

### 测试

测试脚本已更新：

- **位置**: `examples/test_room_message_query_plugin.py`
- **说明**: 已更新使用说明，提示需要配置处理插件

### 迁移指南

#### 从旧版本迁移

如果你之前使用此插件直接发送消息：

1. **保持现有功能**:
   ```yaml
   # 添加到 config.yaml
   plugins:
     room-message-handler-plugin:
       enabled: true
       priority: 40
   ```

2. **或使用 AI 分析**:
   ```yaml
   # OpenAI 插件会自动读取上下文中的查询结果
   plugins:
     openai-bot-plugin:
       enabled: true
       priority: 40
   ```

3. **或自定义处理**:
   - 参考 `examples/room_message_handler_plugin.py`
   - 创建自己的处理插件

### 未来增强

潜在的改进方向：

1. 支持更多查询条件（发送者、关键词过滤等）
2. 支持导出到不同格式（JSON、CSV、HTML）
3. 支持查询结果缓存
4. 支持分页查询大量消息
