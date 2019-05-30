from django.shortcuts import render
from django.views.generic import View
from django.core.cache import cache
from django_redis import get_redis_connection

from .models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


# http://127.0.0.1:8000
class IndexView(View):

    def get(self, request):

        content = cache.get('index_page_data')
        if content is None:
            print('设置缓存')
            # 商品种类信息
            types = GoodsType.objects.all()

            # 首页轮播信息
            goods_banners = IndexGoodsBanner.objects.all()

            # 商品促销信息
            goods_promotions = IndexPromotionBanner.objects.all()

            # 首页分类商品展示
            for type in types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
                type.image_banners = image_banners
                type.title_banners = title_banners

            content = {
                'types': types,
                'goods_banners': goods_banners,
                'goods_promotions': goods_promotions,
                # 'curt_count': counter,

            }
            cache.set('index_page_data', content, 3600)

        user = request.user
        counter = 0
        if user.is_authenticated():

            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            counter = conn.hlen(cart_key)

        content.update(curt_count=counter)
        # 返回数据给模板

        return render(request, 'index.html', content)
