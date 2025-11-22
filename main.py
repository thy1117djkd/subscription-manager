#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代理订阅管理工具 - 主程序入口
支持订阅管理、节点测试、配置导出等功能
"""

import asyncio
import argparse
from src.core.subscription import SubscriptionManager
from src.core.tester import ProxyTester
from src.web.app import create_app
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='代理订阅管理工具')
    parser.add_argument('--web', action='store_true', help='启动Web服务')
    parser.add_argument('--test', action='store_true', help='测试所有节点')
    parser.add_argument('--update', action='store_true', help='更新订阅')
    parser.add_argument('--add', type=str, help='添加订阅URL')
    parser.add_argument('--export', type=str, help='导出配置格式: clash/v2ray/surge')
    parser.add_argument('--host', default='0.0.0.0', help='Web服务地址')
    parser.add_argument('--port', type=int, default=5000, help='Web服务端口')
    return parser.parse_args()


async def test_nodes():
    """测试所有节点"""
    logger.info("开始测试节点...")
    tester = ProxyTester()
    results = await tester.test_all_nodes()

    print("\n" + "=" * 60)
    print("节点测试结果".center(60))
    print("=" * 60)

    for result in results:
        status = "✓" if result['available'] else "✗"
        delay = f"{result['delay']}ms" if result['available'] else "超时"
        print(f"{status} {result['name']:<30} {delay:>10}")

    print("=" * 60)


async def update_subscriptions():
    """更新所有订阅"""
    logger.info("开始更新订阅...")
    manager = SubscriptionManager()
    await manager.update_all()
    print("订阅更新完成！")


def start_web_server(host, port):
    """启动Web服务"""
    logger.info(f"启动Web服务: http://{host}:{port}")
    app = create_app()
    app.run(host=host, port=port, debug=False)


async def main():
    """主函数"""
    args = parse_args()

    if args.add:
        manager = SubscriptionManager()
        await manager.add_subscription(args.add)
        print(f"已添加订阅: {args.add}")

    elif args.update:
        await update_subscriptions()

    elif args.test:
        await test_nodes()

    elif args.export:
        manager = SubscriptionManager()
        config = await manager.export_config(args.export)
        print(f"配置已导出为 {args.export} 格式")
        print(config)

    elif args.web:
        start_web_server(args.host, args.port)

    else:
        print("代理订阅管理工具")
        print("使用 --help 查看帮助信息")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序已停止")
    except Exception as e:
        logger.error(f"程序出错: {e}")
