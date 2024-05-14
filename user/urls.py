"""
URL configuration for BugMangement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from .views import account, home, manage, wiki, file, issues

urlpatterns = [
    # path('admin/', admin.site.urls),
    # 登录，注册,注销等相关路径
    path('', account.login, name='login'),  # 作为网站登录展示
    path('logout/', account.logout, name='logout'),
    path('register/', account.register, name='register'),
    path('index/', home.index, name='index'),
    re_path(r'^blog/(?P<project_id>\d+)/', home.blog, name='blog'),

    path('send/sms', account.send_sms, name='send_sms'),
    path('img_code/', account.img_code, name='img_code'),

    # 项目管理相关路径
    path('manage/', manage.management, name='management'),
    path('manage/star/', manage.star_manage, name='star_manage'),

    path('settings/', manage.settings, name='settings'),
    path('settings/delete/', manage.delete, name='project_delete'),
    path('settings/persion_settings/', manage.persion_settings, name='persion_settings'),
    path('settings/change_pwd/', manage.change_pwd, name='change_pwd'),

    re_path(r'^manage_project/(?P<project_id>\d+)/', include([
        re_path('dashboard/$', manage.dashboard, name='dashboard'),
        re_path('statistics/$', manage.statistics, name='statistics'),



        re_path('file/$', file.file, name='file'),
        re_path('file/delete/$', file.delete, name='file_delete'),
        re_path('file/post/$', file.post, name='file_post'),
        re_path(r'file/download/(?P<file_id>\d+)/$', file.download, name='file_download'),
        re_path('cos_credential$', file.cos_credential, name='cos_credential'),

        re_path('wiki/$', wiki.wiki, name='wiki'),
        re_path('wiki/add/$', wiki.add, name='wiki_add'),
        re_path('wiki/img_upload/$', wiki.img_upload, name='wiki_img_upload'),
        re_path('wiki/file_upload/demo$', wiki.fileupload_demo, name='wiki_fileupload_demo'),
        re_path('wiki/cos/credential/$', wiki.credential, name='wiki_credential'),
        re_path(r'wiki/delete/(?P<article_id>\d+)/$', wiki.delete, name='wiki_delete'),
        re_path(r'wiki/edit/(?P<article_id>\d+)/$', wiki.edit, name='wiki_edit'),
        re_path('wiki/catalog/$', wiki.catalog, name='WikiCatalog'),

        re_path('issues/$', issues.issues, name='issues'),
        re_path(r'issues/detail/(?P<issues_id>\d+)/$', issues.issues_detail, name='issues_detail'),

    ], None
    ))

]
