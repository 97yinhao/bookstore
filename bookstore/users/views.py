from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import reverse

from order.models import OrderInfo, OrderBooks
from users.models import Passport, Address
import re


# Create your views here.
from utils.decorators import login_required


def register(request):
    """显示用户注册界面"""
    return render(request, 'users/register.html')


def register_handle(request):
    """进行用户注册处理"""
    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    password2 = request.POST.get('cpwd')
    email = request.POST.get('email')

    # 进行数据校验
    if not all([username, password, email]):
        # 有数据为空
        return render(request, 'users/register.html', {'errmsg': '参数不能为空!'})
    # 判断邮箱是否合法
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        # 邮箱不合法
        return render(request, 'users/register.html', {'errmsg': '邮箱不合法!'})
    if password != password2:
        # 两次密码不一致
        return render(request, 'users/register.html', {'errmsg': '两次密码不一致!'})
    if not 7 < len(password) < 21:
        return render(request, 'users/register.html', {'errmsg': '密码最少8位,最长20位!'})
    if not 4 < len(username) < 21:
        return render(request, 'users/register.html', {'errmsg': '请输入5-20个字符的用户名!'})
    if not re.match(r'\w', username):
        return render(request, 'users/register.html', {'errmsg': '用户名只能包含数字、字母、下划线!'})

    # 向用户系统中添加用户
    try:
        Passport.object.add_one_passport(username=username, password=password, email=email)
    except Exception as e:
        print('Error:', e)
        return render(request, 'users/register.html', {'errmsg': '用户已存在!'})

    return redirect(reverse('books:index'))


def login(request):
    """显示登录界面"""
    if request.COOKIES.get("username"):
        username = request.COOKIES.get("username")
        checked = 'checked'
    else:
        username = ''
        checked = ''

    context = {
        'username': username,
        'checked': checked,
    }
    return render(request, 'users/login.html', context)


def login_check(request):
    """进行用户登录校验"""
    # 获取数据
    username = request.POST.get('username')
    password = request.POST.get('password')
    remember = request.POST.get('remember')

    # 数据校验
    if not all([username, password, remember]):
        # 有数据为空
        return JsonResponse({'res': 2})

    # 根据用户名和密码查找账户信息
    passport = Passport.object.get_one_passport(username=username, password=password)
    if passport:
        next_url = reverse('books:index')
        jres = JsonResponse({'res': 1, 'next_url': next_url})

        # 判断是否需要记住用户名
        if remember == 'true':
            jres.set_cookie('username', username, max_age=7*24*3600)
        else:
            jres.delete_cookie('username')

        # 记住用户登录状态
        request.session['islogin'] = True
        request.session['username'] = username
        request.session['passport_id'] = passport.id
        return jres
    else:
        # 用户名密码错误
        return JsonResponse({'res': 0})


def logout(request):
    """用户退出登录"""
    # 清空用户的session信息
    request.session.flush()
    # 跳转到首页
    return redirect(reverse('books:index'))


@login_required
def user(request):
    """用户中心-信息页"""
    passport_id = request.session.get('passport_id')
    # 获取用户的基本信息
    addr = Address.objects.get_default_address(passport_id=passport_id)

    books_li = []

    context = {
        'addr': addr,
        'page': 'user',
        'books_li': books_li
    }

    return render(request, 'users/user_center_info.html', context)


@login_required
def address(request):
    """用户中心-地址页"""
    # 获取登录用户的id
    passport_id = request.session.get('passport_id')

    if request.method == 'GET':
        # 显示地址页面
        # 查询用户默认地址
        addr = Address.objects.get_default_address(passport_id=passport_id)
        return render(request, 'users/user_center_site.html', {'addr': addr, 'page': 'address'})
    else:
        # 添加收货地址
        # 接收数据
        recipient_name = request.POST.get('username')
        recipient_addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recipient_phone = request.POST.get('phone')

        # 进行校验
        if not all([recipient_name, recipient_addr, zip_code, recipient_phone]):
            return render(request, 'users/user_center_site.html', {'errmsg': '参数不能为空'})

        # 添加收货地址
        Address.objects.add_one_address(
            passport_id=passport_id,
            recipient_name=recipient_name,
            recipient_addr=recipient_addr,
            zip_code=zip_code,
            recipient_phone=recipient_phone
        )

        return redirect(reverse('user:address'))


@login_required
def order(request, page):
    """用户中心-订单页"""
    # 查询用户的订单信息
    passport_id = request.session.get('passport_id')

    # 获取订单信息
    order_li = OrderInfo.objects.filter(passport_id=passport_id)

    # 遍历获取订单的商品信息
    # order -> OrderInfo实例对象
    for order in order_li:
        # 根据订单id查询订单商品信息
        order_id = order.order_id
        order_books_li = OrderBooks.objects.filter(order_id=order_id)

        # 计算商品的小计
        # order_books -> OrderBooks实例对象
        for order_books in order_books_li:
            count = order_books.count
            price = order_books.price
            amount = count * price
            # 保存订单中每一个商品的小计
            order_books.amount = amount
        # 给order对象动态增加一个属性order_books_li,保存订单中商品的信息
        order.order_books_li = order_books_li

    paginator = Paginator(order_li, 3)
    num_pages = paginator.num_pages

    if not page:
        page = 1
    if page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)

    order_li = paginator.page(page)
    if num_pages < 5:
        pages = range(1, num_pages + 1)
    elif page <= 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages - 4, num_pages + 1)
    else:
        pages = range(page - 2, page + 3)

    context = {
        'order_li': order_li,
        'pages': pages
    }

    return render(request, 'users/user_center_order.html', context)
