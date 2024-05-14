import time
from django.shortcuts import render, HttpResponse, redirect, reverse
from django.http import JsonResponse
from user.forms.issues import IssuesModelForm
from user import models
from utils.pagination import Pagination

def issues(request, project_id):
    if request.method == 'GET':
        queryset = models.Issues.objects.filter(project_id=project_id)

        page_object = Pagination(
            current_page=request.GET.get('page'),
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET,
            per_page=1
        )

        issues_object_list = queryset[page_object.start:page_object.end]
        form = IssuesModelForm(request=request)
        # issues_object_list = models.Issues.objects.filter(project_id=project_id)
        context = {
            'form': form,
            'issues_object_list': issues_object_list,
            'page_html': page_object.page_html()
        }
        return render(request, 'user/manage/issues.html', context)

    form = IssuesModelForm(request=request, data=request.POST)
    if form.is_valid():
        # 添加问题
        form.instance.project = request.bug_management.project
        form.instance.creator = request.bug_management.user
        form.save()
        return JsonResponse({'status': True, })
    return JsonResponse({'status': False, 'error': form.errors})

def issues_detail(request,project_id):
    """编辑问题"""
    return render(request, 'user/manage/issues_detail.html')
