# 快速测试指南：RoomMessageQueryPlugin + OpenAI

## 5 分钟快速测试

### 1. 检查配置文件

确认 `config.yaml` 包含：

```yaml
plugins:
  room-message-query-plugin:
    enabled: true
    priority: 50
    trigger_keyword: "查询聊天记录"
    default_limit: 20
    analysis_prompt: "请分析以上聊天记录，总结主要讨论内容和关键信息。"

  openai-bot-plugin:
    enabled: true
    priority: 40
```

### 2. 启动 Bot

```bash
cd E:\code\GitHub\omni-bot-sdk-oss
.venv\Scripts\python.exe examples\test_room_message_query_plugin.py
```

### 3. 检查启动日志

**成功标志**:
```
✅ 成功加载并实例化插件: room-message-query-plugin
✅ 成功加载并实例化插件: openai-bot-plugin
✅ 插件加载完成，执行顺序: ... -> room-message-query-plugin -> openai-bot-plugin
✅ Bot Setup Complete. All services are running.
```

### 4. 测试查询

在微信群聊中发送：
```
查询聊天记录
```

### 5. 观察日志输出

**预期日志顺序**:

```
1️⃣ 检测到触发词:
INFO - room_message_query_plugin:88 - 检测到查询请求: 查询聊天记录

2️⃣ 查询完成:
INFO - room_message_query_plugin:123 - 查询到 X 条消息，已添加分析提示并传递给 AI 插件

3️⃣ AI 处理:
DEBUG - room_message_query_plugin:124 - 聊天历史: X 条历史消息 + 1 条分析提示，not_for_bot=False
INFO - openai_bot_plugin - 开始处理...

4️⃣ 返回结果:
INFO - openai_bot_plugin - AI 回复已发送
```

### 6. 验证结果

**成功**: 用户在群聊中收到 AI 对历史消息的分析回复

**示例回复**:
```
根据聊天记录分析：

主要讨论内容：
1. XXX
2. YYY

关键信息：
- AAA
- BBB

待办事项：
[ ] CCC
```

## 故障排查清单

### 问题 1: 没有任何响应

**检查**:
- [ ] room-message-query-plugin 是否启用？
- [ ] 触发关键词是否正确？
- [ ] 消息是否在群聊中发送？

**日志查找**:
```
❌ 如果没有: "检测到查询请求"
→ 检查触发关键词配置

❌ 如果没有: "查询到 X 条消息"
→ 检查数据库和查询逻辑
```

### 问题 2: 查询成功但 AI 不回复

**检查**:
- [ ] openai-bot-plugin 是否启用？
- [ ] 优先级是否正确（查询插件 > AI 插件）？
- [ ] OpenAI API key 是否有效？

**日志查找**:
```
✅ 有: "已添加分析提示并传递给 AI 插件"
✅ 有: "not_for_bot=False"
❌ 但没有 AI 插件的日志
→ 检查 openai-bot-plugin 配置
```

### 问题 3: AI 回复了但内容不对

**检查**:
- [ ] 分析提示是否正确设置？
- [ ] JSON 格式是否正确？

**验证方法**:
```python
# 在 openai-bot-plugin 中添加日志
import json
chat_history = json.loads(context.get('chat_history', '[]'))
print(f"消息数量: {len(chat_history)}")
print(f"最后一条: {chat_history[-1]}")  # 应该是分析提示
```

### 问题 4: 格式化错误

**日志标志**:
```
❌ WARNING - 格式化消息时出错: can't concat str to bytes
```

**已修复**: 最新版本已处理 bytes 类型转换

**验证**: 重新安装或确认使用最新代码

### 问题 5: 插件执行顺序错误

**日志查找**:
```
插件加载完成，执行顺序: ... -> openai-bot-plugin -> room-message-query-plugin
```

**问题**: 顺序反了

**修复**:
```yaml
room-message-query-plugin:
  priority: 50  # 更高优先级

openai-bot-plugin:
  priority: 40  # 更低优先级
```

## 详细日志分析

### 完整成功日志示例

```
# 1. 消息到达
23:57:53.362 - INFO - message_service:84 - 新消息插入队列

# 2. 检测触发
23:57:53.388 - INFO - room_message_query_plugin:88 - 检测到查询请求: 查询聊天记录

# 3. 查询数据库
23:57:53.399 - INFO - room_message_query_plugin:123 - 查询到 18 条消息，已添加分析提示并传递给 AI 插件
23:57:53.400 - DEBUG - room_message_query_plugin:124 - 聊天历史: 18 条历史消息 + 1 条分析提示，not_for_bot=False

# 4. 插件链完成
23:57:53.400 - INFO - plugin_manager:133 - 插件处理消息完成

# 5. AI 处理（openai-bot-plugin 的日志）
23:57:53.500 - INFO - openai_bot_plugin - 接收到 chat_history，开始分析
23:57:55.000 - INFO - openai_bot_plugin - AI 分析完成，正在发送回复

# 6. RPA 发送消息
23:57:55.100 - INFO - rpa_service - 执行 SendTextMessageAction
```

## 调试命令

### 启用 DEBUG 日志

```yaml
# config.yaml
logging:
  level: DEBUG
```

### 手动测试 JSON 格式

```bash
.venv\Scripts\python.exe -c "
import json
test_data = [
    {'speaker_name': '测试', 'content': '你好', 'is_bot': False},
    {'speaker_name': '用户', 'content': '请分析以上聊天记录', 'is_bot': False}
]
print(json.dumps(test_data, ensure_ascii=False))
"
```

### 检查插件加载

```bash
.venv\Scripts\python.exe -c "
from omni_bot_sdk.bot import Bot
bot = Bot(config_path='./config.yaml')
bot.setup()
print('插件列表:', [p.get_plugin_name() for p in bot.plugin_manager.plugins])
"
```

## 成功指标

### ✅ 完全成功

- [x] 检测到触发词
- [x] 成功查询消息
- [x] 转换为 JSON 格式
- [x] 设置 not_for_bot=False
- [x] AI 插件处理
- [x] 用户收到分析回复

### ⚠️ 部分成功

- [x] 查询成功
- [ ] AI 没有回复
→ 检查 openai-bot-plugin

### ❌ 完全失败

- [ ] 没有检测到触发词
→ 检查配置和触发词

## 下一步

成功后可以尝试：

1. **自定义分析提示**
   ```yaml
   analysis_prompt: "请总结会议要点和行动项"
   ```

2. **调整查询范围**
   ```yaml
   default_limit: 100
   default_hours: 48
   ```

3. **测试不同命令**
   ```
   查询聊天记录 50
   查询聊天记录 6小时
   ```

## 需要帮助？

1. 查看完整文档: `docs/plugins/room_message_query_with_openai.md`
2. 检查 JSON 格式: `docs/plugins/room_message_query_json_format.md`
3. 故障排查: `docs/plugins/TROUBLESHOOTING_room_message_query.md`
