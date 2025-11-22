#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
订阅管理核心模块
负责订阅的添加、更新、解析和管理
"""

import aiohttp
import asyncio
import base64
import yaml
from typing import List, Dict
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SubscriptionManager:
    """订阅管理器"""

    def __init__(self, db_path='data/subscriptions.db'):
        self.db_path = db_path
        self.subscriptions = []
        self.nodes = []

    async def add_subscription(self, url: str, name: str = None) -> bool:
        """添加订阅"""
        try:
            if name is None:
                name = f"订阅_{len(self.subscriptions) + 1}"

            subscription = {
                'url': url,
                'name': name,
                'added_at': datetime.now().isoformat(),
                'last_update': None,
                'node_count': 0
            }

            self.subscriptions.append(subscription)
            logger.info(f"已添加订阅: {name}")
            return True

        except Exception as e:
            logger.error(f"添加订阅失败: {e}")
            return False

    async def fetch_subscription(self, url: str) -> str:
        """获取订阅内容"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
                else:
                    raise Exception(f"HTTP {response.status}")

    async def parse_subscription(self, content: str) -> List[Dict]:
        """解析订阅内容"""
        nodes = []

        try:
            # 尝试解析为Base64
            try:
                decoded = base64.b64decode(content).decode('utf-8')
                lines = decoded.strip().split('\n')
            except:
                lines = content.strip().split('\n')

            # 解析每一行
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                node = self._parse_node_line(line)
                if node:
                    nodes.append(node)

            logger.info(f"解析到 {len(nodes)} 个节点")
            return nodes

        except Exception as e:
            logger.error(f"解析订阅失败: {e}")
            return []

    def _parse_node_line(self, line: str) -> Dict:
        """解析单个节点配置"""
        # 简化的解析逻辑
        node = {
            'name': 'Unknown',
            'type': 'unknown',
            'server': '',
            'port': 0,
            'config': line
        }

        # 根据协议前缀判断类型
        if line.startswith('vmess://'):
            node['type'] = 'vmess'
        elif line.startswith('ss://'):
            node['type'] = 'shadowsocks'
        elif line.startswith('trojan://'):
            node['type'] = 'trojan'

        return node

    async def update_all(self):
        """更新所有订阅"""
        tasks = []
        for sub in self.subscriptions:
            task = self._update_single(sub)
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _update_single(self, subscription: Dict):
        """更新单个订阅"""
        try:
            content = await self.fetch_subscription(subscription['url'])
            nodes = await self.parse_subscription(content)

            subscription['last_update'] = datetime.now().isoformat()
            subscription['node_count'] = len(nodes)
            self.nodes.extend(nodes)

            logger.info(f"订阅 {subscription['name']} 更新成功")

        except Exception as e:
            logger.error(f"订阅 {subscription['name']} 更新失败: {e}")

    async def export_config(self, format: str = 'clash') -> str:
        """导出配置"""
        if format == 'clash':
            return self._export_clash()
        elif format == 'v2ray':
            return self._export_v2ray()
        else:
            return "不支持的格式"

    def _export_clash(self) -> str:
        """导出Clash配置"""
        config = {
            'port': 7890,
            'socks-port': 7891,
            'allow-lan': True,
            'mode': 'rule',
            'log-level': 'info',
            'proxies': self.nodes,
            'proxy-groups': [
                {
                    'name': '节点选择',
                    'type': 'select',
                    'proxies': [node['name'] for node in self.nodes]
                }
            ],
            'rules': [
                'DOMAIN-SUFFIX,google.com,节点选择',
                'GEOIP,CN,DIRECT',
                'MATCH,节点选择'
            ]
        }

        return yaml.dump(config, allow_unicode=True)

    def _export_v2ray(self) -> str:
        """导出V2Ray配置"""
        # 简化的V2Ray配置
        return "V2Ray配置导出功能开发中..."
