"""
分析模型 - 管理用户行为和内容浏览数据
"""
from datetime import datetime
from app import db


class UserActivity(db.Model):
    """用户活动记录模型"""

    __tablename__ = 'user_activities'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 活动类型
    activity_type = db.Column(db.String(50), nullable=False, index=True)
    # 类型包括: view_story, complete_module, submit_comment, rate_content,
    # share_content, login, logout, quiz_attempt, etc.

    # 活动详情（JSON格式存储相关数据）
    details = db.Column(db.JSON)
    # 例如: {"story_id": 123, "duration": 300} 或 {"module_id": 45, "score": 85}

    # IP和设备信息
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    device_type = db.Column(db.String(50))  # mobile, tablet, desktop

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f'<UserActivity {self.activity_type} by User {self.user_id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'details': self.details or {},
            'device_type': self.device_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def log_activity(user_id, activity_type, details=None, request=None):
        """记录用户活动"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            details=details or {}
        )

        if request:
            activity.ip_address = request.remote_addr
            activity.user_agent = request.headers.get('User-Agent', '')
            # 简单的设备类型检测
            user_agent = activity.user_agent.lower()
            if 'mobile' in user_agent:
                activity.device_type = 'mobile'
            elif 'tablet' in user_agent or 'ipad' in user_agent:
                activity.device_type = 'tablet'
            else:
                activity.device_type = 'desktop'

        db.session.add(activity)
        db.session.commit()
        return activity

    @staticmethod
    def get_user_activities(user_id, limit=50):
        """获取用户活动历史"""
        return UserActivity.query.filter_by(user_id=user_id)\
                                 .order_by(UserActivity.created_at.desc())\
                                 .limit(limit).all()

    @staticmethod
    def get_activity_stats(user_id, days=30):
        """获取用户活动统计"""
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)
        activities = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= start_date
        ).all()

        stats = {
            'total_activities': len(activities),
            'by_type': {},
            'by_device': {}
        }

        for activity in activities:
            # 按类型统计
            activity_type = activity.activity_type
            stats['by_type'][activity_type] = stats['by_type'].get(activity_type, 0) + 1

            # 按设备统计
            device_type = activity.device_type or 'unknown'
            stats['by_device'][device_type] = stats['by_device'].get(device_type, 0) + 1

        return stats


class ContentView(db.Model):
    """内容浏览记录模型"""

    __tablename__ = 'content_views'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)

    # 关联
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 可为空（匿名用户）
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'))
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'))

    # 浏览信息
    duration = db.Column(db.Integer)  # 浏览时长（秒）
    completed = db.Column(db.Boolean, default=False)  # 是否看完

    # 来源信息
    referrer = db.Column(db.String(500))  # 来源URL
    search_query = db.Column(db.String(200))  # 搜索关键词（如果是通过搜索来的）

    # IP和设备信息
    ip_address = db.Column(db.String(50))
    device_type = db.Column(db.String(50))

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    user = db.relationship('User', backref='content_views')
    story = db.relationship('Story', backref='views')
    module = db.relationship('LearningModule', backref='views')

    def __repr__(self):
        return f'<ContentView story={self.story_id} module={self.module_id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'story_id': self.story_id,
            'module_id': self.module_id,
            'duration': self.duration,
            'completed': self.completed,
            'device_type': self.device_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def log_view(story_id=None, module_id=None, user_id=None, duration=None,
                 completed=False, request=None):
        """记录内容浏览"""
        view = ContentView(
            user_id=user_id,
            story_id=story_id,
            module_id=module_id,
            duration=duration,
            completed=completed
        )

        if request:
            view.ip_address = request.remote_addr
            view.referrer = request.referrer
            user_agent = request.headers.get('User-Agent', '').lower()
            if 'mobile' in user_agent:
                view.device_type = 'mobile'
            elif 'tablet' in user_agent or 'ipad' in user_agent:
                view.device_type = 'tablet'
            else:
                view.device_type = 'desktop'

        db.session.add(view)
        db.session.commit()
        return view

    @staticmethod
    def get_popular_content(content_type='story', limit=10, days=30):
        """获取热门内容"""
        from datetime import timedelta
        from sqlalchemy import func

        start_date = datetime.utcnow() - timedelta(days=days)

        if content_type == 'story':
            result = db.session.query(
                ContentView.story_id,
                func.count(ContentView.id).label('view_count')
            ).filter(
                ContentView.story_id.isnot(None),
                ContentView.created_at >= start_date
            ).group_by(ContentView.story_id)\
             .order_by(func.count(ContentView.id).desc())\
             .limit(limit).all()

            return [{'story_id': r[0], 'views': r[1]} for r in result]

        elif content_type == 'module':
            result = db.session.query(
                ContentView.module_id,
                func.count(ContentView.id).label('view_count')
            ).filter(
                ContentView.module_id.isnot(None),
                ContentView.created_at >= start_date
            ).group_by(ContentView.module_id)\
             .order_by(func.count(ContentView.id).desc())\
             .limit(limit).all()

            return [{'module_id': r[0], 'views': r[1]} for r in result]

        return []

    @staticmethod
    def get_view_stats(story_id=None, module_id=None, days=30):
        """获取内容浏览统计"""
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)
        query = ContentView.query.filter(ContentView.created_at >= start_date)

        if story_id:
            query = query.filter_by(story_id=story_id)
        elif module_id:
            query = query.filter_by(module_id=module_id)

        views = query.all()

        total_views = len(views)
        total_duration = sum(v.duration for v in views if v.duration)
        completed_views = sum(1 for v in views if v.completed)
        unique_users = len(set(v.user_id for v in views if v.user_id))

        return {
            'total_views': total_views,
            'unique_users': unique_users,
            'average_duration': round(total_duration / total_views, 2) if total_views > 0 else 0,
            'completion_rate': round(completed_views / total_views * 100, 2) if total_views > 0 else 0
        }
