"""
评论模型 - 管理用户评论
"""
from datetime import datetime
from app import db


class Comment(db.Model):
    """评论模型"""

    __tablename__ = 'comments'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    # 关联
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'))
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'))

    # 父评论（用于回复功能）
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic', cascade='all, delete-orphan')

    # 互动统计
    like_count = db.Column(db.Integer, default=0)
    dislike_count = db.Column(db.Integer, default=0)

    # 状态
    is_approved = db.Column(db.Boolean, default=True)  # 是否通过审核
    is_pinned = db.Column(db.Boolean, default=False)  # 是否置顶
    is_deleted = db.Column(db.Boolean, default=False)  # 软删除

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Comment {self.id} by User {self.user_id}>'

    def to_dict(self, include_user=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'content': self.content,
            'like_count': self.like_count,
            'dislike_count': self.dislike_count,
            'is_pinned': self.is_pinned,
            'reply_count': self.replies.filter_by(is_deleted=False).count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_user and self.author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'nickname': self.author.nickname or self.author.username,
                'avatar': self.author.avatar,
                'level': self.author.level
            }

        if self.parent_id:
            data['parent_id'] = self.parent_id

        return data

    def increment_like(self):
        """增加点赞"""
        self.like_count += 1
        db.session.commit()

    def increment_dislike(self):
        """增加踩"""
        self.dislike_count += 1
        db.session.commit()

    def soft_delete(self):
        """软删除评论"""
        self.is_deleted = True
        db.session.commit()

    @staticmethod
    def get_recent_comments(limit=10):
        """获取最新评论"""
        return Comment.query.filter_by(is_deleted=False, is_approved=True)\
                           .order_by(Comment.created_at.desc())\
                           .limit(limit).all()

    @staticmethod
    def get_story_comments(story_id, limit=None):
        """获取故事的评论"""
        query = Comment.query.filter_by(
            story_id=story_id,
            is_deleted=False,
            is_approved=True,
            parent_id=None  # 只获取顶级评论
        ).order_by(Comment.is_pinned.desc(), Comment.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()
