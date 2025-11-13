# 中国皮影戏学习平台

一个全面的中国皮影戏文化学习与交流平台，支持故事展示、互动学习、智能推荐等功能。

## 功能特点

### 核心功能
- **皮影戏故事展示**：精选中国传统皮影戏故事，支持视频播放和场景展示
- **互动学习模块**：系统化的皮影戏知识学习，包括历史、制作工艺、表演技巧等
- **角色库**：收录经典皮影戏角色，详细介绍其特征和背景
- **在线测验**：通过测验巩固学习成果，获取积分奖励
- **学习进度跟踪**：自动记录学习进度，个性化推荐学习内容

### 用户交互
- **评论系统**：支持多级评论和回复功能
- **评分系统**：对故事和学习模块进行评分
- **积分等级**：完成学习任务获取积分，提升用户等级
- **社交分享**：将学习成果分享到社交媒体

### 智能推荐
- **个性化推荐**：基于用户学习历史和兴趣推荐内容
- **协同过滤**：发现相似用户喜欢的内容
- **DeepSeek集成**：使用AI技术提供智能推荐

### 管理后台
- **内容管理**：创建和编辑故事、学习模块、角色
- **用户管理**：管理用户账户和权限
- **数据分析**：查看平台使用统计和趋势分析
- **评论审核**：审核和管理用户评论

### 国际化
- **多语言支持**：支持中文和英文切换
- **双语内容**：故事和学习模块提供中英文版本

## 技术栈

### 后端
- **Flask** - Python Web框架
- **Flask-SQLAlchemy** - ORM数据库操作
- **Flask-Login** - 用户认证管理
- **Flask-JWT-Extended** - JWT令牌认证
- **Flask-Babel** - 国际化支持
- **Flask-CORS** - 跨域请求处理
- **Flask-Migrate** - 数据库迁移

### 前端
- **HTML5/CSS3** - 现代Web标准
- **JavaScript (ES6+)** - 交互逻辑
- **Fetch API** - 异步数据加载

### 数据库
- **SQLite** (开发环境)
- **PostgreSQL** (生产环境推荐)

### API集成
- **DeepSeek API** - AI智能推荐

## 快速开始

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd mamamma
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

5. **初始化数据库**
```bash
flask init-db
```

6. **运行应用**
```bash
python app.py
```

访问 http://localhost:5000 查看应用

### 创建管理员账户
```bash
flask create-admin
```

## 项目结构

```
mamamma/
├── app/                    # 应用包
│   ├── __init__.py        # 应用工厂
│   ├── models/            # 数据库模型
│   │   ├── user.py        # 用户模型
│   │   ├── story.py       # 故事模型
│   │   ├── character.py   # 角色模型
│   │   ├── comment.py     # 评论模型
│   │   ├── learning.py    # 学习模块
│   │   ├── rating.py      # 评分模型
│   │   └── analytics.py   # 分析模型
│   ├── routes/            # 路由蓝图
│   │   ├── auth.py        # 认证路由
│   │   ├── main.py        # 主页面路由
│   │   ├── stories.py     # 故事路由
│   │   ├── learning.py    # 学习路由
│   │   ├── api.py         # API路由
│   │   └── admin.py       # 管理员路由
│   ├── services/          # 业务逻辑服务
│   │   ├── deepseek.py    # DeepSeek集成
│   │   └── recommendation.py  # 推荐系统
│   └── utils/             # 工具函数
│       ├── helpers.py     # 辅助函数
│       ├── decorators.py  # 装饰器
│       └── init_data.py   # 数据初始化
├── static/                # 静态文件
│   ├── css/              # 样式文件
│   ├── js/               # JavaScript文件
│   └── images/           # 图片资源
├── templates/            # HTML模板
├── tests/               # 测试文件
├── migrations/          # 数据库迁移
├── config.py           # 配置文件
├── app.py              # 应用入口
└── requirements.txt    # 项目依赖

```

## API文档

### 认证API
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `GET /auth/logout` - 用户登出
- `POST /auth/api/refresh` - 刷新令牌

### 故事API
- `GET /api/stories` - 获取故事列表
- `GET /api/stories/<id>` - 获取故事详情
- `GET /api/stories/<id>/comments` - 获取故事评论
- `POST /stories/<id>/comment` - 添加评论
- `POST /stories/<id>/rate` - 评分故事
- `POST /stories/<id>/like` - 点赞故事

### 学习模块API
- `GET /api/modules` - 获取学习模块列表
- `GET /api/modules/<id>` - 获取模块详情
- `POST /learning/<id>/update-progress` - 更新学习进度
- `POST /learning/<id>/complete` - 完成模块

### 推荐API
- `GET /api/recommendations` - 获取个性化推荐
- `GET /api/stats/trending` - 获取趋势内容

## 测试

运行测试：
```bash
pytest
```

运行测试并查看覆盖率：
```bash
pytest --cov=app tests/
```

## 部署

### 使用Gunicorn部署
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 使用Docker部署
```bash
# 构建镜像
docker build -t shadowpuppet-platform .

# 运行容器
docker run -p 5000:5000 shadowpuppet-platform
```

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

MIT License

## 联系方式

项目链接: [GitHub Repository]

## 致谢

- 中国非物质文化遗产 - 皮影戏
- Flask框架及其生态系统
- 所有贡献者
