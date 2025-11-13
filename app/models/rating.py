"""
评分模型 - 管理用户对故事和模块的评分
"""
from datetime import datetime
from app import db


class Rating(db.Model):
    """评分模型"""

    __tablename__ = 'ratings'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)  # 评分 1-5

    # 关联
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'))
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'))

    # 评价内容（可选）
    review = db.Column(db.Text)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 唯一约束：一个用户只能对一个故事/模块评分一次
    __table_args__ = (
        db.UniqueConstraint('user_id', 'story_id', name='unique_user_story_rating'),
        db.UniqueConstraint('user_id', 'module_id', name='unique_user_module_rating'),
    )

    def __repr__(self):
        return f'<Rating {self.score} by User {self.user_id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'score': self.score,
            'review': self.review,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'nickname': self.user.nickname or self.user.username,
                'avatar': self.user.avatar
            } if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_average_rating(story_id=None, module_id=None):
        """获取平均评分"""
        if story_id:
            avg = db.session.query(db.func.avg(Rating.score)).filter_by(story_id=story_id).scalar()
        elif module_id:
            avg = db.session.query(db.func.avg(Rating.score)).filter_by(module_id=module_id).scalar()
        else:
            return 0

        return round(avg, 2) if avg else 0

    @staticmethod
    def get_rating_distribution(story_id=None, module_id=None):
        """获取评分分布"""
        query = Rating.query
        if story_id:
            query = query.filter_by(story_id=story_id)
        elif module_id:
            query = query.filter_by(module_id=module_id)

        distribution = {i: 0 for i in range(1, 6)}
        ratings = query.all()

        for rating in ratings:
            distribution[rating.score] += 1

        return distribution
