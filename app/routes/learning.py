"""
学习路由 - 处理学习模块相关的页面
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user, login_required
from app import db
from app.models import (LearningModule, Quiz, QuizQuestion, QuizAnswer,
                       UserProgress, Rating, Comment, UserActivity, ContentView)
from datetime import datetime

bp = Blueprint('learning', __name__)


@bp.route('/')
def list_modules():
    """学习模块列表页"""
    page = int(request.args.get('page', 1))
    per_page = 12
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')

    query = LearningModule.query.filter_by(is_published=True)

    # 过滤
    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty_level=int(difficulty))

    # 排序
    query = query.order_by(LearningModule.order, LearningModule.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 获取所有分类
    categories = db.session.query(LearningModule.category).filter(
        LearningModule.is_published == True,
        LearningModule.category.isnot(None)
    ).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('learning/list.html',
                         pagination=pagination,
                         categories=categories,
                         current_category=category,
                         current_difficulty=difficulty)


@bp.route('/<slug>')
@login_required
def module_detail(slug):
    """学习模块详情页"""
    module = LearningModule.query.filter_by(slug=slug, is_published=True).first_or_404()

    # 获取或创建用户进度
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        module_id=module.id
    ).first()

    if not progress:
        # 首次访问，创建进度记录
        progress = UserProgress(
            user_id=current_user.id,
            module_id=module.id
        )
        db.session.add(progress)
        module.increment_enrollment()
        db.session.commit()

    # 记录浏览
    ContentView.log_view(
        module_id=module.id,
        user_id=current_user.id,
        request=request
    )

    # 记录活动
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='view_module',
        details={'module_id': module.id, 'module_title': module.title},
        request=request
    )

    # 获取测验
    quizzes = module.quizzes.all()

    # 获取用户评分
    user_rating = Rating.query.filter_by(
        user_id=current_user.id,
        module_id=module.id
    ).first()

    # 获取评论
    comments = module.comments.filter_by(
        is_deleted=False,
        is_approved=True,
        parent_id=None
    ).order_by(Comment.created_at.desc()).limit(10).all()

    return render_template('learning/detail.html',
                         module=module,
                         progress=progress,
                         quizzes=quizzes,
                         user_rating=user_rating,
                         comments=comments)


@bp.route('/<int:module_id>/update-progress', methods=['POST'])
@login_required
def update_progress(module_id):
    """更新学习进度"""
    module = LearningModule.query.get_or_404(module_id)
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        module_id=module_id
    ).first_or_404()

    data = request.get_json()
    progress_value = data.get('progress', 0)
    time_spent = data.get('time_spent', 0)
    last_position = data.get('last_position', '')

    progress.update_progress(progress_value)
    if time_spent:
        progress.add_time(time_spent)
    if last_position:
        progress.last_position = last_position

    return jsonify({
        'message': '进度已更新',
        'progress': progress.to_dict()
    }), 200


@bp.route('/<int:module_id>/complete', methods=['POST'])
@login_required
def complete_module(module_id):
    """完成学习模块"""
    module = LearningModule.query.get_or_404(module_id)
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        module_id=module_id
    ).first_or_404()

    if not progress.completed:
        progress.complete()

        # 记录活动
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='complete_module',
            details={
                'module_id': module.id,
                'module_title': module.title,
                'points_earned': module.points_reward
            },
            request=request
        )

        return jsonify({
            'message': f'恭喜完成学习！获得{module.points_reward}积分',
            'points_earned': module.points_reward,
            'user_points': current_user.points,
            'user_level': current_user.level
        }), 200

    return jsonify({'message': '模块已完成'}), 200


@bp.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    """参加测验"""
    quiz = Quiz.query.get_or_404(quiz_id)
    module = quiz.module

    # 检查用户进度
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        module_id=module.id
    ).first()

    if not progress:
        flash('请先学习该模块内容', 'warning')
        return redirect(url_for('learning.module_detail', slug=module.slug))

    # 检查尝试次数
    if progress.quiz_attempts >= quiz.max_attempts:
        flash(f'您已达到最大尝试次数（{quiz.max_attempts}次）', 'danger')
        return redirect(url_for('learning.module_detail', slug=module.slug))

    # 获取问题
    questions = quiz.questions.all()

    return render_template('learning/quiz.html',
                         quiz=quiz,
                         module=module,
                         questions=questions,
                         progress=progress)


@bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    """提交测验答案"""
    quiz = Quiz.query.get_or_404(quiz_id)
    module = quiz.module

    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        module_id=module.id
    ).first_or_404()

    # 增加尝试次数
    progress.quiz_attempts += 1

    data = request.get_json()
    answers = data.get('answers', {})  # {question_id: user_answer}

    # 评分
    total_points = 0
    earned_points = 0
    results = []

    for question in quiz.questions:
        question_id = str(question.id)
        user_answer = answers.get(question_id)

        is_correct = question.check_answer(user_answer)
        points = question.points if is_correct else 0

        total_points += question.points
        earned_points += points

        # 记录答案
        answer_record = QuizAnswer(
            user_id=current_user.id,
            quiz_id=quiz_id,
            question_id=question.id,
            user_answer=user_answer,
            is_correct=is_correct,
            points_earned=points
        )
        db.session.add(answer_record)

        results.append({
            'question_id': question.id,
            'is_correct': is_correct,
            'points': points,
            'explanation': question.explanation
        })

    # 计算分数
    score = int((earned_points / total_points) * 100) if total_points > 0 else 0

    # 更新最佳成绩
    if score > progress.best_quiz_score:
        progress.best_quiz_score = score

    # 检查是否通过
    if score >= quiz.passing_score:
        progress.quiz_passed = True
        current_user.add_points(10)  # 通过测验获得积分

    db.session.commit()

    # 记录活动
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='quiz_attempt',
        details={
            'quiz_id': quiz.id,
            'score': score,
            'passed': score >= quiz.passing_score
        },
        request=request
    )

    return jsonify({
        'score': score,
        'passed': score >= quiz.passing_score,
        'results': results,
        'total_points': total_points,
        'earned_points': earned_points,
        'attempts_left': quiz.max_attempts - progress.quiz_attempts
    }), 200


@bp.route('/<int:module_id>/comment', methods=['POST'])
@login_required
def add_comment(module_id):
    """添加评论"""
    module = LearningModule.query.get_or_404(module_id)

    if request.is_json:
        data = request.get_json()
        content = data.get('content', '').strip()
    else:
        content = request.form.get('content', '').strip()

    if not content:
        if request.is_json:
            return jsonify({'error': '评论内容不能为空'}), 400
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('learning.module_detail', slug=module.slug))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        module_id=module_id
    )
    db.session.add(comment)
    current_user.add_points(5)

    try:
        db.session.commit()
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

    return redirect(url_for('learning.module_detail', slug=module.slug))


@bp.route('/<int:module_id>/rate', methods=['POST'])
@login_required
def rate_module(module_id):
    """评分学习模块"""
    module = LearningModule.query.get_or_404(module_id)

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
        return redirect(url_for('learning.module_detail', slug=module.slug))

    # 检查是否已经评分
    existing_rating = Rating.query.filter_by(
        user_id=current_user.id,
        module_id=module_id
    ).first()

    if existing_rating:
        existing_rating.score = score
        existing_rating.review = review
        message = '评分已更新'
    else:
        rating = Rating(
            score=score,
            review=review,
            user_id=current_user.id,
            module_id=module_id
        )
        db.session.add(rating)
        current_user.add_points(3)
        message = '评分成功，获得3积分！'

    try:
        db.session.commit()
        if request.is_json:
            return jsonify({'message': message}), 200
        flash(message, 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': '评分失败'}), 500
        flash('评分失败，请稍后重试', 'danger')

    return redirect(url_for('learning.module_detail', slug=module.slug))
