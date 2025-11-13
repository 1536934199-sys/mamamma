"""
认证路由 - 处理用户注册、登录、登出
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, UserActivity
from datetime import datetime
import re

bp = Blueprint('auth', __name__)


def is_valid_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_username(username):
    """验证用户名格式"""
    # 用户名：3-20个字符，只能包含字母、数字、下划线
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # 处理JSON请求（API）
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
        else:
            # 处理表单请求
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

        # 验证输入
        errors = []

        if not username:
            errors.append('用户名不能为空')
        elif not is_valid_username(username):
            errors.append('用户名格式无效（3-20个字符，只能包含字母、数字、下划线）')
        elif User.query.filter_by(username=username).first():
            errors.append('用户名已存在')

        if not email:
            errors.append('邮箱不能为空')
        elif not is_valid_email(email):
            errors.append('邮箱格式无效')
        elif User.query.filter_by(email=email).first():
            errors.append('邮箱已被注册')

        if not password:
            errors.append('密码不能为空')
        elif len(password) < 6:
            errors.append('密码至少需要6个字符')
        elif password != confirm_password:
            errors.append('两次输入的密码不一致')

        if errors:
            if request.is_json:
                return jsonify({'error': errors}), 400
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

        # 创建用户
        try:
            user = User.create_user(
                username=username,
                email=email,
                password=password,
                nickname=username
            )
            db.session.commit()

            # 记录活动
            UserActivity.log_activity(
                user_id=user.id,
                activity_type='register',
                details={'username': username},
                request=request
            )

            if request.is_json:
                # API响应
                access_token = create_access_token(identity=user.id)
                refresh_token = create_refresh_token(identity=user.id)
                return jsonify({
                    'message': '注册成功',
                    'user': user.to_dict(),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }), 201
            else:
                # 网页响应
                flash('注册成功！请登录', 'success')
                return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': '注册失败', 'message': str(e)}), 500
            flash('注册失败，请稍后重试', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # 处理JSON请求（API）
        if request.is_json:
            data = request.get_json()
            username_or_email = data.get('username', '').strip()
            password = data.get('password', '')
            remember = data.get('remember', False)
        else:
            # 处理表单请求
            username_or_email = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)

        # 验证输入
        if not username_or_email or not password:
            if request.is_json:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            flash('用户名和密码不能为空', 'danger')
            return render_template('auth/login.html')

        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user or not user.check_password(password):
            if request.is_json:
                return jsonify({'error': '用户名或密码错误'}), 401
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            if request.is_json:
                return jsonify({'error': '账户已被禁用'}), 403
            flash('账户已被禁用，请联系管理员', 'danger')
            return render_template('auth/login.html')

        # 登录成功
        user.update_last_login()

        # 记录活动
        UserActivity.log_activity(
            user_id=user.id,
            activity_type='login',
            details={'method': 'web' if not request.is_json else 'api'},
            request=request
        )

        if request.is_json:
            # API响应 - 返回JWT令牌
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return jsonify({
                'message': '登录成功',
                'user': user.to_dict(include_email=True),
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 200
        else:
            # 网页响应 - 使用Flask-Login
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            flash(f'欢迎回来，{user.nickname or user.username}！', 'success')
            return redirect(url_for('main.index'))

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    # 记录活动
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='logout',
        request=request
    )

    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('main.index'))


@bp.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    stats = current_user.get_learning_stats()
    return render_template('auth/profile.html', user=current_user, stats=stats)


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        bio = request.form.get('bio', '').strip()
        location = request.form.get('location', '').strip()
        language = request.form.get('language', 'zh_CN')

        # 更新资料
        if nickname:
            current_user.nickname = nickname
        if bio:
            current_user.bio = bio
        if location:
            current_user.location = location
        if language in ['zh_CN', 'en_US']:
            current_user.language = language
            session['language'] = language

        try:
            db.session.commit()
            flash('资料更新成功', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('更新失败，请稍后重试', 'danger')

    return render_template('auth/edit_profile.html')


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 验证
        if not current_user.check_password(current_password):
            flash('当前密码错误', 'danger')
            return render_template('auth/change_password.html')

        if len(new_password) < 6:
            flash('新密码至少需要6个字符', 'danger')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return render_template('auth/change_password.html')

        # 更新密码
        current_user.set_password(new_password)
        try:
            db.session.commit()
            flash('密码修改成功', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('修改失败，请稍后重试', 'danger')

    return render_template('auth/change_password.html')


# API端点
@bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': new_access_token}), 200


@bp.route('/api/me')
@jwt_required()
def api_get_current_user():
    """获取当前用户信息（API）"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    return jsonify({'user': user.to_dict(include_email=True)}), 200
