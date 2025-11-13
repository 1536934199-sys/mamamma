"""
路由包 - 导出所有蓝图
"""
from app.routes.auth import bp as auth_bp
from app.routes.main import bp as main_bp
from app.routes.api import bp as api_bp
from app.routes.stories import bp as stories_bp
from app.routes.learning import bp as learning_bp
from app.routes.admin import bp as admin_bp

__all__ = ['auth_bp', 'main_bp', 'api_bp', 'stories_bp', 'learning_bp', 'admin_bp']
