"""
应用工厂 - 使用工厂模式创建Flask应用
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import config
import os
import logging
from logging.handlers import RotatingFileHandler


# 初始化扩展（但不绑定到app）
db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_name=None):
    """
    应用工厂函数

    Args:
        config_name: 配置名称 ('development', 'production', 'testing')

    Returns:
        Flask应用实例
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # 加载配置
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    login_manager.login_message_category = 'info'

    # 注册蓝图
    from app.routes import auth, main, api, stories, learning, admin

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(stories.bp, url_prefix='/stories')
    app.register_blueprint(learning.bp, url_prefix='/learning')
    app.register_blueprint(admin.bp, url_prefix='/admin')

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化数据
        from app.utils.init_data import init_database
        init_database()

    # 配置日志
    setup_logging(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 注册上下文处理器
    register_context_processors(app)

    return app


def setup_logging(app):
    """配置日志系统"""
    if not app.debug and not app.testing:
        # 创建日志目录
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 文件处理器
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('皮影戏学习平台启动')


def register_error_handlers(app):
    """注册错误处理器"""
    from flask import render_template, jsonify, request

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': '资源未找到'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': '服务器内部错误'}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': '禁止访问'}), 403
        return render_template('errors/403.html'), 403


def register_context_processors(app):
    """注册模板上下文处理器"""
    from datetime import datetime

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    @app.context_processor
    def inject_config():
        return {'app_config': app.config}


@babel.localeselector
def get_locale():
    """获取用户语言偏好"""
    from flask import request, session

    # 优先使用会话中的语言设置
    if 'language' in session:
        return session['language']

    # 否则使用请求头中的Accept-Language
    return request.accept_languages.best_match(['zh_CN', 'en_US']) or 'zh_CN'


@login_manager.user_loader
def load_user(user_id):
    """加载用户回调"""
    from app.models.user import User
    return User.query.get(int(user_id))
