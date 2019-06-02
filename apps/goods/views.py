from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.core.cache import cache
from django.core.paginator import Paginator
from django_redis import get_redis_connection

from .models import (GoodsType, GoodsSKU, IndexGoodsBanner,
                     IndexPromotionBanner, IndexTypeGoodsBanner)
from order.models import OrderGoods


# http://127.0.0.1:8000/index
class IndexView(View):

    def get(self, request):

        content = cache.get('index_page_data')
        if content is None:
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
        curt_count = 0
        if user.is_authenticated():

            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            curt_count = conn.hlen(cart_key)

        content.update(curt_count=curt_count)
        # 返回数据给模板

        return render(request, 'index.html', content)


# /goods/sku_id
class DetailView(View):

    def get(self, request, goods_id):

        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse('goods:index'))

        # 商品种类信息
        types = GoodsType.objects.all()

        # 商品的评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[0:2]

        # 获取购物车信息
        user = request.user
        curt_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            curt_count = conn.hlen(cart_key)

            # 用户浏览历史记录的添加
            conn = get_redis_connection('default')
            history_key = 'history_%d' % user.id
            conn.lrem(history_key, 0, goods_id)
            conn.lpush(history_key, goods_id)
            conn.ltrim(history_key, 0, 4)



        # 模板上下文
        content ={
            'sku': sku,
            'types': types,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'curt_count': curt_count,
        }

        return render(request, 'detail.html', content)


# /goods/种类id/页码?sort=排序方式
class ListView(View):

    def get(self, request, type_id, page):

        # 查询种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在
            return redirect(reverse('goods:index'))

        # 获取商品具体信息
        # 获取sort排序方式
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 获取商品分类信息
        types = GoodsType.objects.all()

        # 获取新品推荐信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[0:2]

        # 对数据进行分页
        paginator = Paginator(skus, 1)

        # 获取page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的page数据对象
        skus_page = paginator.page(page)

        # 获取购物车信息
        user = request.user
        curt_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            curt_count = conn.hlen(cart_key)

        content = {
            'type': type,
            'types': types,
            'new_skus': new_skus,
            'skus_page': skus_page,
            'curt_count': curt_count,
            'sort': sort
        }

        return render(request, 'list.html', content)
