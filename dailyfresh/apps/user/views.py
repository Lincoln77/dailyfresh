from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from user.models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from celery_tasks.tasks import send_register_active_email, generate_static_index_html
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
import re


def tests(request):
    """生成静态首页"""
    generate_static_index_html.delay()
    return HttpResponse('ok')

def register(request):
    """注册 user/register"""
    if request.method == 'GET':
        # 显示注册页面
        return render(request, 'register.html')
    else:
        # 1.接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2.进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 验证邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不合法'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已经存在
            return render(request, 'register.html', {'errmsg': '用户名已经存在'})
        # 3.进行业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 4.返回首页
        return redirect(reverse('goods:index'))


def register_handle(request):
    """进行注册处理"""
    # 1.接受数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 2.进行数据校验
    if not all([username, password, email]):
        # 数据不完整
        return render(request, 'register.html', {'errmsg': '数据不完整'})

    # 验证邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不合法'})

    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请同意协议'})
    # 校验用户名是否重复
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # 用户名不存在
        user = None

    if user:
        # 用户名已经存在
        return render(request, 'register.html', {'errmsg': '用户名已经存在'})
    # 3.进行业务处理：进行用户注册
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()

    # 4.返回首页
    return redirect(reverse('goods:index'))


class RegisterView(View):
    """注册"""
    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """进行注册处理"""
        # 1.接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2.进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 验证邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不合法'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已经存在
            return render(request, 'register.html', {'errmsg': '用户名已经存在'})
        # 3.进行业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 4.发送激活邮件，包含激活连接：http://127.0.0.1:8000/user/active/3
        # 激活连接中需要包含用户的身份信息，并且要把身份信息进行加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)  # bytes
        token = token.decode()

        # 发邮件
        # TODO :send_register_active_email.delay(email, username, token)
        send_register_active_email.delay(email, username, token)
        # 组织邮件信息
        # subject = '天天生鲜欢迎信息'
        # message = ''
        # html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面的链接激活您的账户:<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
        # username, token, token)
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # send_mail(subject, message, sender, receiver, html_message=html_message)
        # 5.返回首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    """用户激活"""
    def get(self, request, token):
        """进行用户激活"""
        # 进行解密， 获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 1.获取待激活的用户id
            user_id = info['confirm']

            # 2.根据用户id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 3.跳转到登录界面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活连接以过期
            return HttpResponse('激活链接已经过期')


# user/logout
class LogoutView(View):
    """退出登录"""
    def get(self, request):
        """退出登录"""
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user/login
class LoginView(View):
    """登录视图类"""
    def get(self, request):
        """显示登录界面"""
        # 1.判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        # 2.使用模板返回页面
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录校验"""
        # 1.接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 2.校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 3.校验用户名和密码
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已经激活
                # 1）记录用户的登录状态
                login(request, user)
                # 获取用户登录后要跳转的地址
                # 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))

                # 拿到要跳转 的对象
                response = redirect(next_url)  # HttpResponseRedirect

                # 2）判断是否需要记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 3)返回response
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# /user
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""
    def get(self, request):
        """显示"""
        # page='user'
        # request.user：
        # 如果用户未登录->AnonymousUser类的一个实例
        # 如果用户登录->User类的一个实例
        # request.user.is_authenticated()
        # 1.获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 2.获取用户的历史浏览器记录
        con = get_redis_connection('default')

        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的五个商品id
        sku_ids = con.lrange(history_key, 0, 4)
        # 遍历获取用户浏览器的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}
        # 3.除了给模板文件传递的模板变量外，django框架会把request.user也传给模板文件
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-信息页"""
    def get(self, request, page):
        """显示"""
        # page='order'
        # 1.获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 2.遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品的信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count*order_sku.price
                # 动态给order_sku增加属性amount，保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态名称
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 3.分页
        paginator = Paginator(orders, 1)

        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo:进行页码控制，页面上最多显示5个页码
        # 1）总页数小于五页，页面上显示所有的页码
        # 2）如果当前页是前三页，显示1-5页
        # 3）如果当前页是后三页，显示后五页
        # 4）其他情况，显示当前页的前两页，当前页，当前页的后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 4.组织上下文
        context = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order'
        }

        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request, 'user_center_order.html', context)


# /user/address
class AddressView(LoginRequiredMixin, View):
    """用户中心-信息页"""
    def get(self, request):
        """显示"""
        # page='address'
        # 获取用户默认收货地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)

        # 使用模板
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        """地址的添加"""
        # 1.接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 2.校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不合法'})

        # 3.业务处理：地址添加
        # 如果用户已经存在默认收货地址，添加的地址不作为默认地址
        # 获取登录用户对应的User对象
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收获地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答，刷新地址页面
        return redirect(reverse('user:address'))  # get请求
