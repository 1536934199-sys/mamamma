"""
推荐系统 - 内容推荐算法
"""
from app.models import (User, Story, LearningModule, UserProgress,
                       UserActivity, ContentView, Rating)
from app.services.deepseek import get_deepseek_client
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_personalized_recommendations(user_id, limit=10):
    """
    获取个性化推荐

    Args:
        user_id: 用户ID
        limit: 推荐数量

    Returns:
        推荐内容字典
    """
    user = User.query.get(user_id)
    if not user:
        return get_default_recommendations(limit)

    # 获取用户学习历史
    user_history = get_user_learning_history(user_id)

    # 如果用户历史较少，返回默认推荐
    if len(user_history.get('viewed_stories', [])) < 3:
        return get_default_recommendations(limit)

    # 使用混合推荐策略
    recommendations = {
        'stories': [],
        'modules': []
    }

    # 1. 基于协同过滤的推荐
    collaborative_stories = get_collaborative_stories(user_id, limit=5)
    recommendations['stories'].extend(collaborative_stories)

    # 2. 基于内容的推荐
    content_based_stories = get_content_based_stories(user_id, limit=5)
    recommendations['stories'].extend(content_based_stories)

    # 3. 基于学习进度的模块推荐
    recommended_modules = get_next_modules(user_id, limit=limit)
    recommendations['modules'].extend(recommended_modules)

    # 4. 尝试使用DeepSeek进行智能推荐（可选）
    try:
        deepseek_recs = get_deepseek_recommendations(user_id, user_history, limit=5)
        if deepseek_recs:
            recommendations['stories'].extend(deepseek_recs.get('stories', []))
            recommendations['modules'].extend(deepseek_recs.get('modules', []))
    except Exception as e:
        logger.warning(f"DeepSeek推荐失败: {str(e)}")

    # 去重并限制数量
    recommendations['stories'] = deduplicate_and_limit(recommendations['stories'], limit)
    recommendations['modules'] = deduplicate_and_limit(recommendations['modules'], limit)

    return recommendations


def get_user_learning_history(user_id):
    """获取用户学习历史"""
    # 获取浏览过的故事
    viewed_stories = ContentView.query.filter_by(user_id=user_id)\
        .filter(ContentView.story_id.isnot(None))\
        .order_by(ContentView.created_at.desc())\
        .limit(50).all()

    # 获取学习进度
    progress = UserProgress.query.filter_by(user_id=user_id).all()

    # 获取评分
    ratings = Rating.query.filter_by(user_id=user_id).all()

    # 获取活动
    activities = UserActivity.query.filter_by(user_id=user_id)\
        .order_by(UserActivity.created_at.desc())\
        .limit(100).all()

    return {
        'viewed_stories': [v.story_id for v in viewed_stories],
        'viewed_modules': [p.module_id for p in progress],
        'completed_modules': [p.module_id for p in progress if p.completed],
        'liked_stories': [r.story_id for r in ratings if r.score >= 4 and r.story_id],
        'recent_activities': [a.activity_type for a in activities]
    }


def get_collaborative_stories(user_id, limit=5):
    """
    协同过滤推荐故事

    找到相似用户喜欢的故事
    """
    # 获取用户评分较高的故事
    user_liked_stories = Rating.query.filter_by(user_id=user_id)\
        .filter(Rating.score >= 4)\
        .filter(Rating.story_id.isnot(None))\
        .all()

    if not user_liked_stories:
        return []

    liked_story_ids = [r.story_id for r in user_liked_stories]

    # 找到也喜欢这些故事的其他用户
    similar_users = Rating.query.filter(
        Rating.story_id.in_(liked_story_ids),
        Rating.user_id != user_id,
        Rating.score >= 4
    ).with_entities(Rating.user_id).distinct().all()

    similar_user_ids = [u[0] for u in similar_users]

    if not similar_user_ids:
        return []

    # 获取这些用户喜欢的其他故事
    recommended = Story.query.join(Rating).filter(
        Rating.user_id.in_(similar_user_ids),
        Rating.score >= 4,
        Story.id.notin_(liked_story_ids),
        Story.is_published == True
    ).group_by(Story.id)\
     .order_by(func.count(Rating.id).desc())\
     .limit(limit).all()

    return [s.to_dict() for s in recommended]


def get_content_based_stories(user_id, limit=5):
    """
    基于内容的推荐

    推荐与用户喜欢的故事相似的内容
    """
    # 获取用户浏览最多的故事分类
    viewed_categories = ContentView.query.join(Story).filter(
        ContentView.user_id == user_id,
        ContentView.story_id.isnot(None)
    ).with_entities(Story.category, func.count(Story.category))\
     .group_by(Story.category)\
     .order_by(func.count(Story.category).desc())\
     .limit(3).all()

    if not viewed_categories:
        return []

    preferred_categories = [c[0] for c in viewed_categories]

    # 获取用户已浏览的故事ID
    viewed_story_ids = [v.story_id for v in ContentView.query.filter_by(user_id=user_id).all()]

    # 推荐相同分类的热门故事
    recommended = Story.query.filter(
        Story.category.in_(preferred_categories),
        Story.id.notin_(viewed_story_ids) if viewed_story_ids else True,
        Story.is_published == True
    ).order_by(Story.view_count.desc())\
     .limit(limit).all()

    return [s.to_dict() for s in recommended]


def get_next_modules(user_id, limit=10):
    """
    推荐下一步学习模块

    基于用户当前等级和已完成模块
    """
    user = User.query.get(user_id)
    completed_module_ids = [p.module_id for p in
                           UserProgress.query.filter_by(user_id=user_id, completed=True).all()]

    # 推荐适合用户等级且未完成的模块
    recommended = LearningModule.query.filter(
        LearningModule.difficulty_level <= user.level + 1,
        LearningModule.id.notin_(completed_module_ids) if completed_module_ids else True,
        LearningModule.is_published == True
    ).order_by(
        LearningModule.difficulty_level,
        LearningModule.enrollment_count.desc()
    ).limit(limit).all()

    return [m.to_dict() for m in recommended]


def get_deepseek_recommendations(user_id, user_history, limit=5):
    """
    使用DeepSeek API获取智能推荐
    """
    try:
        client = get_deepseek_client()

        # 调用DeepSeek API
        recs = client.get_content_recommendations(user_history, limit=limit)

        if not recs:
            return None

        # 解析推荐结果
        story_ids = [r.get('story_id') for r in recs if r.get('type') == 'story']
        module_ids = [r.get('module_id') for r in recs if r.get('type') == 'module']

        stories = Story.query.filter(Story.id.in_(story_ids)).all() if story_ids else []
        modules = LearningModule.query.filter(LearningModule.id.in_(module_ids)).all() if module_ids else []

        return {
            'stories': [s.to_dict() for s in stories],
            'modules': [m.to_dict() for m in modules]
        }
    except Exception as e:
        logger.error(f"DeepSeek推荐错误: {str(e)}")
        return None


def get_default_recommendations(limit=10):
    """
    默认推荐（新用户或无足够历史数据）
    """
    # 推荐精选和热门内容
    featured_stories = Story.get_featured_stories(limit=5)
    popular_stories = Story.get_popular_stories(limit=5)

    popular_modules = LearningModule.query.filter_by(is_published=True)\
        .order_by(LearningModule.enrollment_count.desc())\
        .limit(limit).all()

    return {
        'stories': [s.to_dict() for s in featured_stories + popular_stories][:limit],
        'modules': [m.to_dict() for m in popular_modules]
    }


def deduplicate_and_limit(items, limit):
    """去重并限制数量"""
    seen_ids = set()
    unique_items = []

    for item in items:
        item_id = item.get('id')
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            unique_items.append(item)
            if len(unique_items) >= limit:
                break

    return unique_items


def get_trending_content(days=7, limit=10):
    """获取趋势内容"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # 使用ContentView统计
    trending_stories = ContentView.get_popular_content('story', limit=limit, days=days)
    trending_modules = ContentView.get_popular_content('module', limit=limit, days=days)

    return {
        'stories': trending_stories,
        'modules': trending_modules
    }
