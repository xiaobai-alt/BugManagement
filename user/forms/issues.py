from django import forms
from user import models
from .bootstrap import BootStrapForm


# class BootStrapForm(object):
#     # 对于相同的属性添加操作，可以通过重定义属性的方法集体实现
#     # 将具有相同设置的方法集装成类，继承该类
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for name, field in self.fields.items():
#             if name in self.bootstrap_class_exclude:
#                 continue
#             field.widget.attrs['class'] = 'form-control'
#             field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


class IssuesModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Issues
        exclude = ['project', 'creator', 'create_datetime', 'latest_update_datetime']
        widgets = {
            "assign": forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"}),
            "attention": forms.SelectMultiple(
                attrs={'class': "selectpicker", "data-live-search": "true", "data-actions-box": "true"}),
            "parent": forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"})
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 处理数据初始化
        # 1.获取当前项目的所有问题类型[(1, 'xx'), (2, 'xx')]
        self.fields['issues_type'].choices = models.IssuesType.objects.filter(
            project=request.bug_management.project).values_list('id', 'title')

        # 2.获取当前项目的所有模块
        module_list = [("", "没有选中任何项"), ]
        module_object_list = models.IssuesType.objects.filter(
            project=request.bug_management.project).values_list('id', 'title')
        module_list.extend(module_object_list)
        self.fields['module'].choices = module_list

        # 3.指派和关注者
        # 数据库找到当前项目的参与者 和 创建者
        total_user_list = [(request.bug_management.project.creator_id, request.bug_management.project.creator.user_name), ]
        project_user_list = models.ProjectUser.objects.filter(project=request.bug_management.project).values_list('user_id',
                                                                                                          'user__user_name')
        total_user_list.extend(project_user_list)
        self.fields['assign'].choices = [("", "没有选中任何项")] + total_user_list
        self.fields['attention'].choices = total_user_list

        # 4.当前项目已创建的问题
        parent_list = [("", "没有选中任何项")]
        parent_object_list = models.Issues.objects.filter(project=request.bug_management.project).values_list('id', 'subject')
        parent_list.extend(parent_object_list)
        self.fields['parent'].choices = parent_list

