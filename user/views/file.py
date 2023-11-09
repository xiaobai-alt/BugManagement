import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from django.urls import reverse
from user.forms.file import FolderModelForm, FileModelForm
from user import models
from utils.tencent.cos import cos


def file(request, project_id):
    """文件列表"""
    parent_object = None
    folder_id = request.GET.get('folder', "")  # 有值就取，无值为空字符串

    if folder_id.isdecimal():  # 判断字符串是否为10进制数
        parent_object = models.FileRepository.objects.filter(id=int(folder_id), file_type=2,
                                                             project=request.bug_management.project).first()

    # 查看页面
    if request.method == 'GET':
        # 获取当前目录下所有文件 & 文件夹获取
        header_list = []  # 导航条设置路径
        parent = parent_object
        while parent:
            header_list.insert(0, {'id': parent.id, 'name': parent.name})
            parent = parent.parent

        queryset = models.FileRepository.objects.filter(project=request.bug_management.project)
        if parent_object:
            file_object_list = queryset.filter(parent=parent_object).order_by('-file_type')  # 倒序查询
        else:
            # 根目录
            file_object_list = queryset.filter(parent__isnull=True).order_by('-file_type')
        forms = FolderModelForm(request, parent_object)
        context = {
            'forms': forms,
            'file_object_list': file_object_list,
            'header_list': header_list,
            'folder_object': parent_object
        }
        return render(request, 'user/manage/file.html', context)

    # 添加文件夹 & 文件夹修改
    fid = request.POST.get('fid')
    edit_object = None
    if fid.isdecimal():
        edit_object = models.FileRepository.objects.filter(id=int(folder_id), file_type=2,
                                                           project=request.bug_management.project).first()
    if edit_object:
        forms = FolderModelForm(request, parent_object, data=request.POST, instance=edit_object)
    else:
        forms = FolderModelForm(request, parent_object, data=request.POST)
    if forms.is_valid():
        forms.instance.project = request.bug_management.project
        forms.instance.file_type = 2
        forms.instance.update_user = request.bug_management.user
        forms.instance.parent = parent_object
        forms.save()
        return JsonResponse({'status': True})

    return JsonResponse({'status': False, 'error': forms.errors})


@csrf_exempt
def cos_credential(request, project_id):
    """"""
    # 在获取凭证前要进行容量限制， 单文件 & 总容量
    one_file_size_limit = request.bug_management.price_policy.project_size * 1024 * 1024
    total_size = 0
    file_list = json.loads(request.body.decode('utf-8'))
    # print(file_list)
    for item in file_list:
        # 文件的字节大小  item['size'] = B
        # 数据库中的单文件限制单位为 MB
        if item['size'] > one_file_size_limit:
            msg = "上传的{}超出单次最大限制{}M".format(item['name'], request.bug_management.price_policy.project_size)
            return JsonResponse({'status': False, 'error': msg})
        total_size += item['size']
    # 总容量进行限制
    # print(total_size)
    # print(request.bug_management.price_policy.project_space)  # 项目容许使用的空间
    # print(request.bug_management.project.use_space)  # 项目已经使用的空间
    all_space = request.bug_management.price_policy.project_space * 1024 * 1024
    # print(all_space)
    if request.bug_management.project.use_space + total_size > all_space:
        return JsonResponse({'status': False, 'error': '您的存储空间不足，请升级套餐或删除无用文件'})

    data = cos.get_credential(request.bug_management.project.bucket, request.bug_management.project.region)
    return JsonResponse({'status': True, 'data': data})


def delete(request, project_id):
    """删除文件"""
    fid = request.GET.get('fid')
    # 删除数据库中的文件夹 & 文件（级联删除）
    delete_object = models.FileRepository.objects.filter(id=fid, project=request.bug_management.project).first()
    if delete_object.file_type == 1:
        # 删除文件（数据库删除+COS文件删除，清除文件消耗容量
        # cos桶中删除项目
        cos.file_delete(request.bug_management.project.bucket, request.bug_management.project.region, delete_object.key)
        # 删除文件后更新项目空间
        request.bug_management.project.use_space -= delete_object.file_size
        request.bug_management.project.save()

        # 数据库中删除文件
        delete_object.delete()
    else:
        # 处理删除数据库文件夹，还要查询该文件夹下每一个文件，同时进行文件删除的所有操作

        # 先处理本地数据库的文件夹
        total_size = 0
        delete_key = []
        folder_list = [delete_object, ]
        for folder in folder_list:
            child_list = models.FileRepository.objects.filter(project=request.bug_management.project,
                                                              parent=folder).order_by('-file_type')
            for child in child_list:
                if child.file_type == 2:
                    folder_list.append(child)
                else:
                    # 文件大小汇总
                    total_size += child.file_size

                    # 添加一个列表，用于判断是否执行批量删除
                    delete_key.append({'key': child.key})
        if delete_key:
            # 构造要删除的目录
            folder = f'{delete_object.name}/'
            cos.delete_cos_dir(request.bug_management.project.bucket, request.bug_management.project.region, folder)
        if total_size:
            request.bug_management.project.use_space -= total_size
            request.bug_management.project.save()

        # 数据库中删除文件夹
        delete_object.delete()

    return JsonResponse({'status': True})


@csrf_exempt
def post(request, project_id):
    """已上传成功的文件写入数据库"""
    # print(request.POST)
    form = FileModelForm(request, data=request.POST)
    if form.is_valid():
        # print('ok')
        # 上传成功后，删除库中不存在的字段后新增数据
        data_dict = form.cleaned_data
        data_dict.pop('etag')
        data_dict.update(
            {'project': request.bug_management.project, 'file_type': 1, 'update_user': request.bug_management.user})
        instance = models.FileRepository.objects.create(**data_dict)

        # 更新项目已使用空间
        request.bug_management.project.use_space += data_dict['file_size']
        request.bug_management.project.save()

        result = {
            'id': instance.id,
            'name': instance.name,
            'file_size': instance.file_size,
            'username': instance.update_user.user_name,
            'update_time': instance.update_time.strftime('%Y年-%m月-%d日 %H:%M'),
            # 'file_type': instance.get_file_type_display()
            'download_url': reverse('user:file_download', kwargs={"project_id":project_id, "file_id": instance.id})
        }
        print(result)
        return JsonResponse({'status': True, 'data': result})
    return JsonResponse({'status': False, 'data': '文件出错'})


@csrf_exempt
def download(request, project_id, file_id):
    """下载文件"""
    # 首先到COS中获取文件内容
    import requests
    file_object = models.FileRepository.objects.filter(id=file_id, project_id=project_id).first()
    resp = requests.get(file_object.file_path)
    response = HttpResponse(resp.content)
    response['Content-Disposition'] = 'attachment; filename={}'.format(file_object.name)

    return response