import time
from django.shortcuts import render, HttpResponse, redirect, reverse
from user.forms.project import ProjectModels
from django.http import JsonResponse
from user import models
from utils.tencent.cos import cos
from django.views.decorators.csrf import csrf_exempt
from utils.encode import enpasswd
from django.db.models import Q


def management(request):
    if request.method == 'GET':
        """
            1.我们在get请求时，需要从数据库中获取到星标，创建，参与这三个属性，并将其返回到页面显示
            主要获取数据为：
                1.我创建的项目：有星标，无星标
                2.我参与的项目：有星标，无星标
            2.如何判断星标
                通过列表循环
                列表 = 循环 【我创建的项目】+【我参与的项目】  从而提取有星标的数据
        """
        project_dict = {'star': [], 'my': [], 'join': []}
        my_project_list = models.Project.objects.filter(creator=request.bug_management.user)
        for item in my_project_list:
            if item.star:
                project_dict['star'].append({'value': item, 'type': 'my'})
            else:
                project_dict['my'].append(item)
        join_project_list = models.ProjectUser.objects.filter(user=request.bug_management.user)
        for item in join_project_list:
            if item.star:
                project_dict['star'].append({'value': item.project, 'type': 'join'})
            else:
                project_dict['join'].append(item.project)
        forms = ProjectModels(request)
        return render(request, 'manage/project_manage.html', {'forms': forms, 'project_dict': project_dict})
    forms = ProjectModels(request, data=request.POST)
    if forms.is_valid():
        # 1.在项目创建时新建一个cos桶用户存储该项目的文件
        """桶名格式定义为{用户手机号}-{时间戳}-1319494266"""
        bucket = "{}-{}-1319494266".format(request.bug_management.user.phone, str(int(time.time())))
        region = 'ap-nanjing'
        cos.create_bucket(bucket, region)

        # 验证通过就可以保存，即创建项目,由于页面表单只需要用户填写名称，颜色，描述，因此还需要我们在后再做一次操作
        forms.instance.bucket = bucket
        forms.instance.region = region
        forms.instance.creator = request.bug_management.user
        forms.save()
        return JsonResponse({'status': True})
    else:
        return JsonResponse({'status': False, 'error': forms.errors})


def star_manage(request):
    if request.method == 'POST':
        # print(request.POST.get('project_style'))
        project_id = request.POST.get('project_id')
        if not request.POST.get('project_style'):
            if request.POST.get('project_type') == 'my':
                models.Project.objects.filter(id=project_id, creator=request.bug_management.user).update(star=True)
                return JsonResponse({'status': True, 'data': '/manage/'})
            if request.POST.get('project_type') == 'join':
                models.Project.objects.filter(proiect_id=project_id, user=request.bug_management.user).update(star=True)
                return JsonResponse({'status': True, 'data': '/manage/'})
        if request.POST.get('project_style') == 'cancel':
            # print('删除中')
            if request.POST.get('project_type') == 'my':
                models.Project.objects.filter(id=project_id, creator=request.bug_management.user).update(star=False)
                return JsonResponse({'status': True, 'data': '/manage/'})
            elif request.POST.get('project_type') == 'join':
                models.Project.objects.filter(proiect_id=project_id, user=request.bug_management.user).update(
                    star=False)
                return JsonResponse({'status': True, 'data': '/manage/'})

    return redirect('/manage')


def dashboard(request, project_id):
    return render(request, 'user/manage/dashboard.html')


def statistics(request, project_id):
    return render(request, 'user/manage/statistics.html')


def file(request, project_id):
    return render(request, 'user/manage/file.html')


def settings(request):
    return render(request, 'user/manage/settings.html')


def persion_settings(request):
    if request.method == 'GET':
        # per_info_list = models.UserInfo.objects.filter(id=request.bug_management.user.id)
        # content = {
        #     'per_info_lst': per_info_list,
        # }
        userinfo = models.UserInfo.objects.filter(id=request.bug_management.user.id)
        content = {
            'userinfo': userinfo,
        }
        # for item in userinfo:
        #     print(item.user_name)
        return render(request, 'user/manage/persion_settings.html', content)


@csrf_exempt
def change_pwd(request):
    if request.method == 'GET':
        return render(request, 'user/manage/change_pwd.html')
    data = request.POST
    # print(data)
    user_name = data['username']
    user_email = data['useremail']
    user_phone = data['userphone']
    user_new_pwd = enpasswd.MD5(data['usernewpwd'])
    user_new_pwd_1 = enpasswd.MD5(data['usernewpwd1'])
    if user_new_pwd == user_new_pwd_1:
        models.UserInfo.objects.filter(Q(user_name=user_name) | Q(email=user_email) | Q(phone=user_phone)).update(
            password=user_new_pwd)
        return JsonResponse({'status': True, 'info': '密码修改成功，点击确认返回登陆界面，请您重新登录'})
    else:
        return JsonResponse({'status': False, 'error': '密码确认有误'})


@csrf_exempt
def delete(request):
    if request.method == 'GET':
        project_object_list = models.Project.objects.filter(creator=request.bug_management.user).order_by('-id')
        content = {
            'project_object_list': project_object_list,
        }
        return render(request, 'user/manage/project_delete.html', content)
    # print(request.POST)
    project_id = request.POST.get('fid')
    # 只有项目创建者可以删除项目

    project_object = models.Project.objects.filter(id=project_id).all()
    for item in project_object:
        creator = item.creator
        bucket = item.bucket
        region = item.region
        break
    if request.bug_management.user != creator:
        return render(request, 'user/manage/project_delete.html', {'error': '您不是项目创建者，无权删除'})
    # 删除桶
    #   -首先要删除桶中文件（要注意碎片文件）（找到桶中所有文件并删除）
    #   -删除桶
    # 删除项目
    cos.delete_bucket(bucket, region)
    models.Project.objects.filter(id=project_id).delete()
    return redirect('project_delete')
