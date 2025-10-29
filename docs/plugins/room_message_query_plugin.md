# 群聊消息查询插件 (Room Message Query Plugin)

## 简介

群聊消息查询插件是一个用于查询群聊历史消息的功能插件。当在群聊中发送特定关键词时，插件会自动查询该群的历史聊天记录并以格式化的文本形式返回。

## 功能特性

- ✅ 支持通过关键词触发查询
- ✅ 支持按消息条数查询（例如：最近100条）
- ✅ 支持按时间范围查询（例如：最近12小时）
- ✅ 自动格式化输出，包含时间、发送者和消息内容
- ✅ 智能过滤，只处理群聊中的文本消息
- ✅ 支持配置化管理

## 安装

插件已集成在 `omni-bot-sdk` 中，无需额外安装。确保你已经安装了最新版本的 SDK：

```bash
pip install -e .
```

## 配置

### 1. 在 config.yaml 中添加插件配置

```yaml
plugins:
  # 群聊消息查询插件
  room-message-query-plugin:
    enabled: true              # 启用插件
    priority: 50               # 插件优先级（数值越大越先执行）
    trigger_keyword: "查询聊天记录"  # 触发查询的关键词
    default_limit: 50          # 默认查询消息条数（1-500）
    default_hours: 24          # 默认查询最近几小时（1-720）
```

### 2. 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `enabled` | boolean | false | 是否启用插件 |
| `priority` | integer | 50 | 插件优先级，数值越大越先执行 |
| `trigger_keyword` | string | "查询聊天记录" | 触发查询的关键词 |
| `default_limit` | integer | 50 | 默认查询的消息条数（范围：1-500） |
| `default_hours` | integer | 24 | 默认查询的时间范围，单位：小时（范围：1-720） |

## 使用方法

### 命令格式

在已配置的微信群聊中发送以下命令：

#### 1. 使用默认配置查询

```
查询聊天记录
```

这将使用配置文件中设置的 `default_limit` 和 `default_hours` 进行查询。

#### 2. 指定消息条数

```
查询聊天记录 100
```

查询该群最近的100条消息。

#### 3. 指定时间范围

支持以下格式：

```
查询聊天记录 12小时
查询聊天记录 12h
查询聊天记录 12hour
```

查询该群最近12小时内的消息。

### 输出格式

插件会返回格式化的文本消息，包含：

```
=== 群聊记录查询结果 ===
群组: 27167423333@chatroom
查询条件: 最近50条消息
共找到 50 条消息
==================================================

[2025-10-29 21:54:50] 张三: 大家好
[2025-10-29 21:53:32] 李四: 今天天气不错
[2025-10-29 21:52:15] 王五: [图片]
...

==================================================
```

## 工作原理

1. **消息监听**: 插件监听所有群聊中的文本消息
2. **关键词匹配**: 检测消息内容是否包含触发关键词
3. **参数解析**: 从消息中提取查询参数（条数或时间范围）
4. **数据查询**: 使用 `message_query` 服务查询历史消息
5. **格式化输出**: 将查询结果格式化为易读的文本
6. **发送回复**: 通过 RPA 服务将结果发送到群聊

## 代码示例

### 基本使用

```python
from omni_bot_sdk.bot import Bot

# 初始化Bot（确保config.yaml中已配置插件）
bot = Bot()
bot.setup()

# 启动Bot，开始监听消息
bot.start()
```

### 在插件中使用消息查询服务

```python
from omni_bot_sdk.services.functional.message_query import query_room_messages
from datetime import timedelta

# 查询指定群组的消息
messages = query_room_messages(
    room_username="27167423333@chatroom",  # 群组username
    time_range=timedelta(hours=12),        # 查询最近12小时
    limit=100,                              # 最多返回100条
    bot=bot                                 # Bot实例
)

# 处理查询结果
for msg in messages:
    print(f"{msg.str_time} | {msg.contact.display_name}: {msg.to_text()}")
```

## 技术细节

### 依赖服务

- `DatabaseService`: 用于访问聊天数据库
- `MessageQueryService`: 提供消息查询功能
- `RPAService`: 用于发送回复消息

### 消息过滤

插件只处理满足以下条件的消息：
- 消息类型为文本 (`MessageType.Text`)
- 消息来自群聊（`message.room` 存在）
- 消息内容包含触发关键词

### 性能优化

- 使用异步处理，不阻塞消息流
- 限制单次查询最多500条消息
- 限制输出文本长度，避免消息过长

## 故障排除

### 插件未响应

1. 检查 `config.yaml` 中插件是否启用（`enabled: true`）
2. 确认触发关键词正确
3. 查看日志，确认插件是否成功加载

### 查询无结果

1. 确认群组有历史消息
2. 检查时间范围和消息条数设置是否合理
3. 查看日志中的错误信息

### 消息格式异常

1. 检查数据库中消息数据完整性
2. 查看日志中的格式化错误

## 相关文件

- 插件代码: `src/omni_bot_sdk/plugins/core/room_message_query_plugin.py`
- 配置示例: `examples/config_room_message_query.yaml`
- 测试脚本: `examples/test_room_message_query_plugin.py`
- 查询服务: `src/omni_bot_sdk/services/functional/message_query_service.py`

## 版本历史

### v1.0.0 (2025-10-29)
- 初始版本
- 支持按条数和时间范围查询
- 支持格式化文本输出
- 集成到 omni-bot-sdk 核心插件

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个插件！

## 许可证

本插件遵循 omni-bot-sdk 的 GPL-3.0 许可证。
