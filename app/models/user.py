"""
用户模型 - 管理用户账户和认证
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    """用户模型"""

    __tablename__ = 'users'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # 个人资料
    nickname = db.Column(db.String(100))
    avatar = db.Column(db.String(200), default='default_avatar.png')
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))

    # 账户状态
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)

    # 偏好设置
    language = db.Column(db.String(10), default='zh_CN')
    theme = db.Column(db.String(20), default='light')

    # 积分系统
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # 关系
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    progress = db.relationship('UserProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    activities = db.relationship('UserActivity', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def add_points(self, points):
        """增加积分并更新等级"""
        self.points += points
        # 简单的等级计算：每100积分升1级
        new_level = (self.points // 100) + 1
        if new_level > self.level:
            self.level = new_level
            return True  # 表示升级了
        return False

    def to_dict(self, include_email=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname or self.username,
            'avatar': self.avatar,
            'bio': self.bio,
            'location': self.location,
            'points': self.points,
            'level': self.level,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        if include_email:
            data['email'] = self.email
            data['email_verified'] = self.email_verified
        return data

    @staticmethod
    def create_user(username, email, password, **kwargs):
        """创建新用户"""
        user = User(username=username, email=email, **kwargs)
        user.set_password(password)
        db.session.add(user)
        return user

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def get_learning_stats(self):
        """获取学习统计"""
        completed_modules = UserProgress.query.filter_by(
            user_id=self.id,
            completed=True
        ).count()

        total_progress = db.session.query(
            db.func.avg(UserProgress.progress)
        ).filter_by(user_id=self.id).scalar() or 0

        return {
            'completed_modules': completed_modules,
            'average_progress': round(total_progress, 2),
            'total_comments': self.comments.count(),
            'total_ratings': self.ratings.count()
        }
