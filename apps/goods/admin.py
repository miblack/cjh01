from django.contrib import admin
from django.core.cache import cache

from .models import GoodsType, IndexPromotionBanner,GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, GoodsSKU, Goods
# Register your models here.


class BaseAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        from celery_tasks.tasks import save_static_html
        save_static_html.delay()

        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        from celery_tasks.tasks import save_static_html
        save_static_html.delay()

        cache.delete('index_page_data')


admin.site.register(Goods, BaseAdmin)
admin.site.register(GoodsType, BaseAdmin)
admin.site.register(IndexPromotionBanner, BaseAdmin)
admin.site.register(GoodsImage, BaseAdmin)
admin.site.register(IndexGoodsBanner, BaseAdmin)
admin.site.register(IndexTypeGoodsBanner, BaseAdmin)
admin.site.register(GoodsSKU, BaseAdmin)


