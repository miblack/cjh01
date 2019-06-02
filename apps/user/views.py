import re

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings
from django_redis import get_redis_connection

from .models import User, Address
from goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired


# Create your views here.
# /user/register
class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 1.接收注册相关数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2.判断数据是否合法,数据检验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 检验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 检验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            # 用户名存在
            return render(request, 'register.html', {'errmsg': '用户名已经存在'})

        # 3.进行业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0  # 默认为不激活状态
        user.save()

        # 发送激活邮件，包含激活链接:http://127.0.0.1:8000/user/active/3
        # 激活链接中包含用户的身份信息,加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()

        # 发邮件
        subject = '天天生鲜欢迎信息'
        message = ''
        sender = settings.EMAIL_HOST_USER
        receiver = [email]
        html_message = '<h1>{} ,欢迎你成为天天生鲜会员,请点击下方链接激活账号</h1></br><a href="http://127.0.0.1:8000/user/active/{}">http://127.0.0.1:8000/user/active/{}</a>'.format(username, token, token)
        send_mail(subject, message, sender, recipient_list=receiver, html_message=html_message)

        # 返回应答,跳转到首页
        return redirect(reverse('goods:index'))


# /user/active
class ActiveView(View):
    '''用户激活'''

    def get(self, request, token):
        '''进行用户激活'''
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取激活用户的信息
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')


# /user/login
class LoginView(View):
    '''登录类视图'''

    def get(self, request):

        if 'username' in request.COOKIES:
            username = request.POST.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登录校验'''

        # 1. 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整'})

        # 业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user) # 记录用户登录状态
                next_url = request.GET.get('next', reverse('goods:index'))
                # 默认到首页
                response = redirect(next_url)

                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                return response

            else:
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码不正确'})


# /user/logout
class LogoutView(View):
    # 退出登录
    def get(self, request):
        # 清除session信息
        logout(request)
        # 跳转
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):

    def get(self, request):
        # page='user'

        # 用户信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 用户的最近浏览
        conn = get_redis_connection('default')

        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = conn.lrange(history_key, 0, 4)

        # 从数据库中查询用户的浏览商品的具体信息
        goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        goods_res = []
        for a_id in sku_ids:
            for goods in goods_li:
                if a_id == goods.id:
                    goods_res.append(goods)

        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li,
        }

        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):

    def get(self, request):
        # page=order

        # 用户的订单信息

        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class UserAddressView(LoginRequiredMixin, View):

    def get(self, reuqest):
        # page=address

        # 获取用户默认收货地址
        user = reuqest.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(reuqest, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 获取地址信息
        receiver = request.POST.get('receiver')
        addr = request.POST.get('address')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 校验信息
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

        # 业务处理和数据存储
        # 获取登录用户的user对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)  # models.Manager
        # except Address.DoesNotExist:
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
        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))  # get请求方式

