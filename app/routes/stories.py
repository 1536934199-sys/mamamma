"""
故事路由 - 处理皮影戏故事相关的页面
"""
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import current_user, login_required
from app import db
from app.models import Story, Comment, Rating, ContentView, UserActivity
from app.utils.helpers import paginate

bp = Blueprint('stories', __name__)


@bp.route('/')
def list_stories():
    """故事列表页"""
    page = int(request.args.get('page', 1))
    per_page = 12
    category = request.args.get('category')
    sort = request.args.get('sort', 'latest')  # latest, popular, rating

    query = Story.query.filter_by(is_published=True)

    # 分类过滤
    if category:
        query = query.filter_by(category=category)

    # 排序
    if sort == 'popular':
        query = query.order_by(Story.view_count.desc())
    elif sort == 'rating':
        # 按评分排序（需要join Rating表）
        query = query.outerjoin(Rating).group_by(Story.id)\
            .order_by(db.func.avg(Rating.score).desc().nullslast())
    else:  # latest
        query = query.order_by(Story.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 获取所有分类
    categories = db.session.query(Story.category).filter(
        Story.is_published == True,
        Story.category.isnot(None)
    ).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('stories/list.html',
                         pagination=pagination,
                         categories=categories,
                         current_category=category,
                         current_sort=sort)


@bp.route('/<slug>')
def story_detail(slug):
    """故事详情页"""
    # 优先使用语言
    language = current_user.language if current_user.is_authenticated else 'zh_CN'

    story = Story.query.filter_by(slug=slug, is_published=True).first_or_404()

    # 增加浏览次数
    story.increment_view()

    # 记录浏览
    ContentView.log_view(
        story_id=story.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        request=request
    )

    # 记录用户活动
    if current_user.is_authenticated:
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='view_story',
            details={'story_id': story.id, 'story_title': story.title},
            request=request
        )

    # 获取评论
    comments = Comment.get_story_comments(story.id, limit=20)

    # 获取用户评分
    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(
            user_id=current_user.id,
            story_id=story.id
        ).first()

    # 获取相关故事
    related_stories = Story.query.filter(
        Story.category == story.category,
        Story.id != story.id,
        Story.is_published == True
    ).order_by(Story.view_count.desc()).limit(4).all()

    return render_template('stories/detail.html',
                         story=story,
                         comments=comments,
                         user_rating=user_rating,
                         related_stories=related_stories)


@bp.route('/<int:story_id>/like', methods=['POST'])
@login_required
def like_story(story_id):
    """点赞故事"""
    story = Story.query.get_or_404(story_id)
    story.increment_like()

    # 记录活动
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='like_story',
        details={'story_id': story.id, 'story_title': story.title},
        request=request
    )

    if request.is_json:
        return jsonify({
            'message': '点赞成功',
            'like_count': story.like_count
        }), 200
    return redirect(url_for('stories.story_detail', slug=story.slug))


@bp.route('/<int:story_id>/share', methods=['POST'])
def share_story(story_id):
    """分享故事"""
    story = Story.query.get_or_404(story_id)
    story.increment_share()

    # 记录活动
    if current_user.is_authenticated:
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='share_story',
            details={'story_id': story.id, 'story_title': story.title},
            request=request
        )

    return jsonify({
        'message': '分享成功',
        'share_count': story.share_count
    }), 200


@bp.route('/<int:story_id>/comment', methods=['POST'])
@login_required
def add_comment(story_id):
    """添加评论"""
    story = Story.query.get_or_404(story_id)

    if request.is_json:
        data = request.get_json()
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
    else:
        content = request.form.get('content', '').strip()
        parent_id = request.form.get('parent_id')

    if not content:
        if request.is_json:
            return jsonify({'error': '评论内容不能为空'}), 400
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('stories.story_detail', slug=story.slug))

    # 创建评论
    comment = Comment(
        content=content,
        user_id=current_user.id,
        story_id=story_id,
        parent_id=parent_id if parent_id else None
    )
    db.session.add(comment)

    # 增加用户积分
    current_user.add_points(5)

    try:
        db.session.commit()

        # 记录活动
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='submit_comment',
            details={'story_id': story.id, 'comment_id': comment.id},
            request=request
        )

        if request.is_json:
            return jsonify({
                'message': '评论成功',
                'comment': comment.to_dict()
            }), 201
        flash('评论成功，获得5积分！', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': '评论失败'}), 500
        flash('评论失败，请稍后重试', 'danger')

    return redirect(url_for('stories.story_detail', slug=story.slug))


@bp.route('/<int:story_id>/rate', methods=['POST'])
@login_required
def rate_story(story_id):
    """评分故事"""
    story = Story.query.get_or_404(story_id)

    if request.is_json:
        data = request.get_json()
        score = data.get('score')
        review = data.get('review', '').strip()
    else:
        score = request.form.get('score')
        review = request.form.get('review', '').strip()

    try:
        score = int(score)
        if score < 1 or score > 5:
            raise ValueError
    except (TypeError, ValueError):
        if request.is_json:
            return jsonify({'error': '评分必须是1-5之间的整数'}), 400
        flash('评分必须是1-5之间的整数', 'danger')
        return redirect(url_for('stories.story_detail', slug=story.slug))

    # 检查是否已经评分
    existing_rating = Rating.query.filter_by(
        user_id=current_user.id,
        story_id=story_id
    ).first()

    if existing_rating:
        # 更新评分
        existing_rating.score = score
        existing_rating.review = review
        message = '评分已更新'
    else:
        # 创建新评分
        rating = Rating(
            score=score,
            review=review,
            user_id=current_user.id,
            story_id=story_id
        )
        db.session.add(rating)
        # 增加用户积分
        current_user.add_points(3)
        message = '评分成功，获得3积分！'

    try:
        db.session.commit()

        # 记录活动
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='rate_content',
            details={'story_id': story.id, 'score': score},
            request=request
        )

        if request.is_json:
            return jsonify({
                'message': message,
                'average_rating': story.get_average_rating()
            }), 200
        flash(message, 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': '评分失败'}), 500
        flash('评分失败，请稍后重试', 'danger')

    return redirect(url_for('stories.story_detail', slug=story.slug))


# 引入必要的模块
from flask import flash, redirect, url_for
