import re

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings

from .models import User
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


# /user
class UserInfoView(LoginRequiredMixin, View):

    def get(self, request):
        # page='user'
        return render(request, 'user_center_info.html', {'page': 'user'})


# /user/order
class UserOrderView(LoginRequiredMixin, View):

    def get(self, request):
        # page=order
        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class UserAddressView(LoginRequiredMixin, View):

    def get(self, reuqest):
        # page=address
        return render(reuqest, 'user_center_site.html', {'page': 'address'})
