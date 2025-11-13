"""
辅助函数 - 通用工具函数
"""
import os
import re
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def generate_slug(title):
    """从标题生成URL友好的slug"""
    # 移除特殊字符，保留字母、数字、空格和中文
    slug = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title.lower())
    # 将空格替换为连字符
    slug = re.sub(r'[\s_]+', '-', slug)
    # 移除首尾的连字符
    slug = slug.strip('-')
    return slug


def format_duration(seconds):
    """格式化时长"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}小时{minutes}分钟"
        return f"{hours}小时"


def format_number(num):
    """格式化数字显示"""
    if num < 1000:
        return str(num)
    elif num < 10000:
        return f"{num/1000:.1f}K"
    elif num < 1000000:
        return f"{num/10000:.1f}万"
    else:
        return f"{num/1000000:.1f}M"


def time_ago(dt):
    """返回相对时间"""
    if not dt:
        return ""

    now = datetime.utcnow()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "刚刚"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}分钟前"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}小时前"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days}天前"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months}个月前"
    else:
        years = diff.days // 365
        return f"{years}年前"


def paginate(query, page, per_page):
    """分页辅助函数"""
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }


def save_uploaded_file(file, folder='uploads'):
    """保存上传的文件"""
    if not file or not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    # 添加时间戳避免文件名冲突
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"

    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    file_path = os.path.join(upload_path, filename)
    file.save(file_path)

    # 返回相对路径
    return os.path.join(folder, filename)


def get_client_ip(request):
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr


def truncate_text(text, length=100, suffix='...'):
    """截断文本"""
    if not text or len(text) <= length:
        return text
    return text[:length].rstrip() + suffix


def calculate_reading_time(content):
    """计算阅读时间（分钟）"""
    # 中文按500字/分钟，英文按200词/分钟
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_words = len(re.findall(r'[a-zA-Z]+', content))

    chinese_time = chinese_chars / 500
    english_time = english_words / 200

    total_minutes = chinese_time + english_time
    return max(1, int(total_minutes))


def sanitize_html(html_content):
    """清理HTML内容，防止XSS攻击"""
    # 简单实现，生产环境应使用bleach等库
    import html
    return html.escape(html_content)


def generate_share_text(title, description, url):
    """生成分享文本"""
    return {
        'title': title,
        'description': truncate_text(description, 200),
        'url': url,
        'hashtags': ['皮影戏', 'ShadowPuppetry', '中国文化']
    }
