from django import forms
from user import models
from django.core.exceptions import ValidationError
from user.forms.widgets import ColorRadioSelect

class BootStrapForm(object):
    # 对于相同的属性添加操作，可以通过重定义属性的方法集体实现
    # 将具有相同设置的方法集装成类，继承该类
    # 为了规划出不希望继承统一样式的属性，定义一个空列表来写入此类属性名，后续集成时可以在对应的类中自己定义并添加该类属性名
    bootstrap_class_exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.bootstrap_class_exclude:
                continue
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


class ProjectModels(BootStrapForm, forms.ModelForm):
    bootstrap_class_exclude = ['color']

    class Meta:
        model = models.Project
        fields = ['name', 'color', 'defs']
        widgets = {
            'defs': forms.Textarea,
            'color': ColorRadioSelect(attrs={'class': 'color-radio'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):
        """
        1.判断当前用户是否创建过此项目
        2.判断当前用户是否还有创建项目的额度
        """
        name = self.cleaned_data['name']
        exist = models.Project.objects.filter(name=name, creator=self.request.bug_management.user).exists()
        if exist:
            raise ValidationError('您已创建该项目')
        # 到用户策略中查询最多能创建项目数
        # self.request.bug_management.price_policy.project_num
        # 查询已创建的项目
        count = models.Project.objects.filter(creator=self.request.bug_management.user).count()
        if count >= self.request.bug_management.price_policy.project_num:
            raise ValidationError('您的项目数已达到最大值，请先充值或删除一些项目')

        return name
