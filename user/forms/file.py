from django import forms
from django.core.exceptions import ValidationError
from user import models
from utils.tencent.cos.cos import file_check
from .bootstrap import BootStrapForm


# class BootStrapForm(object):
#     # 对于相同的属性添加操作，可以通过重定义属性的方法集体实现
#     # 将具有相同设置的方法集装成类，继承该类
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for name, field in self.fields.items():
#             field.widget.attrs['class'] = 'form-control'
#             field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


class FolderModelForm(BootStrapForm, forms.ModelForm):

    def __init__(self, request, parent_object, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_object = parent_object

    class Meta:
        model = models.FileRepository
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name']

        # 先判断目录是否为根目录
        queryset = models.FileRepository.objects.filter(file_type=2, name=name,
                                                        project=self.request.bug_management.project)
        if self.parent_object:
            exist = queryset.filter(parent=self.parent_object).exists()
        else:
            exist = queryset.filter(parent__isnull=True).exists()
        if exist:
            raise ValidationError('文件夹已存在')
        return name


class FileModelForm(forms.ModelForm):
    etag = forms.CharField(label='ETag')

    class Meta:
        model = models.FileRepository
        exclude = ['project', 'file_type', 'update_user', 'update_time']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_file_path(self):
        return 'https://{}'.format(self.cleaned_data['file_path'])

    def clean(self):
        key = self.cleaned_data['key']
        etag = self.cleaned_data['etag']
        size = self.cleaned_data['file_size']
        if not key or not etag:
            return self.cleaned_data
        # 向cos校验
        from qcloud_cos.cos_exception import CosServiceError
        try:
            result = file_check(
                self.request.bug_management.project.bucket,
                self.request.bug_management.project.region,
                key
            )
        except CosServiceError as e:
            # print("1")
            self.add_error("key", '文件不存在')
            return self.cleaned_data
        cos_etag = result.get('ETag')
        if etag != cos_etag:
            self.add_error("etag", 'ETag错误')
            # print("2")
        cos_length = result.get('Content-Length')
        if int(cos_length) != size:
            # print(int(cos_length), size)
            # print("3")
            self.add_error("file_size", '文件大小错误')
        # result.get('ETag')
        # print(result)
        return self.cleaned_data
