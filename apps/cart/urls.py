from django.conf.urls import url

from .views import CartAddView, CartInfoView

urlpatterns = [
    url(r'^add$', CartAddView.as_view(), name='add'),
    url(r'^$', CartInfoView.as_view(), name='show'),
]