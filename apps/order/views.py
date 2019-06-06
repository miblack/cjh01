from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.db import transaction
from django_redis import get_redis_connection

from goods.models import GoodsSKU
from user.models import Address
from .models import OrderInfo, OrderGoods
from utils.mixin import LoginRequiredMixin

from datetime import datetime


# /order/place
class OrderPlaceView(LoginRequiredMixin, View):

    def post(self, request):
        # 提交订单页面显示

        user = request.user
        # 获取参数sku_ids
        sku_ids = request.POST.getlist('sku_ids')

        # 校验参数
        if not sku_ids:
            return redirect(reverse('cart:show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = []
        total_price = 0
        total_count = 0
        # 便利sku_ids
        for sku_id in sku_ids:
            # 根据id获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            count = conn.hget(cart_key, sku_id)

            if count is None:
                count = 0

            # 商品小计
            amount = sku.price * int(count)
            # 保存商品的数量,小计
            sku.count = count
            sku.amount = amount

            skus.append(sku)

            # 累计商品数量和总金额
            total_price += amount
            total_count += int(count)

        # 运费
        transit_price = 10
        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收货地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文
        sku_ids = ','.join(sku_ids)  # [1,23] --> 1,23
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'total_pay': total_pay,
            'transit_price': transit_price,
            'addrs': addrs,
            'sku_ids': sku_ids
        }

        return render(request, 'place_order.html', context)


# /order/commit
class OrderCommitView(View):

    @transaction.atomic
    def post(self, request):
        # 创建订单

        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 判断数据是否完整
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Exception as e:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址不存在'})



        # 创建订单核心
        # 组织参数
        # 订单id：20190605231212+用户id

        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 设置事物保存点
        save_id = transaction.savepoint()

        try:

            # 向df_order_info插入一条数据
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_price=total_price,
                                             total_count=total_count,
                                             transit_price=transit_price)

            # 向df_order_goods表中插入几条数据
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品的信息
                for i in range(3):
                    try:
                        # sku = GoodsSKU.objects.select_for_update().get(id=sku_id)  解决并发冲突 --> 悲观锁
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except Exception as e:
                        # 商品不存在
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    # 从redis中获取用户所要购买的商品的数量
                    count = conn.hget(cart_key, sku_id)

                    # 判断商品的库存
                    if int(count) > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # 更新商品的库存和销量
                    orgin_stock = sku.stock
                    new__stock = orgin_stock - int(count)
                    new_sales = sku.sales + int(count)

                    # 返回受影响的行
                    res = GoodsSKU.objects.filter(id=sku_id, stock=orgin_stock).update(stock=new__stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            # 尝试第三次
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败'})
                        continue

                    # 向df_order_goods表中插入1条数据
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)

                    # 累加订单商品的总数量和总金额
                    amount = sku.price * int(count)
                    total_count += int(count)
                    total_price += amount

                    # 跳出循环
                    break

            # 更新订单信息表中的商品总数量和总金额
            order.total_price = total_price
            order.total_count = total_count
            order.save()

        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # 提交事物
        transaction.savepoint_commit(save_id)

        # 清楚用户购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})






