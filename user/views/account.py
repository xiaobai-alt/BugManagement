import datetime
import uuid

from django.shortcuts import render, HttpResponse, redirect
from user.forms.account import RegisterModelForm, SendSMS, LoginModelForm, LoginPModelForm
from django.http import JsonResponse
from django.db.models import Q
from user import models


# 写一个判断函数，判断request是否存在ajax请求，用来区分登录功能的两种不同登录方式
# def is_ajax(self):
#     return self.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


# Create your views here.

def send_sms(request):
    form = SendSMS(request, data=request.GET)  # 通过重写函数的方式，将request传递到钩子函数中，将手机号的检验及判断全部集中到钩子函数中# 对手机号做校验，格式是否正确，不能为空
    if form.is_valid():
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'user/register.html', {'form': form})

    form = RegisterModelForm(data=request.POST)
    if form.is_valid():
        # form语句会自动存储，添加新数据到数据库
        # 且form会自动剔除数据库没有的字段，不会将表单多余字段存入
        # 用户表中新增一条用户数据
        instance = form.save()

        project_policy = models.PricePolicy.objects.filter(category=1, title='标准用户版').first()
        # 创建交易记录
        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),  # 生成一个随机字符串，uuid理论上不会重复
            user=instance,
            price_policy=project_policy,
            count=1,
            price=0,
            start_datetime=datetime.datetime.now(),

        )

        return JsonResponse({'status': True, 'data': '/'})
    return JsonResponse({'status': False, 'error': form.errors})


# def login_sms_check(request):
#     if request.method == 'GET':
#         formP = LoginPModelForm(request)  # 账号密码登录表单
#         formS = LoginModelForm()  # 短信登录表单
#         return render(request, 'login.html', {'formP': formP, 'formS': formS})
#     formS = LoginModelForm(data=request.POST)
#     formP = LoginPModelForm(request, data=request.POST)
#     if formS.is_valid():
#         phone = formS.cleaned_data.get('phone')
#         user_object = models.UserInfo.objects.filter(phone=phone).first()
#         if user_object:
#             request.session['user_id'] = user_object.id
#             request.session.set_expiry(60 * 60 * 24)
#             return JsonResponse({'status': True, 'data': '/index/'})
#         else:
#             return JsonResponse({'status': False, 'error': formS.errors})
#     return render(request, 'login.html', {'formP': formP, 'formS': formS})


def logout(request):
    request.session.flush()
    return redirect('/')


def login(request):
    if request.method == 'GET':
        formP = LoginPModelForm(request)  # 账号密码登录表单
        formS = LoginModelForm()  # 短信登录表单
        return render(request, 'login.html', {'formP': formP, 'formS': formS})

    formS = LoginModelForm(data=request.POST)
    formP = LoginPModelForm(request, data=request.POST)
    if not request.headers.get('x-requested-with'):
        # print('先在走的是密码登录')
        if formP.is_valid():
            login_name = formP.cleaned_data['login_name']
            passwd = formP.cleaned_data['password']
            # user_object = models.UserInfo.objects.filter(user_name=username, password=passwd).first()
            user_object = models.UserInfo.objects.filter(Q(email=login_name) | Q(phone=login_name)).filter(
                password=passwd).first()
            if user_object:
                request.session['user_id'] = user_object.id
                request.session.set_expiry(60 * 60 * 24)  # 登录成功后修改session有效期
                return redirect('/index/')
            formP.add_error('user_name', '用户名或密码错误')
    elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # print('OK,checking')
        if formS.is_valid():
            phone = formS.cleaned_data.get('phone')
            user_object = models.UserInfo.objects.filter(phone=phone).first()
            if user_object:
                request.session['user_id'] = user_object.id
                request.session.set_expiry(60 * 60 * 24)
                return JsonResponse({'status': True, 'data': '/index/'})
            else:
                return JsonResponse({'status': False, 'error': formS.errors})
    return render(request, 'login.html', {'formP': formP, 'formS': formS})


def img_code(request):
    """生成图片验证码"""
    from io import BytesIO
    from utils.encode.create_image_code import check_code

    img_object, code = check_code()
    request.session['img_code'] = code
    # session默认失效时间为2周
    request.session.set_expiry(60)  # 手动设置session的过期时间为60s
    # 3. 写入内存(Python3)
    stream = BytesIO()
    img_object.save(stream, 'png')

    return HttpResponse(stream.getvalue())
