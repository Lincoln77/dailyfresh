# 使用celery
from celery import Celery
from django.conf import settings
from django.template import loader, RequestContext
from django.core.mail import send_mail

# 在任务处理者一端加这几句
import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()

from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

# 创建一个Celery类的实例对象
app = Celery(
    'celery_tasks.tasks',
    broker='redis://192.168.190.130:6379/8'
)


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面的链接激活您的账户:<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
    sender = settings.EMAIL_FROM
    receiver = [to_email]

    send_mail(subject, message, sender, receiver, html_message=html_message)

@app.task
def generate_static_index_html():
    """产生首页静态页面"""
    # 1.获取商品的种类信息
    types = GoodsType.objects.all()

    # 2.获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 3.获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 4.获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

        # 动态的给type增加属性，分别保存首页分类商品的图片信息与文字信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 组织上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners
    }
    # 使用模板
    # 1.加载模板文件，返回模板对象
    temp = loader.get_template('static_index.html')
    # 2.模板上下文渲染
    static_index_html = temp.render(context)

    # 生成首页对应的静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
