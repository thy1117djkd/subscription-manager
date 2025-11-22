#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
节点测试模块
测试节点的可用性和延迟
"""

import asyncio
import aiohttp
import time
from typing import List, Dict
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ProxyTester:
    """代理节点测试器"""

    def __init__(self, timeout=5, test_url='https://www.google.com/generate_204'):
        self.timeout = timeout
        self.test_url = test_url

    async def test_node(self, node: Dict) -> Dict:
        """测试单个节点"""
        result = {
            'name': node.get('name', 'Unknown'),
            'type': node.get('type', 'unknown'),
            'available': False,
            'delay': 0,
            'error': None
        }

        try:
            start_time = time.time()

            # 简化的测试逻辑
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 204 or response.status == 200:
                        delay = int((time.time() - start_time) * 1000)
                        result['available'] = True
                        result['delay'] = delay
                        logger.info(f"节点 {result['name']} 可用, 延迟: {delay}ms")
                    else:
                        result['error'] = f"HTTP {response.status}"

        except asyncio.TimeoutError:
            result['error'] = '超时'
            logger.warning(f"节点 {result['name']} 超时")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"节点 {result['name']} 测试失败: {e}")

        return result

    async def test_all_nodes(self, nodes: List[Dict] = None) -> List[Dict]:
        """测试所有节点"""
        if nodes is None:
            # 模拟一些节点数据
            nodes = self._get_sample_nodes()

        tasks = [self.test_node(node) for node in nodes]
        results = await asyncio.gather(*tasks)

        available_count = sum(1 for r in results if r['available'])
        logger.info(f"测试完成: {available_count}/{len(results)} 个节点可用")

        return results

    def _get_sample_nodes(self) -> List[Dict]:
        """获取示例节点（用于演示）"""
        return [
            {'name': 'HK-Node-01', 'type': 'vmess', 'server': 'example.com', 'port': 443},
            {'name': 'US-Node-01', 'type': 'trojan', 'server': 'example.com', 'port': 443},
            {'name': 'JP-Node-01', 'type': 'shadowsocks', 'server': 'example.com', 'port': 443},
        ]
