from django.conf.urls import url

from .views import (
    RegisterView, ActiveView, LoginView,
    UserInfoView, UserOrderView, UserAddressView,
    LogoutView
)

app_name = '[user]'
urlpatterns = [
    # url(r'^register$', views.register, name='register'),
    # url(r'^register_handle$', views.register_handle, name='register_handle'), # 注册处理
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    url(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心信息页
    url(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),
    url(r'^address$', UserAddressView.as_view(), name='address'),

]
