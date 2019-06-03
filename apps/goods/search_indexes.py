# 定义索引类
from haystack import indexes
from .models import GoodsSKU


class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):

    # 索引字段
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):

        return GoodsSKU

    def index_queryset(self, using=None):

        return self.get_model().objects.all()