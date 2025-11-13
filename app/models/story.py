"""
故事模型 - 管理皮影戏故事
"""
from datetime import datetime
from app import db


# 故事和角色的多对多关系表
story_characters = db.Table('story_characters',
    db.Column('story_id', db.Integer, db.ForeignKey('stories.id'), primary_key=True),
    db.Column('character_id', db.Integer, db.ForeignKey('characters.id'), primary_key=True),
    db.Column('role_description', db.String(200)),  # 角色在故事中的描述
    db.Column('order', db.Integer, default=0)  # 出场顺序
)


class Story(db.Model):
    """皮影戏故事模型"""

    __tablename__ = 'stories'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    title_en = db.Column(db.String(200))  # 英文标题
    slug = db.Column(db.String(200), unique=True, index=True)  # URL友好的标识符

    # 内容
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text)  # 英文描述
    full_content = db.Column(db.Text)  # 完整故事内容
    full_content_en = db.Column(db.Text)

    # 媒体文件
    thumbnail = db.Column(db.String(200))  # 缩略图
    video_url = db.Column(db.String(500))  # 视频URL
    images = db.Column(db.JSON)  # 故事图片集 JSON数组

    # 分类和标签
    category = db.Column(db.String(50), index=True)  # 神话、历史、民间传说等
    tags = db.Column(db.JSON)  # 标签数组
    difficulty_level = db.Column(db.Integer, default=1)  # 难度等级 1-5

    # 统计信息
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)

    # 状态
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # 是否为精选故事

    # 时间信息
    duration = db.Column(db.Integer)  # 视频时长（秒）
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)

    # 创作者信息
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = db.relationship('User', backref='stories')

    # 关系
    characters = db.relationship('Character', secondary=story_characters,
                                backref=db.backref('stories', lazy='dynamic'))
    comments = db.relationship('Comment', backref='story', lazy='dynamic',
                              cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='story', lazy='dynamic',
                             cascade='all, delete-orphan')
    scenes = db.relationship('Scene', backref='story', lazy='dynamic',
                            cascade='all, delete-orphan', order_by='Scene.order')

    def __repr__(self):
        return f'<Story {self.title}>'

    def to_dict(self, include_content=False, language='zh_CN'):
        """转换为字典"""
        is_english = language == 'en_US'

        data = {
            'id': self.id,
            'title': self.title_en if is_english and self.title_en else self.title,
            'slug': self.slug,
            'description': self.description_en if is_english and self.description_en else self.description,
            'thumbnail': self.thumbnail,
            'video_url': self.video_url,
            'category': self.category,
            'tags': self.tags or [],
            'difficulty_level': self.difficulty_level,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'share_count': self.share_count,
            'is_featured': self.is_featured,
            'duration': self.duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'average_rating': self.get_average_rating(),
            'total_comments': self.comments.count()
        }

        if include_content:
            data['full_content'] = self.full_content_en if is_english and self.full_content_en else self.full_content
            data['images'] = self.images or []
            data['characters'] = [char.to_dict(language=language) for char in self.characters]
            data['scenes'] = [scene.to_dict(language=language) for scene in self.scenes]

        return data

    def get_average_rating(self):
        """获取平均评分"""
        avg = db.session.query(db.func.avg(Rating.score)).filter_by(story_id=self.id).scalar()
        return round(avg, 2) if avg else 0

    def increment_view(self):
        """增加浏览次数"""
        self.view_count += 1
        db.session.commit()

    def increment_like(self):
        """增加点赞次数"""
        self.like_count += 1
        db.session.commit()

    def increment_share(self):
        """增加分享次数"""
        self.share_count += 1
        db.session.commit()

    @staticmethod
    def get_featured_stories(limit=5):
        """获取精选故事"""
        return Story.query.filter_by(is_published=True, is_featured=True)\
                         .order_by(Story.created_at.desc())\
                         .limit(limit).all()

    @staticmethod
    def get_popular_stories(limit=10):
        """获取热门故事"""
        return Story.query.filter_by(is_published=True)\
                         .order_by(Story.view_count.desc())\
                         .limit(limit).all()


class Scene(db.Model):
    """场景模型 - 故事中的各个场景"""

    __tablename__ = 'scenes'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)

    # 场景信息
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text)

    # 媒体
    image_url = db.Column(db.String(500))
    audio_url = db.Column(db.String(500))  # 配音或音乐

    # 顺序和时间
    order = db.Column(db.Integer, default=0, nullable=False)
    start_time = db.Column(db.Integer)  # 视频中的开始时间（秒）
    end_time = db.Column(db.Integer)  # 视频中的结束时间（秒）

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Scene {self.title}>'

    def to_dict(self, language='zh_CN'):
        """转换为字典"""
        is_english = language == 'en_US'
        return {
            'id': self.id,
            'title': self.title_en if is_english and self.title_en else self.title,
            'description': self.description_en if is_english and self.description_en else self.description,
            'image_url': self.image_url,
            'audio_url': self.audio_url,
            'order': self.order,
            'start_time': self.start_time,
            'end_time': self.end_time
        }
