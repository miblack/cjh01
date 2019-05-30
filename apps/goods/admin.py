from django.contrib import admin

from .models import GoodsType, IndexPromotionBanner,GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, GoodsSKU, Goods
# Register your models here.


class BaseAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        from celery_tasks.tasks import save_static_html
        save_static_html.delay()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        from celery_tasks.tasks import save_static_html
        save_static_html.delay()


admin.site.register(GoodsType)
admin.site.register(IndexPromotionBanner, BaseAdmin)
admin.site.register(GoodsImage, BaseAdmin)
admin.site.register(IndexGoodsBanner, BaseAdmin)
admin.site.register(IndexTypeGoodsBanner, BaseAdmin)
admin.site.register(GoodsSKU, BaseAdmin)
admin.site.register(Goods, BaseAdmin)

