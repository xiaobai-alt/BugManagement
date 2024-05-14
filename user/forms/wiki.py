from django import forms
from user import models
from .bootstrap import BootStrapForm

# class BootStrapForm(object):
#     # 对于相同的属性添加操作，可以通过重定义属性的方法集体实现
#     # 将具有相同设置的方法集装成类，继承该类
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for name, field in self.fields.items():
#             field.widget.attrs['class'] = 'form-control'
#             field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


class WikiModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Wiki
        exclude = ['project', ]
        fields = ['article_title', 'content', 'parent_article']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        data_list = [("", "(可选择上级目录)"), ]
        list1 = models.Wiki.objects.filter(project=request.bug_management.project).values_list('id', 'article_title')
        data_list.extend(list1)
        self.fields['parent_article'].choices = data_list
