"""
管理员路由 - 后台管理功能
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import (User, Story, LearningModule, Character, Comment,
                       Quiz, QuizQuestion, UserActivity, ContentView)
from app.utils.decorators import admin_required
from app.utils.helpers import generate_slug
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__)


@bp.before_request
@login_required
@admin_required
def before_request():
    """所有admin路由都需要管理员权限"""
    pass


@bp.route('/')
def dashboard():
    """管理员仪表盘"""
    # 统计数据
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_stories': Story.query.count(),
        'published_stories': Story.query.filter_by(is_published=True).count(),
        'total_modules': LearningModule.query.count(),
        'total_comments': Comment.query.filter_by(is_deleted=False).count(),
        'pending_comments': Comment.query.filter_by(is_approved=False, is_deleted=False).count()
    }

    # 最近7天的活动
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_activities = UserActivity.query.filter(
        UserActivity.created_at >= seven_days_ago
    ).order_by(UserActivity.created_at.desc()).limit(20).all()

    # 最新用户
    new_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_activities=recent_activities,
                         new_users=new_users)


# ==================== 用户管理 ====================
@bp.route('/users')
def users_list():
    """用户列表"""
    page = int(request.args.get('page', 1))
    per_page = 20

    query = User.query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/users/list.html', pagination=pagination)


@bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
def toggle_user_active(user_id):
    """切换用户激活状态"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('不能禁用自己的账户', 'danger')
        return redirect(url_for('admin.users_list'))

    user.is_active = not user.is_active
    db.session.commit()

    status = '激活' if user.is_active else '禁用'
    flash(f'用户 {user.username} 已{status}', 'success')
    return redirect(url_for('admin.users_list'))


# ==================== 故事管理 ====================
@bp.route('/stories')
def stories_list():
    """故事列表"""
    page = int(request.args.get('page', 1))
    per_page = 20

    query = Story.query.order_by(Story.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/stories/list.html', pagination=pagination)


@bp.route('/stories/create', methods=['GET', 'POST'])
def create_story():
    """创建故事"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        title_en = request.form.get('title_en', '').strip()
        description = request.form.get('description', '').strip()
        description_en = request.form.get('description_en', '').strip()
        full_content = request.form.get('full_content', '').strip()
        full_content_en = request.form.get('full_content_en', '').strip()
        category = request.form.get('category', '').strip()
        difficulty_level = int(request.form.get('difficulty_level', 1))
        is_featured = request.form.get('is_featured') == 'on'
        is_published = request.form.get('is_published') == 'on'

        if not title or not description:
            flash('标题和描述不能为空', 'danger')
            return render_template('admin/stories/create.html')

        # 生成slug
        slug = generate_slug(title)

        # 检查slug是否已存在
        if Story.query.filter_by(slug=slug).first():
            slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        story = Story(
            title=title,
            title_en=title_en if title_en else None,
            slug=slug,
            description=description,
            description_en=description_en if description_en else None,
            full_content=full_content,
            full_content_en=full_content_en if full_content_en else None,
            category=category,
            difficulty_level=difficulty_level,
            is_featured=is_featured,
            is_published=is_published,
            author_id=current_user.id,
            published_at=datetime.utcnow() if is_published else None
        )

        db.session.add(story)
        db.session.commit()

        flash('故事创建成功', 'success')
        return redirect(url_for('admin.stories_list'))

    return render_template('admin/stories/create.html')


@bp.route('/stories/<int:story_id>/edit', methods=['GET', 'POST'])
def edit_story(story_id):
    """编辑故事"""
    story = Story.query.get_or_404(story_id)

    if request.method == 'POST':
        story.title = request.form.get('title', '').strip()
        story.title_en = request.form.get('title_en', '').strip() or None
        story.description = request.form.get('description', '').strip()
        story.description_en = request.form.get('description_en', '').strip() or None
        story.full_content = request.form.get('full_content', '').strip()
        story.full_content_en = request.form.get('full_content_en', '').strip() or None
        story.category = request.form.get('category', '').strip()
        story.difficulty_level = int(request.form.get('difficulty_level', 1))
        story.is_featured = request.form.get('is_featured') == 'on'
        story.is_published = request.form.get('is_published') == 'on'

        if story.is_published and not story.published_at:
            story.published_at = datetime.utcnow()

        db.session.commit()
        flash('故事更新成功', 'success')
        return redirect(url_for('admin.stories_list'))

    return render_template('admin/stories/edit.html', story=story)


@bp.route('/stories/<int:story_id>/delete', methods=['POST'])
def delete_story(story_id):
    """删除故事"""
    story = Story.query.get_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    flash('故事已删除', 'success')
    return redirect(url_for('admin.stories_list'))


# ==================== 学习模块管理 ====================
@bp.route('/modules')
def modules_list():
    """学习模块列表"""
    page = int(request.args.get('page', 1))
    per_page = 20

    query = LearningModule.query.order_by(LearningModule.order, LearningModule.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/modules/list.html', pagination=pagination)


@bp.route('/modules/create', methods=['GET', 'POST'])
def create_module():
    """创建学习模块"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', '').strip()
        difficulty_level = int(request.form.get('difficulty_level', 1))
        order = int(request.form.get('order', 0))
        estimated_duration = int(request.form.get('estimated_duration', 30))
        points_reward = int(request.form.get('points_reward', 10))
        is_published = request.form.get('is_published') == 'on'

        if not title or not content:
            flash('标题和内容不能为空', 'danger')
            return render_template('admin/modules/create.html')

        slug = generate_slug(title)
        if LearningModule.query.filter_by(slug=slug).first():
            slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        module = LearningModule(
            title=title,
            slug=slug,
            description=description,
            content=content,
            category=category,
            difficulty_level=difficulty_level,
            order=order,
            estimated_duration=estimated_duration,
            points_reward=points_reward,
            is_published=is_published
        )

        db.session.add(module)
        db.session.commit()

        flash('学习模块创建成功', 'success')
        return redirect(url_for('admin.modules_list'))

    return render_template('admin/modules/create.html')


# ==================== 评论管理 ====================
@bp.route('/comments')
def comments_list():
    """评论列表"""
    page = int(request.args.get('page', 1))
    per_page = 50

    query = Comment.query.filter_by(is_deleted=False)\
        .order_by(Comment.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/comments/list.html', pagination=pagination)


@bp.route('/comments/<int:comment_id>/approve', methods=['POST'])
def approve_comment(comment_id):
    """批准评论"""
    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    flash('评论已批准', 'success')
    return redirect(url_for('admin.comments_list'))


@bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    """删除评论"""
    comment = Comment.query.get_or_404(comment_id)
    comment.soft_delete()
    flash('评论已删除', 'success')
    return redirect(url_for('admin.comments_list'))


# ==================== 数据分析 ====================
@bp.route('/analytics')
def analytics():
    """数据分析"""
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)

    # 活跃用户统计
    active_users = UserActivity.query.filter(
        UserActivity.created_at >= start_date
    ).with_entities(UserActivity.user_id).distinct().count()

    # 内容浏览统计
    story_views = ContentView.query.filter(
        ContentView.created_at >= start_date,
        ContentView.story_id.isnot(None)
    ).count()

    module_views = ContentView.query.filter(
        ContentView.created_at >= start_date,
        ContentView.module_id.isnot(None)
    ).count()

    # 新增用户
    new_users = User.query.filter(User.created_at >= start_date).count()

    analytics_data = {
        'active_users': active_users,
        'story_views': story_views,
        'module_views': module_views,
        'new_users': new_users,
        'period_days': days
    }

    return render_template('admin/analytics.html', data=analytics_data)
