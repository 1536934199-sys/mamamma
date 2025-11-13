/**
 * 主JavaScript文件 - 通用功能
 */

// API基础URL
const API_BASE_URL = '/api';

// 工具函数
const utils = {
    // 格式化时间
    formatTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 30) {
            return date.toLocaleDateString('zh-CN');
        } else if (days > 0) {
            return `${days}天前`;
        } else if (hours > 0) {
            return `${hours}小时前`;
        } else if (minutes > 0) {
            return `${minutes}分钟前`;
        } else {
            return '刚刚';
        }
    },

    // 格式化数字
    formatNumber(num) {
        if (num < 1000) return num.toString();
        if (num < 10000) return (num / 1000).toFixed(1) + 'K';
        if (num < 1000000) return (num / 10000).toFixed(1) + '万';
        return (num / 1000000).toFixed(1) + 'M';
    },

    // 显示Toast消息
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // 发送API请求
    async apiRequest(url, options = {}) {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(API_BASE_URL + url, {
                ...options,
                headers
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '请求失败');
            }

            return await response.json();
        } catch (error) {
            utils.showToast(error.message, 'error');
            throw error;
        }
    }
};

// 评论功能
class CommentManager {
    constructor(contentType, contentId) {
        this.contentType = contentType; // 'story' or 'module'
        this.contentId = contentId;
        this.init();
    }

    init() {
        const form = document.getElementById('comment-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // 回复按钮
        document.querySelectorAll('.reply-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleReply(e));
        });

        // 点赞按钮
        document.querySelectorAll('.like-comment-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleLike(e));
        });
    }

    async handleSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const content = form.querySelector('textarea[name="content"]').value.trim();
        const parentId = form.querySelector('input[name="parent_id"]')?.value;

        if (!content) {
            utils.showToast('评论内容不能为空', 'warning');
            return;
        }

        try {
            const url = this.contentType === 'story'
                ? `/stories/${this.contentId}/comment`
                : `/learning/${this.contentId}/comment`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content, parent_id: parentId })
            });

            if (response.ok) {
                const data = await response.json();
                utils.showToast('评论成功', 'success');
                form.reset();
                location.reload(); // 简单实现，重新加载页面
            } else {
                const error = await response.json();
                utils.showToast(error.error || '评论失败', 'error');
            }
        } catch (error) {
            utils.showToast('评论失败，请稍后重试', 'error');
        }
    }

    handleReply(e) {
        const commentId = e.target.dataset.commentId;
        const form = document.getElementById('comment-form');
        const parentIdInput = form.querySelector('input[name="parent_id"]');

        if (parentIdInput) {
            parentIdInput.value = commentId;
        } else {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'parent_id';
            input.value = commentId;
            form.appendChild(input);
        }

        form.querySelector('textarea').focus();
        utils.showToast('回复评论...', 'info');
    }

    async handleLike(e) {
        const commentId = e.target.dataset.commentId;
        // 实现点赞逻辑
        utils.showToast('点赞功能开发中', 'info');
    }
}

// 评分功能
class RatingManager {
    constructor(contentType, contentId) {
        this.contentType = contentType;
        this.contentId = contentId;
        this.currentRating = 0;
        this.init();
    }

    init() {
        const stars = document.querySelectorAll('.rating-star');
        stars.forEach((star, index) => {
            star.addEventListener('click', () => this.setRating(index + 1));
            star.addEventListener('mouseenter', () => this.highlightStars(index + 1));
        });

        const container = document.querySelector('.rating-stars');
        if (container) {
            container.addEventListener('mouseleave', () => this.highlightStars(this.currentRating));
        }
    }

    highlightStars(rating) {
        const stars = document.querySelectorAll('.rating-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }

    async setRating(rating) {
        this.currentRating = rating;
        this.highlightStars(rating);

        try {
            const url = this.contentType === 'story'
                ? `/stories/${this.contentId}/rate`
                : `/learning/${this.contentId}/rate`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ score: rating })
            });

            if (response.ok) {
                utils.showToast('评分成功', 'success');
            } else {
                utils.showToast('评分失败', 'error');
            }
        } catch (error) {
            utils.showToast('评分失败，请稍后重试', 'error');
        }
    }
}

// 学习进度跟踪
class ProgressTracker {
    constructor(moduleId) {
        this.moduleId = moduleId;
        this.progress = 0;
        this.startTime = Date.now();
        this.init();
    }

    init() {
        // 定期更新学习时长
        setInterval(() => this.updateTimeSpent(), 60000); // 每分钟更新

        // 页面滚动跟踪进度
        window.addEventListener('scroll', () => this.trackScrollProgress());

        // 页面离开时保存进度
        window.addEventListener('beforeunload', () => this.saveProgress());
    }

    trackScrollProgress() {
        const content = document.querySelector('.module-content');
        if (!content) return;

        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;

        const scrollPercentage = (scrollTop / (documentHeight - windowHeight)) * 100;
        this.progress = Math.min(100, scrollPercentage);

        // 更新进度条
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${this.progress}%`;
        }
    }

    async updateTimeSpent() {
        const timeSpent = Math.floor((Date.now() - this.startTime) / 60000); // 分钟
        await this.saveProgress(timeSpent);
    }

    async saveProgress(timeSpent = 0) {
        try {
            await utils.apiRequest(`/modules/${this.moduleId}/update-progress`, {
                method: 'POST',
                body: JSON.stringify({
                    progress: this.progress,
                    time_spent: timeSpent
                })
            });
        } catch (error) {
            console.error('保存进度失败:', error);
        }
    }

    async completeModule() {
        try {
            const response = await utils.apiRequest(`/modules/${this.moduleId}/complete`, {
                method: 'POST'
            });
            utils.showToast(response.message, 'success');
            // 可以显示庆祝动画
        } catch (error) {
            console.error('完成模块失败:', error);
        }
    }
}

// 测验管理
class QuizManager {
    constructor(quizId) {
        this.quizId = quizId;
        this.answers = {};
        this.startTime = Date.now();
        this.init();
    }

    init() {
        const form = document.getElementById('quiz-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // 监听答案选择
        document.querySelectorAll('.quiz-option').forEach(option => {
            option.addEventListener('change', (e) => this.recordAnswer(e));
        });
    }

    recordAnswer(e) {
        const questionId = e.target.name.replace('question_', '');
        const value = e.target.value;

        if (e.target.type === 'checkbox') {
            if (!this.answers[questionId]) {
                this.answers[questionId] = [];
            }
            if (e.target.checked) {
                this.answers[questionId].push(value);
            } else {
                this.answers[questionId] = this.answers[questionId].filter(v => v !== value);
            }
        } else {
            this.answers[questionId] = value;
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        // 检查是否所有问题都已回答
        const questions = document.querySelectorAll('.quiz-question');
        if (Object.keys(this.answers).length < questions.length) {
            utils.showToast('请回答所有问题', 'warning');
            return;
        }

        try {
            const response = await utils.apiRequest(`/quiz/${this.quizId}/submit`, {
                method: 'POST',
                body: JSON.stringify({ answers: this.answers })
            });

            this.showResults(response);
        } catch (error) {
            utils.showToast('提交失败，请稍后重试', 'error');
        }
    }

    showResults(data) {
        const resultsHTML = `
            <div class="quiz-results">
                <h2>测验结果</h2>
                <div class="score ${data.passed ? 'passed' : 'failed'}">
                    得分: ${data.score}分
                </div>
                <p>${data.passed ? '恭喜通过！' : '继续努力！'}</p>
                <div class="results-details">
                    ${data.results.map((r, i) => `
                        <div class="question-result ${r.is_correct ? 'correct' : 'incorrect'}">
                            <strong>问题 ${i + 1}: ${r.is_correct ? '✓ 正确' : '✗ 错误'}</strong>
                            ${r.explanation ? `<p>${r.explanation}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
                ${data.attempts_left > 0 ? `<p>剩余尝试次数: ${data.attempts_left}</p>` : ''}
            </div>
        `;

        document.getElementById('quiz-container').innerHTML = resultsHTML;
    }
}

// 社交分享
function shareContent(platform, title, url) {
    const shareUrls = {
        wechat: `weixin://`,
        weibo: `https://service.weibo.com/share/share.php?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`,
        twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`,
        facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`
    };

    if (shareUrls[platform]) {
        if (platform === 'wechat') {
            utils.showToast('请使用微信扫码分享', 'info');
            // 这里可以显示二维码
        } else {
            window.open(shareUrls[platform], '_blank');
        }
    }
}

// 懒加载图片
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化懒加载
    lazyLoadImages();

    // 添加加载动画
    document.body.classList.add('loaded');

    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

// 导出全局对象
window.shadowPuppet = {
    utils,
    CommentManager,
    RatingManager,
    ProgressTracker,
    QuizManager,
    shareContent
};
