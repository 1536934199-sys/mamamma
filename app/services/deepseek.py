"""
DeepSeek API集成 - 智能推荐和内容分析
"""
import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self):
        self.api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        self.api_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
        self.timeout = 30

    def _make_request(self, endpoint, data=None, method='POST'):
        """发送API请求"""
        if not self.api_key:
            logger.warning("DeepSeek API密钥未配置")
            return None

        url = f"{self.api_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            else:
                response = requests.get(url, headers=headers, timeout=self.timeout)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API请求失败: {str(e)}")
            return None

    def get_content_recommendations(self, user_history, limit=10):
        """
        基于用户历史获取内容推荐

        Args:
            user_history: 用户学习历史数据
            limit: 返回的推荐数量

        Returns:
            推荐内容列表
        """
        data = {
            'user_history': user_history,
            'limit': limit,
            'task': 'content_recommendation'
        }

        result = self._make_request('recommendations', data)
        if result:
            return result.get('recommendations', [])
        return []

    def analyze_user_interests(self, user_activities):
        """
        分析用户兴趣

        Args:
            user_activities: 用户活动数据

        Returns:
            用户兴趣标签和偏好
        """
        data = {
            'activities': user_activities,
            'task': 'interest_analysis'
        }

        result = self._make_request('analyze', data)
        if result:
            return result.get('interests', {})
        return {}

    def generate_story_summary(self, story_content):
        """
        生成故事摘要

        Args:
            story_content: 故事内容

        Returns:
            故事摘要
        """
        data = {
            'content': story_content,
            'task': 'summarization',
            'max_length': 200
        }

        result = self._make_request('generate', data)
        if result:
            return result.get('summary', '')
        return ''

    def get_similar_content(self, content_id, content_type='story', limit=5):
        """
        获取相似内容

        Args:
            content_id: 内容ID
            content_type: 内容类型（story/module）
            limit: 返回数量

        Returns:
            相似内容列表
        """
        data = {
            'content_id': content_id,
            'content_type': content_type,
            'limit': limit,
            'task': 'similarity'
        }

        result = self._make_request('similar', data)
        if result:
            return result.get('similar_items', [])
        return []

    def personalize_learning_path(self, user_level, completed_modules, interests):
        """
        个性化学习路径推荐

        Args:
            user_level: 用户等级
            completed_modules: 已完成的模块
            interests: 用户兴趣

        Returns:
            推荐的学习路径
        """
        data = {
            'user_level': user_level,
            'completed_modules': completed_modules,
            'interests': interests,
            'task': 'learning_path'
        }

        result = self._make_request('learning-path', data)
        if result:
            return result.get('path', [])
        return []


def get_deepseek_client():
    """获取DeepSeek客户端实例"""
    return DeepSeekClient()
