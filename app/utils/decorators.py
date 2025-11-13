"""
装饰器 - 自定义装饰器函数
"""
from functools import wraps
from flask import jsonify, request, abort
from flask_login import current_user
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def json_required(f):
    """要求JSON格式的请求"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': '请求必须为JSON格式'}), 400
        return f(*args, **kwargs)
    return decorated_function


def jwt_required_custom(f):
    """自定义JWT验证装饰器（用于API）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            if not user or not user.is_active:
                return jsonify({'error': '用户不存在或已被禁用'}), 401
            # 将用户对象添加到kwargs中
            kwargs['current_user'] = user
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': '认证失败', 'message': str(e)}), 401
    return decorated_function


def api_key_required(f):
    """API密钥验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        # 这里应该验证API密钥，简化实现
        if not api_key:
            return jsonify({'error': '缺少API密钥'}), 401
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(max_per_hour=100):
    """简单的速率限制装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 实际应用中应使用Redis等实现真正的速率限制
            # 这里只是示例
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_pagination(f):
    """验证分页参数"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))

            if page < 1:
                page = 1
            if per_page < 1 or per_page > 100:
                per_page = 20

            kwargs['page'] = page
            kwargs['per_page'] = per_page
            return f(*args, **kwargs)
        except ValueError:
            return jsonify({'error': '无效的分页参数'}), 400
    return decorated_function


def log_activity(activity_type):
    """记录用户活动的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            result = f(*args, **kwargs)

            # 记录活动
            if current_user.is_authenticated:
                from app.models.analytics import UserActivity
                details = kwargs.get('activity_details', {})
                UserActivity.log_activity(
                    user_id=current_user.id,
                    activity_type=activity_type,
                    details=details,
                    request=request
                )

            return result
        return decorated_function
    return decorator


def cache_response(timeout=300):
    """缓存响应装饰器（简化版）"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 实际应用中应使用Redis等实现缓存
            # 这里只是示例
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def cors_enabled(f):
    """启用CORS的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        if isinstance(response, tuple):
            data, status_code = response[0], response[1]
        else:
            data, status_code = response, 200

        if hasattr(data, 'headers'):
            data.headers['Access-Control-Allow-Origin'] = '*'
            data.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            data.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

        return data, status_code
    return decorated_function
