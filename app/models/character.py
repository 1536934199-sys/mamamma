"""
角色模型 - 管理皮影戏角色
"""
from datetime import datetime
from app import db


class Character(db.Model):
    """皮影戏角色模型"""

    __tablename__ = 'characters'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    name_en = db.Column(db.String(100))  # 英文名称

    # 描述
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)
    background = db.Column(db.Text)  # 背景故事
    background_en = db.Column(db.Text)

    # 特征
    character_type = db.Column(db.String(50))  # 英雄、反派、神仙、动物等
    personality_traits = db.Column(db.JSON)  # 性格特征数组
    special_abilities = db.Column(db.JSON)  # 特殊能力

    # 外观
    image_url = db.Column(db.String(500))  # 角色形象图片
    shadow_puppet_image = db.Column(db.String(500))  # 皮影形象
    color_scheme = db.Column(db.String(100))  # 配色方案

    # 元数据
    origin = db.Column(db.String(100))  # 起源（如：西游记、民间传说）
    historical_period = db.Column(db.String(100))  # 历史时期

    # 统计
    popularity_score = db.Column(db.Integer, default=0)

    # 状态
    is_active = db.Column(db.Boolean, default=True)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Character {self.name}>'

    def to_dict(self, language='zh_CN'):
        """转换为字典"""
        is_english = language == 'en_US'
        return {
            'id': self.id,
            'name': self.name_en if is_english and self.name_en else self.name,
            'description': self.description_en if is_english and self.description_en else self.description,
            'background': self.background_en if is_english and self.background_en else self.background,
            'character_type': self.character_type,
            'personality_traits': self.personality_traits or [],
            'special_abilities': self.special_abilities or [],
            'image_url': self.image_url,
            'shadow_puppet_image': self.shadow_puppet_image,
            'color_scheme': self.color_scheme,
            'origin': self.origin,
            'historical_period': self.historical_period,
            'popularity_score': self.popularity_score,
            'story_count': len(self.stories.all())
        }

    def increment_popularity(self):
        """增加人气值"""
        self.popularity_score += 1
        db.session.commit()
