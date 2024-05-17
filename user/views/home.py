from django.shortcuts import render, HttpResponse, redirect
from user import models
from user.forms.account import ProjectModelForm

def index(request):
    ProjectList = models.Project.objects.filter().order_by('-id')
    # print(ProjectList)
    content = {
        'ProjectList': ProjectList,
    }
    return render(request, 'user/index.html', content)


# def blog(request, project_id):
#     project_info = models.Project.objects.filter(id=project_id)
#
#     project_object = models.Project.objects.filter(id=project_id).first()
#     creator_info = models.UserInfo.objects.filter(id=project_object.creator_id)
#     content = {
#         'project_info': project_info,
#         'creator_info': creator_info,
#     }
#     return render(request, 'user/blog.html', content)
def blog(request, project_id):
    return redirect('/manage_project/{0}/dashboard/'.format(project_id))