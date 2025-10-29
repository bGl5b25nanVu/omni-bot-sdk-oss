"""
测试群聊消息查询插件

此脚本演示如何使用群聊消息查询插件
"""
import asyncio
import os
import sys
from omni_bot_sdk.bot import Bot
sys.path.insert(0, os.path.abspath(os.getcwd()))

def main():
    """
    测试群聊消息查询插件的主函数
    """
    print("=== 测试群聊消息查询插件 ===")
    print("请确保config.yaml中已配置room-message-query-plugin")
    print()

    # 初始化Bot（确保config.yaml中启用了插件）
    bot = Bot(config_path="./config.yaml")

    print("Bot已启动，插件已加载")
    print()
    print("使用说明：")
    print("1. 在微信群聊中发送: '查询聊天记录'")
    print("   - 将使用默认配置查询聊天记录")
    print()
    print("2. 在微信群聊中发送: '查询聊天记录 100'")
    print("   - 将查询最近100条消息")
    print()
    print("3. 在微信群聊中发送: '查询聊天记录 12小时'")
    print("   - 将查询最近12小时的消息")
    print()
    print("注意：")
    print("- room-message-query-plugin 会将查询结果传递给下一个插件")
    print("- 需要配置其他插件（如 openai-bot-plugin）来处理查询结果")
    print("- 查看日志以确认查询结果已正确传递")
    print()
    print("按 Ctrl+C 停止...")

    try:
        # 保持运行，让Bot处理消息
        bot.start()
    except KeyboardInterrupt:
        print("\n正在停止...")
        bot.teardown()
        print("已停止")


if __name__ == "__main__":
    main()
