from django.conf.urls import url

from .views import IndexView
from . import views

app_name = '[goods]'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

]
