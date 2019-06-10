from django.conf.urls import url

from .views import OrderPlaceView, OrderCommitView, OrderPayView, OrderCheckView


urlpatterns = [

    url(r'^place$', OrderPlaceView.as_view(), name='place'),    # 提交订单
    url(r'^commit$', OrderCommitView.as_view(), name='commit'),  # 创建订单
    url(r'^pay$', OrderPayView.as_view(), name='pay'),  # 支付
    url(r'^check$', OrderCheckView.as_view(), name='check'),  # 查询支付结果
]
