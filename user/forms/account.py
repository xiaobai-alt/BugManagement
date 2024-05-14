import random
from django import forms
from user import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from utils.tencent.sms import send_sms_single
from django_redis import get_redis_connection
from utils.encode import enpasswd
from .bootstrap import BootStrapForm


# class BootStrapForm(object):
#     # 对于相同的属性添加操作，可以通过重定义属性的方法集体实现
#     # 将具有相同设置的方法集装成类，继承该类
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for name, field in self.fields.items():
#             field.widget.attrs['class'] = 'form-control'
#             field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


# modelform可以帮助我们自动生成标签
class RegisterModelForm(BootStrapForm, forms.ModelForm):
    # 由于models中没有定义手机号类型的格式，可以通过重写的方式，利用正则过滤
    phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    # 为了避免密码在网页明文显示，修改插件属性
    password = forms.CharField(
        label='密码',
        min_length=8,
        max_length=16,
        error_messages={
            'min_length': '密码不得少于8位',
            'max_length': '密码不得大于16位',
        },
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )

    # 为了达到检测用户密码是否正确输入的效果，再次调用我们设定好的密码属性，新增字段作为检测，该字段并不会再数据库中添加
    # 也可以额外添加属性，使用attrs
    confirm_password = forms.CharField(
        label='重复密码',
        min_length=8,
        max_length=16,
        error_messages={
            'min_length': '密码不得少于8位',
            'max_length': '密码不得大于16位',
        },
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入密码'})
    )
    # 没有在model中定义的字段不会添加到数据库中
    code = forms.CharField(label='验证码')

    class Meta:
        model = models.UserInfo
        # fields = '__all__'  # 此处做顺序排版使用，会默认按照models.py中定义的顺序执行，再执行新增的字段
        # 此外还可以自己定义顺序
        fields = ['user_name', 'email', 'password', 'confirm_password', 'phone', 'code']

    def clean_user_name(self):
        user_name = self.cleaned_data['user_name']
        exists = models.UserInfo.objects.filter(user_name=user_name).exists()
        if exists:
            raise ValidationError('用户名已存在')
        return user_name

    def clean_password(self):
        pwd = self.cleaned_data['password']
        return enpasswd.MD5(pwd)
        # 此步的目的在于将密码用密文的形式加密到数据库中，避免泄露

    def clean_confirm_password(self):
        pwd = self.cleaned_data['password']  # cleaned_data是获取已校验的数据，要注意字段定义的顺序，否则取值会出错
        confirm_pwd = enpasswd.MD5(self.cleaned_data['confirm_password'])
        if confirm_pwd != pwd:
            raise ValidationError('请重新确认密码')
        return confirm_pwd

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        exists = models.UserInfo.objects.filter(phone=phone).exists()
        if exists:
            raise ValidationError('手机号已注册')
        return phone

    def clean_code(self):
        # 当方法存在获取其他参数的情况下，要考虑前面的参数可能没有校验通过的情况
        code = self.cleaned_data['code']
        phone = self.cleaned_data.get('phone')
        if not phone:
            return code
        conn = get_redis_connection()
        redis_code = conn.get(phone)
        if not redis_code:
            raise ValidationError('验证码发送失败，请重新发送')
        str_code = redis_code.decode('utf-8')
        if code.strip() != str_code:
            raise ValidationError('验证码错误，请重新输入')
        return code


class LoginModelForm(BootStrapForm, forms.ModelForm):
    # phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    code = forms.CharField(label='验证码')

    class Meta:
        model = models.UserInfo
        # fields = '__all__'  # 此处做顺序排版使用，会默认按照models.py中定义的顺序执行，再执行新增的字段
        # 此外还可以自己定义顺序
        fields = ['phone', 'code']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # 改为返回对象，取值时有改变
        exist = models.UserInfo.objects.filter(phone=phone).exists()
        if not exist:
            raise ValidationError('手机号未注册，请先注册')
        return phone

    def clean_code(self):
        # 当方法存在获取其他参数的情况下，要考虑前面的参数可能没有校验通过的情况
        code = self.cleaned_data['code']
        phone = self.cleaned_data.get('phone')

        if not phone:
            return code
        conn = get_redis_connection()
        redis_code = conn.get(phone)
        if not redis_code:
            raise ValidationError('验证码发送失败，请重新发送')
        str_code = redis_code.decode('utf-8')
        if code.strip() != str_code:
            raise ValidationError('验证码错误，请重新输入')
        return code


class LoginPModelForm(forms.ModelForm):
    login_name = forms.CharField(label='邮箱/手机号登录')
    img_code = forms.CharField(label='图片验证码')

    password = forms.CharField(
        label='密码',
        min_length=8,
        max_length=16,
        error_messages={
            'min_length': '密码不得少于8位',
            'max_length': '密码不得大于16位',
        },
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )

    class Meta:
        model = models.UserInfo
        # fields = '__all__'  # 此处做顺序排版使用，会默认按照models.py中定义的顺序执行，再执行新增的字段
        # 此外还可以自己定义顺序
        fields = ['user_name', 'login_name', 'password', 'img_code']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)

    def clean_user_name(self):
        user_name = self.cleaned_data['user_name']
        exist = models.UserInfo.objects.filter(user_name=user_name).exists()
        if not exist:
            raise ValidationError('用户名有误')
        return user_name

    def clean_password(self):
        # 在钩子中进行加密，返回加密后的密码进行对比
        passwd = enpasswd.MD5(self.cleaned_data['password'])
        return passwd

    def clean_img_code(self):
        img_code = self.cleaned_data['img_code']

        session_code = self.request.session.get('img_code')
        if not session_code:
            raise ValidationError('验证码过期，请刷新')
        if img_code.upper() != session_code.upper():
            raise ValidationError('验证码输入有误，请重新输入')

        return img_code


class SendSMS(forms.Form):
    phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_phone(self):
        """手机号校验钩子"""
        phone = self.cleaned_data['phone']
        # 校验数据库中是否已有手机号
        exist = models.UserInfo.objects.filter(phone=phone).exists()
        tpl = self.request.GET.get('tpl')
        if tpl == 'login':
            if not exist:
                raise ValidationError('手机号未注册，请先注册')
        else:
            if exist:
                raise ValidationError('该手机号已注册')
        # 判断短信模板是否有问题
        template_id = settings.TENCENT_SMS_TEMPLATES.get(tpl)
        if not template_id:
            raise ValidationError('短信模板错误')

        # 发短信&写redis
        code = random.randrange(1000, 9999)
        sms = send_sms_single(phone, template_id, [code, 1])
        if sms['result'] != 0:
            raise ValidationError('短信发送失败，{}'.format(sms['errmsg']))

        # 验证码写入redis(django-redis组件)
        conn = get_redis_connection()
        conn.set(phone, code, ex=60)

        return phone


class ProjectModelForm(forms.Form):
    class Meta:
        model = models.UserInfo
        fields = '__all__'  # 此处做顺序排版使用，会默认按照models.py中定义的顺序执行，再执行新增的字段
        # 此外还可以自己定义顺序
        # fields = ['name', 'defs', 'password', 'img_code']