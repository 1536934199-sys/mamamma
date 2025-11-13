"""
学习模型 - 管理学习模块、测验和用户进度
"""
from datetime import datetime
from app import db


class LearningModule(db.Model):
    """学习模块模型"""

    __tablename__ = 'learning_modules'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))
    slug = db.Column(db.String(200), unique=True, index=True)

    # 内容
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)  # 学习内容（支持Markdown）
    content_en = db.Column(db.Text)

    # 分类
    category = db.Column(db.String(100))  # 表演技巧、文化背景、制作工艺等
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5
    order = db.Column(db.Integer, default=0)  # 课程顺序

    # 媒体资源
    video_url = db.Column(db.String(500))
    thumbnail = db.Column(db.String(200))
    resources = db.Column(db.JSON)  # 额外资源链接

    # 学习要求
    prerequisites = db.Column(db.JSON)  # 前置课程ID数组
    estimated_duration = db.Column(db.Integer)  # 预计学习时长（分钟）
    points_reward = db.Column(db.Integer, default=10)  # 完成后获得的积分

    # 统计
    enrollment_count = db.Column(db.Integer, default=0)
    completion_count = db.Column(db.Integer, default=0)

    # 状态
    is_published = db.Column(db.Boolean, default=True)
    is_free = db.Column(db.Boolean, default=True)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    quizzes = db.relationship('Quiz', backref='module', lazy='dynamic',
                             cascade='all, delete-orphan')
    progress = db.relationship('UserProgress', backref='module', lazy='dynamic',
                              cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='learning_module', lazy='dynamic',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<LearningModule {self.title}>'

    def to_dict(self, include_content=False, language='zh_CN'):
        """转换为字典"""
        is_english = language == 'en_US'
        data = {
            'id': self.id,
            'title': self.title_en if is_english and self.title_en else self.title,
            'slug': self.slug,
            'description': self.description_en if is_english and self.description_en else self.description,
            'category': self.category,
            'difficulty_level': self.difficulty_level,
            'order': self.order,
            'thumbnail': self.thumbnail,
            'video_url': self.video_url,
            'estimated_duration': self.estimated_duration,
            'points_reward': self.points_reward,
            'enrollment_count': self.enrollment_count,
            'completion_count': self.completion_count,
            'completion_rate': self.get_completion_rate(),
            'quiz_count': self.quizzes.count()
        }

        if include_content:
            data['content'] = self.content_en if is_english and self.content_en else self.content
            data['resources'] = self.resources or []
            data['prerequisites'] = self.prerequisites or []

        return data

    def get_completion_rate(self):
        """获取完成率"""
        if self.enrollment_count == 0:
            return 0
        return round((self.completion_count / self.enrollment_count) * 100, 2)

    def increment_enrollment(self):
        """增加注册人数"""
        self.enrollment_count += 1
        db.session.commit()

    def increment_completion(self):
        """增加完成人数"""
        self.completion_count += 1
        db.session.commit()


class Quiz(db.Model):
    """测验模型"""

    __tablename__ = 'quizzes'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))

    # 关联
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)

    # 设置
    time_limit = db.Column(db.Integer)  # 时间限制（分钟）
    passing_score = db.Column(db.Integer, default=60)  # 及格分数
    max_attempts = db.Column(db.Integer, default=3)  # 最大尝试次数
    shuffle_questions = db.Column(db.Boolean, default=True)  # 是否打乱题目顺序

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    questions = db.relationship('QuizQuestion', backref='quiz', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='QuizQuestion.order')

    def __repr__(self):
        return f'<Quiz {self.title}>'

    def to_dict(self, language='zh_CN'):
        """转换为字典"""
        is_english = language == 'en_US'
        return {
            'id': self.id,
            'title': self.title_en if is_english and self.title_en else self.title,
            'time_limit': self.time_limit,
            'passing_score': self.passing_score,
            'max_attempts': self.max_attempts,
            'question_count': self.questions.count()
        }


class QuizQuestion(db.Model):
    """测验问题模型"""

    __tablename__ = 'quiz_questions'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)

    # 问题内容
    question_text = db.Column(db.Text, nullable=False)
    question_text_en = db.Column(db.Text)
    question_type = db.Column(db.String(50), default='multiple_choice')  # 单选、多选、填空、判断
    order = db.Column(db.Integer, default=0)

    # 选项（JSON格式）
    options = db.Column(db.JSON)  # [{"id": "a", "text": "选项A"}, ...]
    options_en = db.Column(db.JSON)

    # 答案
    correct_answer = db.Column(db.JSON)  # 正确答案（可能是单个或多个）
    explanation = db.Column(db.Text)  # 答案解释
    explanation_en = db.Column(db.Text)

    # 评分
    points = db.Column(db.Integer, default=1)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuizQuestion {self.id}>'

    def to_dict(self, include_answer=False, language='zh_CN'):
        """转换为字典"""
        is_english = language == 'en_US'
        data = {
            'id': self.id,
            'question_text': self.question_text_en if is_english and self.question_text_en else self.question_text,
            'question_type': self.question_type,
            'options': self.options_en if is_english and self.options_en else self.options,
            'points': self.points,
            'order': self.order
        }

        if include_answer:
            data['correct_answer'] = self.correct_answer
            data['explanation'] = self.explanation_en if is_english and self.explanation_en else self.explanation

        return data

    def check_answer(self, user_answer):
        """检查答案是否正确"""
        if isinstance(self.correct_answer, list):
            return set(user_answer) == set(self.correct_answer)
        return user_answer == self.correct_answer


class QuizAnswer(db.Model):
    """用户测验答题记录"""

    __tablename__ = 'quiz_answers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)

    # 答案
    user_answer = db.Column(db.JSON)  # 用户的答案
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Integer, default=0)

    # 时间
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    time_spent = db.Column(db.Integer)  # 答题用时（秒）

    # 关系
    user = db.relationship('User', backref='quiz_answers')
    quiz = db.relationship('Quiz', backref='answers')
    question = db.relationship('QuizQuestion', backref='answers')

    def __repr__(self):
        return f'<QuizAnswer user={self.user_id} question={self.question_id}>'


class UserProgress(db.Model):
    """用户学习进度模型"""

    __tablename__ = 'user_progress'

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)

    # 进度信息
    progress = db.Column(db.Float, default=0.0)  # 0-100
    completed = db.Column(db.Boolean, default=False)
    last_position = db.Column(db.String(100))  # 上次学习位置

    # 测验成绩
    quiz_attempts = db.Column(db.Integer, default=0)
    best_quiz_score = db.Column(db.Integer, default=0)
    quiz_passed = db.Column(db.Boolean, default=False)

    # 时间统计
    time_spent = db.Column(db.Integer, default=0)  # 学习时长（分钟）
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)

    # 笔记
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<UserProgress user={self.user_id} module={self.module_id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'module_id': self.module_id,
            'progress': self.progress,
            'completed': self.completed,
            'quiz_attempts': self.quiz_attempts,
            'best_quiz_score': self.best_quiz_score,
            'quiz_passed': self.quiz_passed,
            'time_spent': self.time_spent,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }

    def update_progress(self, progress_value):
        """更新学习进度"""
        self.progress = min(100, max(0, progress_value))
        self.last_accessed = datetime.utcnow()

        if self.progress >= 100 and not self.completed:
            self.complete()

        db.session.commit()

    def complete(self):
        """标记为完成"""
        self.completed = True
        self.completed_at = datetime.utcnow()
        self.progress = 100

        # 增加用户积分
        if self.user and self.module:
            self.user.add_points(self.module.points_reward)
            self.module.increment_completion()

        db.session.commit()

    def add_time(self, minutes):
        """增加学习时长"""
        self.time_spent += minutes
        self.last_accessed = datetime.utcnow()
        db.session.commit()
