from django.shortcuts import render, reverse, redirect
from user.forms.project import ProjectModels
from django.http import JsonResponse, HttpResponseRedirect
from user import models
from user.forms.wiki import WikiModelForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from utils.tencent.cos import cos
from utils.encode.enpasswd import uid


def wiki(request, project_id):
    """wiki首页展示"""
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id and not str(wiki_id).isdecimal():
        # 将不是数字的非法字符过滤，判断是否为10进制数字
        return render(request, 'user/manage/wiki.html')

    wiki_object = models.Wiki.objects.filter(id=wiki_id, project_id=project_id).first()

    return render(request, 'user/manage/wiki.html', {'wiki_object': wiki_object})


@csrf_exempt
def img_upload(request, project_id):
    # 对于这类没有表单csrf的可以用装饰器免除csrf认证
    """markdown上传插件"""
    print('收到图片了')
    result = {
        'success': 0,
        'message': None,
        'url': None
    }
    # 获取请求中的图片对象
    image_object = request.FILES.get('editormd-image-file')
    if not image_object:
        result['message'] = '文件上传失败'
        return JsonResponse(result)
    # 将文件对象上传到桶中
    bucket = request.bug_management.project.bucket
    region = request.bug_management.project.region
    ext = image_object.name.rsplit('.')[-1]  # 获取图片类型
    key = "{}.{}".format(uid(request.bug_management.user.phone), ext)  # 生成文件

    img_url = cos.img_upload(bucket, region, key, image_object)
    print(img_url)
    # 成功上传后还需要通知markdown，才可以返回页面预览
    result = {
        'success': 1,
        'message': None,
        'url': img_url
    }
    return JsonResponse(result)


def fileupload_demo(request, project_id):
    return render(request, 'user/manage/fileupload_demo.html')


def credential(request):
    """用于cos上传文件时生成临时凭证，阅读官方文档进行设置"""
    from sts.sts import Sts
    import json
    import os
    config = {
        # 请求URL，域名部分必须和domain保持一致
        # 使用外网域名时：https://sts.tencentcloudapi.com/
        # 使用内网域名时：https://sts.internal.tencentcloudapi.com/
        'url': 'https://sts.tencentcloudapi.com/',
        # 域名，非必须，默认为 sts.tencentcloudapi.com
        # 内网域名：sts.internal.tencentcloudapi.com
        'domain': 'sts.tencentcloudapi.com',
        # 临时密钥有效时长，单位是秒
        'duration_seconds': 1800,
        'secret_id': os.environ['COS_SECRET_ID'],
        # 固定密钥
        'secret_key': os.environ['COS_SECRET_KEY'],
        # 设置网络代理
        # 'proxy': {
        #     'http': 'xx',
        #     'https': 'xx'
        # },
        # 换成你的 bucket
        'bucket': 'example-1253653367',
        # 换成 bucket 所在地区
        'region': 'ap-guangzhou',
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': ['exampleobject', 'exampleobject2'],
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            'name/cos:PutObject',
            'name/cos:PostObject',
            # 分片上传
            'name/cos:InitiateMultipartUpload',
            'name/cos:ListMultipartUploads',
            'name/cos:ListParts',
            'name/cos:UploadPart',
            'name/cos:CompleteMultipartUpload'
        ],
        # 临时密钥生效条件，关于condition的详细设置规则和COS支持的condition类型可以参考 https://cloud.tencent.com/document/product/436/71306
        "condition": {
            "ip_equal": {
                "qcs:ip": [
                    "10.217.182.3/24",
                    "111.21.33.72/24",
                ]
            }
        }
    }

    try:
        sts = Sts(config)
        response = sts.get_credential()
        return JsonResponse(response)
        #print('get data : ' + json.dumps(dict(response), indent=4))
    except Exception as e:
        print(e)


def add(request, project_id):
    if request.method == 'GET':
        forms = WikiModelForm(request)
        return render(request, 'user/manage/wiki_form.html', {'forms': forms})
    forms = WikiModelForm(request, request.POST)
    if forms.is_valid():
        # 判断目录深度
        if forms.instance.parent_article:
            forms.instance.depth = forms.instance.parent_article.depth + 1
        else:
            forms.instance.depth = 1
        forms.instance.project = request.bug_management.project
        forms.save()
        return redirect(reverse('user:wiki', kwargs={'project_id': project_id}))
    return render(request, 'user/manage/wiki_form.html', {'forms': forms})


def delete(request, project_id, article_id):
    # print('request is coming')
    # forms = WikiModelForm(request)
    article_object = models.Wiki.objects.filter(project_id=project_id, id=article_id).first()
    if article_object:
        models.Wiki.objects.filter(project_id=project_id, id=article_id).delete()

    return redirect(reverse('user:wiki', kwargs={'project_id': project_id}))


def edit(request, project_id, article_id):
    article_object = models.Wiki.objects.filter(project_id=project_id, id=article_id).first()
    if not article_object:
        return redirect(reverse('user:wiki', kwargs={'project_id': project_id}))
    if request.method == 'GET':
        forms = WikiModelForm(request, instance=article_object)
        return render(request, 'user/manage/wiki_form.html', {'forms': forms})
    forms = WikiModelForm(request, data=request.POST, instance=article_object)
    if forms.is_valid():
        if forms.instance.parent_article:
            # if forms.instance.depth == (forms.instance.parent_article.depth + 1)
            # 如若选择了上级文章，将上级文章的深度加1赋值给被修改的文章
            # 在进行编辑处理时，若被编辑的文章选择了比自己depth大的子文章，会导致该被修改的文章及其子文章depth不合规定，会出现depth的bug，页面显示出错
            if forms.instance.depth < forms.instance.parent_article.depth:
                messages.error(request, '禁止迁移文章到该文章的子文章下')
                return render(request, 'user/manage/wiki_form.html', {'forms': forms})
            forms.instance.depth = forms.instance.parent_article.depth + 1

        else:
            forms.instance.depth = 1
        forms.save()
        url = reverse('user:wiki', kwargs={'project_id': project_id})
        preview_url = "{0}?wiki_id={1}".format(url, article_id)
        return redirect(preview_url)


def catalog(request, project_id):
    data = models.Wiki.objects.filter(project_id=project_id).values('id', 'article_title',
                                                                    'parent_article_id').order_by('depth', 'id')
    # data = models.Wiki.objects.filter(project_id=project_id).values('id', 'article_title','parent_article_id')

    return JsonResponse({'status': True, 'data': list(data)})
