from django.conf.urls import url

from .views import IndexView, DetailView, ListView

app_name = '[goods]'
urlpatterns = [
    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)', ListView.as_view(), name='list'),
]
