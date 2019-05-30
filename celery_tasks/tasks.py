from django.shortcuts import render
from django.template import loader
from django.conf import settings

from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
# 使用celery
from celery import Celery

import os

# 创建一个Celery 实例

app = Celery('celery_tasks.tasks', broker='redis://localhost:6379/3')


@app.task
def save_static_html():
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

    # 返回数据给模板
    content = {
        'types': types,
        'goods_banners': goods_banners,
        'goods_promotions': goods_promotions,

    }

    tem = loader.get_template('static_index.html')
    static_index_html = tem.render(content)
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)

