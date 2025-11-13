"""
基础测试
"""
import pytest
from app import create_app, db
from app.models import User, Story, LearningModule


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI runner"""
    return app.test_cli_runner()


class TestUser:
    """用户模型测试"""

    def test_password_hashing(self, app):
        """测试密码哈希"""
        user = User(username='test', email='test@example.com')
        user.set_password('password123')
        assert user.password_hash is not None
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')

    def test_user_creation(self, app):
        """测试用户创建"""
        user = User.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.points == 0
        assert user.level == 1

    def test_add_points(self, app):
        """测试积分系统"""
        user = User.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.commit()

        # 增加积分
        user.add_points(150)
        assert user.points == 150
        assert user.level == 2  # 每100分升1级

        user.add_points(50)
        assert user.points == 200
        assert user.level == 3


class TestStory:
    """故事模型测试"""

    def test_story_creation(self, app):
        """测试故事创建"""
        user = User.create_user(
            username='admin',
            email='admin@example.com',
            password='password123'
        )
        db.session.commit()

        story = Story(
            title='测试故事',
            slug='test-story',
            description='这是一个测试故事',
            category='神话传说',
            author_id=user.id
        )
        db.session.add(story)
        db.session.commit()

        assert story.id is not None
        assert story.view_count == 0
        assert story.like_count == 0

    def test_increment_view(self, app):
        """测试浏览计数"""
        story = Story(
            title='测试故事',
            slug='test-story',
            description='测试',
            category='神话传说'
        )
        db.session.add(story)
        db.session.commit()

        initial_count = story.view_count
        story.increment_view()
        assert story.view_count == initial_count + 1


class TestAPI:
    """API测试"""

    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'

    def test_get_stories(self, client, app):
        """测试获取故事列表"""
        # 创建测试故事
        story = Story(
            title='测试故事',
            slug='test-story',
            description='测试',
            category='神话传说',
            is_published=True
        )
        db.session.add(story)
        db.session.commit()

        response = client.get('/api/stories')
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert len(data['items']) > 0


class TestAuth:
    """认证测试"""

    def test_register(self, client):
        """测试用户注册"""
        response = client.post('/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data

    def test_login(self, client, app):
        """测试用户登录"""
        # 创建用户
        user = User.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.commit()

        # 登录
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data

    def test_invalid_login(self, client):
        """测试无效登录"""
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401


def test_app_exists(app):
    """测试应用实例"""
    assert app is not None


def test_app_is_testing(app):
    """测试应用配置"""
    assert app.config['TESTING']
