from django.template import Library
from django.shortcuts import reverse
from user import models

register = Library()


@register.inclusion_tag('inclusion/project_menu.html')
def all_project_menu(request):
    # 1.从数据库中获取我创建的所有项目
    my_project_list = models.Project.objects.filter(creator=request.bug_management.user)

    # 2.获取我参与的
    join_project_list = models.ProjectUser.objects.filter(user=request.bug_management.user)
    return {'my': my_project_list, 'join': join_project_list, 'request':request}


@register.inclusion_tag('inclusion/manage_menu_list.html')
def manage_menu_list(request):
    data_list = [
        {'title': '概览', 'url': reverse('user:dashboard', kwargs={'project_id': request.bug_management.project.id})},
        {'title': '问题', 'url': reverse('user:issues', kwargs={'project_id': request.bug_management.project.id})},
        {'title': '统计', 'url': reverse('user:statistics', kwargs={'project_id': request.bug_management.project.id})},
        {'title': 'wiki', 'url': reverse('user:wiki', kwargs={'project_id': request.bug_management.project.id})},
        {'title': '文件', 'url': reverse('user:file', kwargs={'project_id': request.bug_management.project.id})},
        # {'title': '设置', 'url': reverse('user:settings', kwargs={'project_id': request.bug_management.project.id})},
    ]
    for item in data_list:
        if request.path_info.startswith(item['url']):
            item['class'] = 'active'
    return {'data_list': data_list}


@register.inclusion_tag('inclusion/snow.html')
def snow():
    return
