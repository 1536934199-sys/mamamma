"""
数据初始化 - 填充示例数据
"""
from app import db
from app.models import (
    User, Story, Character, LearningModule,
    Quiz, QuizQuestion, Scene
)
from datetime import datetime


def init_database():
    """初始化数据库并填充示例数据"""

    # 检查是否已经有数据
    if User.query.first() is not None:
        return  # 已经初始化过了

    print("正在初始化数据库...")

    # 创建管理员用户
    admin = User.create_user(
        username='admin',
        email='admin@shadowpuppet.com',
        password='admin123',
        nickname='管理员',
        is_admin=True,
        email_verified=True
    )

    # 创建示例用户
    user1 = User.create_user(
        username='zhangsan',
        email='zhangsan@example.com',
        password='password123',
        nickname='张三',
        bio='热爱中国传统文化的学习者',
        points=250,
        level=3
    )

    user2 = User.create_user(
        username='lisi',
        email='lisi@example.com',
        password='password123',
        nickname='李四',
        bio='皮影戏爱好者',
        points=180,
        level=2
    )

    db.session.commit()
    print("✓ 用户创建完成")

    # 创建角色
    characters_data = [
        {
            'name': '孙悟空',
            'name_en': 'Sun Wukong',
            'description': '齐天大圣，拥有七十二变和筋斗云的本领',
            'description_en': 'The Monkey King with 72 transformations and cloud somersault abilities',
            'character_type': '英雄',
            'personality_traits': ['勇敢', '机智', '顽皮', '忠诚'],
            'special_abilities': ['七十二变', '筋斗云', '金箍棒'],
            'origin': '西游记',
            'color_scheme': 'gold-red'
        },
        {
            'name': '龙王',
            'name_en': 'Dragon King',
            'description': '掌管水域的神仙，威严庄重',
            'description_en': 'Divine being who controls the waters, dignified and solemn',
            'character_type': '神仙',
            'personality_traits': ['威严', '公正', '强大'],
            'special_abilities': ['呼风唤雨', '水中遨游'],
            'origin': '中国神话',
            'color_scheme': 'blue-gold'
        },
        {
            'name': '白娘子',
            'name_en': 'White Snake Lady',
            'description': '千年白蛇修炼成人，美丽善良',
            'description_en': 'A thousand-year-old white snake in human form, beautiful and kind',
            'character_type': '仙女',
            'personality_traits': ['善良', '美丽', '坚强', '深情'],
            'special_abilities': ['法术', '变化'],
            'origin': '白蛇传',
            'color_scheme': 'white-silver'
        },
        {
            'name': '包公',
            'name_en': 'Judge Bao',
            'description': '铁面无私的清官，明断是非',
            'description_en': 'Impartial magistrate known for fair judgments',
            'character_type': '英雄',
            'personality_traits': ['公正', '睿智', '正直'],
            'special_abilities': ['明察秋毫', '断案如神'],
            'origin': '历史人物',
            'color_scheme': 'black-gold'
        }
    ]

    characters = []
    for char_data in characters_data:
        char = Character(**char_data)
        db.session.add(char)
        characters.append(char)

    db.session.commit()
    print("✓ 角色创建完成")

    # 创建故事
    stories_data = [
        {
            'title': '月夜龙影',
            'title_en': 'Dragon Shadow in Moonlight',
            'slug': 'dragon-shadow-moonlight',
            'description': '清冷的月光洒在幕布上，少年英雄寻找失踪的神鸟，遇见传说中的龙影。',
            'description_en': 'Under the cold moonlight, a young hero searches for a missing divine bird and encounters the legendary dragon shadow.',
            'full_content': '''在一个宁静的村庄，月光如水般洒落。少年提着灯笼，踏上寻找失踪神鸟的旅程。

传说神鸟能带来村庄的繁荣，但它突然消失了。少年勇敢地走进森林深处，在月光下，他看到了腾云驾雾的龙影。

龙影并非恶龙，它告诉少年，神鸟正在天上修炼，不久就会回来。少年明白后，向龙影道谢，回到村庄等待。

果然，几日后，神鸟归来，村庄重获安宁，而少年也成为了村中的英雄。''',
            'category': '神话传说',
            'tags': ['龙', '英雄', '冒险', '月夜'],
            'difficulty_level': 1,
            'is_featured': True,
            'view_count': 1250,
            'like_count': 89,
            'author_id': admin.id
        },
        {
            'title': '西游记·大闹天宫',
            'title_en': 'Journey to the West: Havoc in Heaven',
            'slug': 'journey-to-west-havoc-in-heaven',
            'description': '孙悟空在花果山修炼成仙，因不满天庭封赏，大闹天宫的故事。',
            'description_en': 'The story of Sun Wukong causing havoc in heaven after becoming dissatisfied with heavenly rewards.',
            'full_content': '''孙悟空在花果山修炼七十二变，学会了筋斗云等本领。玉帝招他上天，封为弼马温。

悟空得知这只是个养马的小官，大怒之下返回花果山，自称"齐天大圣"。玉帝派天兵天将围剿，但都被悟空打败。

最后，观音菩萨和如来佛祖出面，才平息了这场天宫大乱。孙悟空被压在五行山下五百年，等待取经人的到来。''',
            'category': '神话传说',
            'tags': ['孙悟空', '西游记', '天宫', '神话'],
            'difficulty_level': 2,
            'is_featured': True,
            'view_count': 2340,
            'like_count': 156,
            'author_id': admin.id
        },
        {
            'title': '白蛇传·断桥相会',
            'title_en': 'Legend of White Snake: Meeting at Broken Bridge',
            'slug': 'white-snake-broken-bridge',
            'description': '白娘子与许仙在西湖断桥相遇，开启一段人妖殊途的爱情故事。',
            'description_en': 'White Snake Lady meets Xu Xian at the Broken Bridge, beginning a love story between human and spirit.',
            'full_content': '''西湖美景，春雨绵绵。白娘子和小青化身为人，在断桥遇见书生许仙。

许仙为白娘子撑伞，两人一见钟情。此后，白娘子施法帮助许仙开药铺，两人结为夫妻。

然而，法海和尚发现白娘子是蛇妖，多次阻挠他们。白娘子为救许仙，不惜水漫金山，最终却被镇压在雷峰塔下。

这段真挚的爱情故事，感动了无数人，也成为了皮影戏中的经典剧目。''',
            'category': '民间传说',
            'tags': ['白蛇传', '爱情', '西湖', '传说'],
            'difficulty_level': 2,
            'is_featured': False,
            'view_count': 890,
            'like_count': 67,
            'author_id': admin.id
        }
    ]

    stories = []
    for story_data in stories_data:
        story = Story(**story_data)
        db.session.add(story)
        stories.append(story)

    db.session.commit()

    # 为故事添加角色
    stories[0].characters.append(characters[1])  # 月夜龙影 - 龙王
    stories[1].characters.append(characters[0])  # 西游记 - 孙悟空
    stories[2].characters.append(characters[2])  # 白蛇传 - 白娘子

    # 为第一个故事添加场景
    scenes_data = [
        {
            'story_id': stories[0].id,
            'title': '开场：月夜下的村庄',
            'title_en': 'Opening: Village Under Moonlight',
            'description': '清冷的月光洒在幕布上，皮影人物缓缓登场。',
            'description_en': 'Cold moonlight falls on the screen as shadow puppets slowly appear.',
            'order': 1
        },
        {
            'story_id': stories[0].id,
            'title': '英雄初现',
            'title_en': 'Hero Appears',
            'description': '少年英雄提灯而来，寻找失踪的神鸟。',
            'description_en': 'The young hero arrives with a lantern, searching for the missing divine bird.',
            'order': 2
        },
        {
            'story_id': stories[0].id,
            'title': '龙影现身',
            'title_en': 'Dragon Shadow Appears',
            'description': '传说中的龙影腾云驾雾，与少年相遇。',
            'description_en': 'The legendary dragon shadow rides the clouds and meets the young hero.',
            'order': 3
        },
        {
            'story_id': stories[0].id,
            'title': '归于宁静',
            'title_en': 'Return to Peace',
            'description': '龙影归于天空，村庄重获安宁。',
            'description_en': 'The dragon shadow returns to the sky, and the village regains peace.',
            'order': 4
        }
    ]

    for scene_data in scenes_data:
        scene = Scene(**scene_data)
        db.session.add(scene)

    db.session.commit()
    print("✓ 故事和场景创建完成")

    # 创建学习模块
    modules_data = [
        {
            'title': '皮影戏的历史与起源',
            'title_en': 'History and Origin of Shadow Puppetry',
            'slug': 'shadow-puppetry-history',
            'description': '了解中国皮影戏的悠久历史和文化渊源',
            'description_en': 'Learn about the long history and cultural origins of Chinese shadow puppetry',
            'content': '''# 皮影戏的历史

皮影戏，又称"影子戏"或"灯影戏"，是一种古老的中国民间艺术。

## 起源

皮影戏起源于中国汉代，距今已有两千多年的历史。传说汉武帝思念去世的李夫人，术士用兽皮刻成李夫人的形象，在烛光下投影，这便是皮影戏的雏形。

## 发展

- **唐宋时期**：皮影戏逐渐成熟，题材丰富
- **元代**：随着蒙古大军传播到西亚和欧洲
- **明清时期**：达到鼎盛，各地形成不同流派
- **现代**：2011年，中国皮影戏入选联合国教科文组织人类非物质文化遗产名录

## 艺术特色

1. **造型艺术**：雕刻精美，色彩鲜艳
2. **表演技巧**：一人操纵多个人物
3. **音乐伴奏**：结合当地戏曲音乐
4. **故事题材**：神话传说、历史故事、民间传说等

皮影戏不仅是一种娱乐形式，更是中华文化的重要载体。''',
            'category': '文化背景',
            'difficulty_level': 1,
            'order': 1,
            'estimated_duration': 30,
            'points_reward': 10
        },
        {
            'title': '皮影人物制作工艺',
            'title_en': 'Shadow Puppet Crafting Techniques',
            'slug': 'puppet-crafting',
            'description': '学习传统皮影人物的制作方法和工艺技巧',
            'description_en': 'Learn traditional methods and techniques for crafting shadow puppets',
            'content': '''# 皮影人物制作工艺

制作一个精美的皮影人物需要多道工序，每一步都体现着匠人的智慧和技艺。

## 材料准备

- **皮料**：通常选用牛皮或驴皮
- **工具**：刻刀、凿子、砂纸等
- **染料**：天然矿物颜料或植物染料

## 制作步骤

### 1. 选皮刮皮
选择质地细腻的生皮，刮去毛发，浸泡软化。

### 2. 打样描图
在纸上设计人物造型，描绘细节。

### 3. 雕镂刻画
将图样贴在皮上，用刻刀精心雕刻。这是最关键的步骤，需要高超的技艺。

### 4. 着色涂彩
用不同颜色的染料为人物上色，讲究色彩搭配。

### 5. 发汗熨平
用火烘烤使皮革定型，再用热熨斗熨平。

### 6. 组装连缀
将头部、身体、四肢等部件用细线或铁丝连接。

### 7. 装杆
在人物的关键部位安装操纵杆。

## 技艺要点

- **镂空艺术**：适度的镂空既保证强度又增加美感
- **色彩运用**：红色代表忠勇，黑色代表正直，白色代表奸诈
- **关节设计**：合理的关节设置让人物动作更灵活

传统皮影制作是一门综合性艺术，融合了绘画、雕刻、音乐等多种技能。''',
            'category': '制作工艺',
            'difficulty_level': 3,
            'order': 2,
            'estimated_duration': 45,
            'points_reward': 20
        },
        {
            'title': '皮影戏表演技巧',
            'title_en': 'Shadow Puppetry Performance Techniques',
            'slug': 'performance-techniques',
            'description': '掌握皮影戏的基本表演技巧和操纵方法',
            'description_en': 'Master basic performance techniques and manipulation methods',
            'content': '''# 皮影戏表演技巧

皮影戏表演是一门需要手、眼、心协调配合的艺术。

## 基本手法

### 1. 举影
将皮影举起,贴近幕布，使影像清晰。

### 2. 走影
操纵皮影在幕布上移动，表现人物行走。

### 3. 打斗
表现武打场面，需要快速、准确的动作。

### 4. 表情动作
通过细微的操纵表现人物的情感和性格。

## 操纵技巧

- **一人多角**：熟练的艺人能同时操纵多个角色
- **配合唱腔**：动作要与唱词、音乐完美配合
- **空间感**：营造远近、高低的空间效果

## 表演要素

1. **光源控制**：调节光线强度和角度
2. **幕布距离**：控制影像大小
3. **速度节奏**：快慢结合，营造戏剧张力

## 团队协作

一场完整的皮影戏演出通常需要：
- 前台操纵者（2-3人）
- 后台伴奏者（3-5人）
- 主唱和帮腔

## 练习建议

- 从简单动作开始，循序渐进
- 多观摩经典演出
- 掌握基本戏曲知识
- 培养音乐节奏感

表演皮影戏不仅需要技巧，更需要对传统文化的理解和热爱。''',
            'category': '表演技巧',
            'difficulty_level': 4,
            'order': 3,
            'estimated_duration': 60,
            'points_reward': 30
        }
    ]

    modules = []
    for module_data in modules_data:
        module = LearningModule(**module_data)
        db.session.add(module)
        modules.append(module)

    db.session.commit()
    print("✓ 学习模块创建完成")

    # 为第一个模块创建测验
    quiz = Quiz(
        title='皮影戏历史知识测验',
        title_en='Shadow Puppetry History Quiz',
        module_id=modules[0].id,
        passing_score=60,
        max_attempts=3
    )
    db.session.add(quiz)
    db.session.commit()

    # 添加测验问题
    questions_data = [
        {
            'quiz_id': quiz.id,
            'question_text': '皮影戏大约起源于哪个朝代？',
            'question_text_en': 'Which dynasty did shadow puppetry originate from?',
            'question_type': 'multiple_choice',
            'options': [
                {'id': 'a', 'text': '汉代'},
                {'id': 'b', 'text': '唐代'},
                {'id': 'c', 'text': '宋代'},
                {'id': 'd', 'text': '明代'}
            ],
            'options_en': [
                {'id': 'a', 'text': 'Han Dynasty'},
                {'id': 'b', 'text': 'Tang Dynasty'},
                {'id': 'c', 'text': 'Song Dynasty'},
                {'id': 'd', 'text': 'Ming Dynasty'}
            ],
            'correct_answer': 'a',
            'explanation': '皮影戏起源于汉代，距今已有两千多年的历史。',
            'order': 1,
            'points': 1
        },
        {
            'quiz_id': quiz.id,
            'question_text': '中国皮影戏在哪一年被列入联合国教科文组织非物质文化遗产名录？',
            'question_text_en': 'In which year was Chinese shadow puppetry listed as UNESCO Intangible Cultural Heritage?',
            'question_type': 'multiple_choice',
            'options': [
                {'id': 'a', 'text': '2008年'},
                {'id': 'b', 'text': '2009年'},
                {'id': 'c', 'text': '2010年'},
                {'id': 'd', 'text': '2011年'}
            ],
            'options_en': [
                {'id': 'a', 'text': '2008'},
                {'id': 'b', 'text': '2009'},
                {'id': 'c', 'text': '2010'},
                {'id': 'd', 'text': '2011'}
            ],
            'correct_answer': 'd',
            'explanation': '2011年，中国皮影戏被列入联合国教科文组织人类非物质文化遗产名录。',
            'order': 2,
            'points': 1
        },
        {
            'quiz_id': quiz.id,
            'question_text': '皮影戏的艺术特色包括哪些？（多选）',
            'question_text_en': 'What are the artistic characteristics of shadow puppetry? (Multiple choice)',
            'question_type': 'multiple_choice',
            'options': [
                {'id': 'a', 'text': '造型艺术'},
                {'id': 'b', 'text': '表演技巧'},
                {'id': 'c', 'text': '音乐伴奏'},
                {'id': 'd', 'text': '以上都是'}
            ],
            'options_en': [
                {'id': 'a', 'text': 'Modeling art'},
                {'id': 'b', 'text': 'Performance skills'},
                {'id': 'c', 'text': 'Musical accompaniment'},
                {'id': 'd', 'text': 'All of the above'}
            ],
            'correct_answer': 'd',
            'explanation': '皮影戏融合了造型艺术、表演技巧和音乐伴奏等多种艺术形式。',
            'order': 3,
            'points': 1
        }
    ]

    for question_data in questions_data:
        question = QuizQuestion(**question_data)
        db.session.add(question)

    db.session.commit()
    print("✓ 测验创建完成")

    print("✅ 数据库初始化完成！")
    print(f"  - 创建了 {User.query.count()} 个用户")
    print(f"  - 创建了 {Character.query.count()} 个角色")
    print(f"  - 创建了 {Story.query.count()} 个故事")
    print(f"  - 创建了 {LearningModule.query.count()} 个学习模块")
    print(f"  - 创建了 {Quiz.query.count()} 个测验")
