from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def login_required(view_func):
    """登录判断装饰器"""
    def wrapper(request, *args, **kwargs):
        if request.session.has_key('islogin'):
            # 用户已登录
            return view_func(request, *args, **kwargs)
        else:
            # 跳转到登录界面
            return redirect(reverse('user:login'))
    return wrapper
