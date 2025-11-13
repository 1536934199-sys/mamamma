"""
API路由 - RESTful API接口
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (User, Story, LearningModule, Character, Comment,
                       Rating, UserProgress, UserActivity, ContentView)
from app.utils.decorators import validate_pagination, json_required
from app.utils.helpers import paginate
from datetime import datetime, timedelta

bp = Blueprint('api', __name__)


# ==================== 故事API ====================
@bp.route('/stories', methods=['GET'])
@validate_pagination
def get_stories(page, per_page):
    """获取故事列表"""
    category = request.args.get('category')
    featured = request.args.get('featured', '').lower() == 'true'
    language = request.args.get('language', 'zh_CN')

    query = Story.query.filter_by(is_published=True)

    if category:
        query = query.filter_by(category=category)
    if featured:
        query = query.filter_by(is_featured=True)

    query = query.order_by(Story.created_at.desc())

    result = paginate(query, page, per_page)
    result['items'] = [story.to_dict(language=language) for story in result['items']]

    return jsonify(result), 200


@bp.route('/stories/<int:story_id>', methods=['GET'])
def get_story(story_id):
    """获取单个故事详情"""
    language = request.args.get('language', 'zh_CN')
    story = Story.query.get_or_404(story_id)

    if not story.is_published:
        return jsonify({'error': '故事未发布'}), 404

    return jsonify(story.to_dict(include_content=True, language=language)), 200


@bp.route('/stories/<int:story_id>/comments', methods=['GET'])
@validate_pagination
def get_story_comments(story_id, page, per_page):
    """获取故事评论"""
    story = Story.query.get_or_404(story_id)

    query = Comment.query.filter_by(
        story_id=story_id,
        is_deleted=False,
        is_approved=True,
        parent_id=None
    ).order_by(Comment.created_at.desc())

    result = paginate(query, page, per_page)
    result['items'] = [comment.to_dict() for comment in result['items']]

    return jsonify(result), 200


# ==================== 学习模块API ====================
@bp.route('/modules', methods=['GET'])
@validate_pagination
def get_modules(page, per_page):
    """获取学习模块列表"""
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    language = request.args.get('language', 'zh_CN')

    query = LearningModule.query.filter_by(is_published=True)

    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty_level=int(difficulty))

    query = query.order_by(LearningModule.order, LearningModule.created_at.desc())

    result = paginate(query, page, per_page)
    result['items'] = [module.to_dict(language=language) for module in result['items']]

    return jsonify(result), 200


@bp.route('/modules/<int:module_id>', methods=['GET'])
def get_module(module_id):
    """获取单个学习模块详情"""
    language = request.args.get('language', 'zh_CN')
    module = LearningModule.query.get_or_404(module_id)

    if not module.is_published:
        return jsonify({'error': '模块未发布'}), 404

    return jsonify(module.to_dict(include_content=True, language=language)), 200


# ==================== 角色API ====================
@bp.route('/characters', methods=['GET'])
@validate_pagination
def get_characters(page, per_page):
    """获取角色列表"""
    language = request.args.get('language', 'zh_CN')

    query = Character.query.filter_by(is_active=True)\
        .order_by(Character.popularity_score.desc())

    result = paginate(query, page, per_page)
    result['items'] = [char.to_dict(language=language) for char in result['items']]

    return jsonify(result), 200


@bp.route('/characters/<int:character_id>', methods=['GET'])
def get_character(character_id):
    """获取单个角色详情"""
    language = request.args.get('language', 'zh_CN')
    character = Character.query.get_or_404(character_id)

    return jsonify(character.to_dict(language=language)), 200


# ==================== 用户API ====================
@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户信息"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


@bp.route('/users/<int:user_id>/progress', methods=['GET'])
@jwt_required()
def get_user_progress(user_id):
    """获取用户学习进度"""
    current_user_id = get_jwt_identity()

    # 只能查看自己的进度
    if current_user_id != user_id:
        return jsonify({'error': '无权访问'}), 403

    progress_list = UserProgress.query.filter_by(user_id=user_id).all()
    return jsonify({
        'progress': [p.to_dict() for p in progress_list]
    }), 200


@bp.route('/users/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """获取用户统计数据"""
    user = User.query.get_or_404(user_id)
    stats = user.get_learning_stats()
    return jsonify(stats), 200


# ==================== 搜索API ====================
@bp.route('/search', methods=['GET'])
def search():
    """搜索内容"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')
    language = request.args.get('language', 'zh_CN')

    if not query:
        return jsonify({'error': '搜索关键词不能为空'}), 400

    results = {'stories': [], 'modules': [], 'characters': []}

    if category in ['all', 'story']:
        stories = Story.query.filter(
            Story.is_published == True,
            (Story.title.contains(query) | Story.description.contains(query))
        ).limit(10).all()
        results['stories'] = [s.to_dict(language=language) for s in stories]

    if category in ['all', 'module']:
        modules = LearningModule.query.filter(
            LearningModule.is_published == True,
            (LearningModule.title.contains(query) | LearningModule.description.contains(query))
        ).limit(10).all()
        results['modules'] = [m.to_dict(language=language) for m in modules]

    if category in ['all', 'character']:
        characters = Character.query.filter(
            Character.is_active == True,
            (Character.name.contains(query) | Character.description.contains(query))
        ).limit(10).all()
        results['characters'] = [c.to_dict(language=language) for c in characters]

    return jsonify(results), 200


# ==================== 推荐API ====================
@bp.route('/recommendations', methods=['GET'])
@jwt_required(optional=True)
def get_recommendations():
    """获取推荐内容"""
    current_user_id = get_jwt_identity()
    limit = int(request.args.get('limit', 10))
    language = request.args.get('language', 'zh_CN')

    if current_user_id:
        # 已登录用户 - 基于学习历史推荐
        from app.services.recommendation import get_personalized_recommendations
        recommendations = get_personalized_recommendations(current_user_id, limit)
    else:
        # 未登录用户 - 推荐热门内容
        recommendations = {
            'stories': [s.to_dict(language=language)
                       for s in Story.get_popular_stories(limit=limit)],
            'modules': [m.to_dict(language=language)
                       for m in LearningModule.query.filter_by(is_published=True)
                       .order_by(LearningModule.enrollment_count.desc())
                       .limit(limit).all()]
        }

    return jsonify(recommendations), 200


# ==================== 统计API ====================
@bp.route('/stats', methods=['GET'])
def get_platform_stats():
    """获取平台统计数据"""
    stats = {
        'total_stories': Story.query.filter_by(is_published=True).count(),
        'total_modules': LearningModule.query.filter_by(is_published=True).count(),
        'total_characters': Character.query.filter_by(is_active=True).count(),
        'total_users': User.query.filter_by(is_active=True).count(),
        'total_learners': db.session.query(db.func.count(db.func.distinct(UserProgress.user_id))).scalar() or 0
    }

    return jsonify(stats), 200


@bp.route('/stats/trending', methods=['GET'])
def get_trending():
    """获取趋势数据"""
    days = int(request.args.get('days', 7))
    language = request.args.get('language', 'zh_CN')

    # 获取热门内容
    popular_stories = ContentView.get_popular_content('story', limit=10, days=days)
    popular_modules = ContentView.get_popular_content('module', limit=10, days=days)

    # 获取详细信息
    story_ids = [item['story_id'] for item in popular_stories]
    module_ids = [item['module_id'] for item in popular_modules]

    stories = Story.query.filter(Story.id.in_(story_ids)).all()
    modules = LearningModule.query.filter(LearningModule.id.in_(module_ids)).all()

    return jsonify({
        'trending_stories': [s.to_dict(language=language) for s in stories],
        'trending_modules': [m.to_dict(language=language) for m in modules]
    }), 200


# ==================== 健康检查 ====================
@bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
