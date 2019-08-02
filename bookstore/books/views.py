from django.shortcuts import render, redirect
from books.models import Books
from books.enums import *
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator


# Create your views here.
def index(request):
    """显示首页"""
    python_new = Books.objects.get_books_by_type(PYTHON, limit=3, sort='new')
    python_hot = Books.objects.get_books_by_type(PYTHON, limit=4, sort='hot')
    javascript_new = Books.objects.get_books_by_type(JAVASCRIPT, limit=3, sort='new')
    javascript_hot = Books.objects.get_books_by_type(JAVASCRIPT, limit=4, sort='hot')
    algorithms_new = Books.objects.get_books_by_type(ALGORITHMS, 3, sort='new')
    algorithms_hot = Books.objects.get_books_by_type(ALGORITHMS, 4, sort='hot')
    machinelearning_new = Books.objects.get_books_by_type(MACHINELEARNING, 3, sort='new')
    machinelearning_hot = Books.objects.get_books_by_type(MACHINELEARNING, 4, sort='hot')
    operatingsystem_new = Books.objects.get_books_by_type(OPERATINGSYSTEM, 3, sort='new')
    operatingsystem_hot = Books.objects.get_books_by_type(OPERATINGSYSTEM, 4, sort='hot')
    database_new = Books.objects.get_books_by_type(DATABASE, 3, sort='new')
    database_hot = Books.objects.get_books_by_type(DATABASE, 4, sort='hot')

    # 定义模板上下文
    context = {
        'python_new': python_new,
        'python_hot': python_hot,
        'javascript_new': javascript_new,
        'javascript_hot': javascript_hot,
        'algorithms_new': algorithms_new,
        'algorithms_hot': algorithms_hot,
        'machinelearning_new': machinelearning_new,
        'machinelearning_hot': machinelearning_hot,
        'operatingsystem_new': operatingsystem_new,
        'operatingsystem_hot': operatingsystem_hot,
        'database_new': database_new,
        'database_hot': database_hot,
    }
    # 使用模板
    return render(request, 'books/index.html', context)


def detail(request, books_id):
    """显示商品的详情页面"""
    # 获取商品的详情信息
    books = Books.objects.get_books_by_id(books_id=books_id)
    if not books:
        # 商品不存在,跳转首页
        return redirect(reverse('books:index'))

    # 新品推荐
    books_li = Books.objects.get_books_by_type(type_id=books.type_id, limit=2, sort='new')

    # 当前商品类型
    type_title = BOOKS_TYPE[books.type_id]

    # 定义上下文
    context = {'books': books, 'books_li': books_li, 'type_title': type_title}

    # 使用模板
    return render(request, 'books/detail.html', context)


def list(request, type_id, page):
    """商品列表页面"""
    # 获取排序方式
    sort = request.GET.get('sort', 'default')

    # 判断type_id是否合法
    if int(type_id) not in BOOKS_TYPE.keys():
        return redirect(reverse('books:index'))

    # 根据商品种类id和排序方式查询数据
    books_li = Books.objects.get_books_by_type(type_id=type_id, sort=sort)

    # 分页
    paginator = Paginator(books_li, 1)

    # 获取分页之后的总页数
    num_pages = paginator.num_pages

    # 取第page页数据
    if page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)

    # 返回值是一个Page类的实例对象
    books_li = paginator.page(page)

    # 进行页码控制
    # 1.总页数<5, 显示所有页码
    # 2.当前页是前3页，显示1-5页
    # 3.当前页是后3页，显示后5页 10 9 8 7
    # 4.其他情况，显示当前页前2页，后2页，当前页
    if num_pages < 5:
        pages = range(1, num_pages + 1)
    elif page < 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages - 4, num_pages + 1)
    else:
        pages = range(page - 2, page + 3)

    # 新品推荐
    books_new = Books.objects.get_books_by_type(type_id=type_id, limit=2, sort='new')

    # 定义上下文
    type_title = BOOKS_TYPE[int(type_id)]
    context = {
        'books_li': books_li,
        'books_new': books_new,
        'type_id': type_id,
        'sort': sort,
        'type_title': type_title,
        'pages': pages
    }

    return render(request, 'books/list.html', context)
