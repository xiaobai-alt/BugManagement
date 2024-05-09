from django import forms
from user import models


class BootStrapForm(object):
    # 对于相同的属性添加操作，可以通过重定义属性的方法集体实现
    # 将具有相同设置的方法集装成类，继承该类
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


class IssuesModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Issues
        exclude = ['project', 'creator', 'create_datetime', 'latest_update_datetime']
