# 中国皮影戏 · 月夜龙影

一个使用 Python 和 HTML/CSS/JavaScript 创作的迷你皮影戏体验。项目基于 Flask，运行后可在浏览器中通过点击切换四幕故事，欣赏月夜下的龙影传说。

## 本地运行

1. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

2. 启动应用

   ```bash
   python app.py
   ```

3. 在浏览器访问 <http://127.0.0.1:5000/> 体验皮影戏。

## 项目结构

- `app.py`：Flask 应用入口，提供场景数据并渲染模板。
- `templates/index.html`：皮影戏舞台页面，包含视觉风格、动画与交互逻辑。
- `requirements.txt`：项目依赖列表。

## 灵感

皮影戏是中国非物质文化遗产，本项目希望通过现代网页技术向这一传统艺术致敬。
