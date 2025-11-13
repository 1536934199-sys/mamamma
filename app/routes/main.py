"""
主路由 - 处理首页和通用页面
"""
from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import current_user
from app.models import Story, LearningModule, Character, Comment
from sqlalchemy import func

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """首页"""
    # 获取精选故事
    featured_stories = Story.get_featured_stories(limit=6)

    # 获取热门故事
    popular_stories = Story.get_popular_stories(limit=8)

    # 获取推荐学习模块
    recommended_modules = LearningModule.query.filter_by(
        is_published=True
    ).order_by(LearningModule.enrollment_count.desc()).limit(6).all()

    # 获取最新评论
    recent_comments = Comment.get_recent_comments(limit=5)

    # 获取热门角色
    popular_characters = Character.query.filter_by(is_active=True)\
        .order_by(Character.popularity_score.desc()).limit(8).all()

    # 统计数据
    stats = {
        'total_stories': Story.query.filter_by(is_published=True).count(),
        'total_modules': LearningModule.query.filter_by(is_published=True).count(),
        'total_characters': Character.query.filter_by(is_active=True).count(),
        'total_learners': db.session.query(func.count(func.distinct(UserProgress.user_id))).scalar() or 0
    }

    return render_template('index.html',
                         featured_stories=featured_stories,
                         popular_stories=popular_stories,
                         recommended_modules=recommended_modules,
                         recent_comments=recent_comments,
                         popular_characters=popular_characters,
                         stats=stats)


@bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')


@bp.route('/contact')
def contact():
    """联系页面"""
    return render_template('contact.html')


@bp.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')  # all, story, module, character
    page = int(request.args.get('page', 1))
    per_page = 20

    results = {'stories': [], 'modules': [], 'characters': [], 'total': 0}

    if query:
        if category in ['all', 'story']:
            # 搜索故事
            stories = Story.query.filter(
                Story.is_published == True,
                (Story.title.contains(query) |
                 Story.description.contains(query) |
                 Story.title_en.contains(query))
            ).all()
            results['stories'] = stories
            results['total'] += len(stories)

        if category in ['all', 'module']:
            # 搜索学习模块
            modules = LearningModule.query.filter(
                LearningModule.is_published == True,
                (LearningModule.title.contains(query) |
                 LearningModule.description.contains(query))
            ).all()
            results['modules'] = modules
            results['total'] += len(modules)

        if category in ['all', 'character']:
            # 搜索角色
            characters = Character.query.filter(
                Character.is_active == True,
                (Character.name.contains(query) |
                 Character.description.contains(query) |
                 Character.name_en.contains(query))
            ).all()
            results['characters'] = characters
            results['total'] += len(characters)

    return render_template('search.html', query=query, results=results, category=category)


@bp.route('/language/<lang>')
def change_language(lang):
    """切换语言"""
    if lang in ['zh_CN', 'en_US']:
        session['language'] = lang
        if current_user.is_authenticated:
            current_user.language = lang
            from app import db
            db.session.commit()
    return redirect(request.referrer or url_for('main.index'))


@bp.route('/characters')
def characters_list():
    """角色列表页"""
    page = int(request.args.get('page', 1))
    per_page = 24

    pagination = Character.query.filter_by(is_active=True)\
        .order_by(Character.popularity_score.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('characters/list.html', pagination=pagination)


@bp.route('/characters/<int:character_id>')
def character_detail(character_id):
    """角色详情页"""
    character = Character.query.get_or_404(character_id)

    # 增加人气
    character.increment_popularity()

    # 获取该角色出现的故事
    stories = character.stories.filter_by(is_published=True).all()

    return render_template('characters/detail.html',
                         character=character,
                         stories=stories)


# 引入必要的导入
from app.models import UserProgress
from app import db
