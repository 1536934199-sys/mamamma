"""
主应用入口 - 中国皮影戏学习平台
"""
import os
from dotenv import load_dotenv
from app import create_app, db

# 加载环境变量
load_dotenv()

# 创建应用实例
app = create_app(os.environ.get('FLASK_ENV', 'development'))


# CLI命令
@app.cli.command()
def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        from app.utils.init_data import init_database
        init_database()
        print("数据库初始化完成！")


@app.cli.command()
def create_admin():
    """创建管理员账户"""
    from app.models import User
    username = input("请输入管理员用户名: ")
    email = input("请输入管理员邮箱: ")
    password = input("请输入管理员密码: ")

    if User.query.filter_by(username=username).first():
        print("用户名已存在！")
        return

    admin = User.create_user(
        username=username,
        email=email,
        password=password,
        is_admin=True,
        email_verified=True
    )
    db.session.commit()
    print(f"管理员账户 {username} 创建成功！")


@app.shell_context_processor
def make_shell_context():
    """Flask Shell上下文"""
    from app.models import (User, Story, Character, Comment, LearningModule,
                           Quiz, QuizQuestion, UserProgress, Rating,
                           UserActivity, ContentView)
    return {
        'db': db,
        'User': User,
        'Story': Story,
        'Character': Character,
        'Comment': Comment,
        'LearningModule': LearningModule,
        'Quiz': Quiz,
        'QuizQuestion': QuizQuestion,
        'UserProgress': UserProgress,
        'Rating': Rating,
        'UserActivity': UserActivity,
        'ContentView': ContentView
    }


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
