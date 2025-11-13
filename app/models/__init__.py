"""
数据库模型包 - 导出所有模型
"""
from app.models.user import User
from app.models.story import Story
from app.models.character import Character
from app.models.comment import Comment
from app.models.learning import LearningModule, Quiz, QuizQuestion, QuizAnswer, UserProgress
from app.models.rating import Rating
from app.models.analytics import UserActivity, ContentView

__all__ = [
    'User',
    'Story',
    'Character',
    'Comment',
    'LearningModule',
    'Quiz',
    'QuizQuestion',
    'QuizAnswer',
    'UserProgress',
    'Rating',
    'UserActivity',
    'ContentView'
]
