from django.db import models


# Create your models here.

class UserInfo(models.Model):
    user_name = models.CharField(verbose_name='用户名', max_length=32, db_index=True)  # db_index 索引，做查询时速度快
    email = models.EmailField(verbose_name='邮箱', max_length=32)
    phone = models.CharField(verbose_name='手机号', max_length=11)
    password = models.CharField(verbose_name='密码', max_length=32)


class PricePolicy(models.Model):
    """价格策略，用来区分用户的不同权限，收费标准"""
    category_choice = (
        (1, '个人免费版'),
        (2, '一类收费版'),
        (3, '二类收费版'),
        (4, '其他'),
    )
    category = models.SmallIntegerField(verbose_name='收费类型', default=1, choices=category_choice)
    title = models.CharField(verbose_name='标题', max_length=32)
    # PositiveIntegerField正整数类型
    price = models.PositiveIntegerField(verbose_name='价格/年')

    project_num = models.PositiveIntegerField(verbose_name='可创建项目数')
    project_member = models.PositiveIntegerField(verbose_name='单项目最大成员数')
    project_space = models.PositiveIntegerField(verbose_name='单项目空间(G)')
    project_size = models.PositiveIntegerField(verbose_name='单次上传文件最大容量(M)')

    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Transaction(models.Model):
    """交易记录表，用于关联用户与价格策略"""
    status_choice = (
        (1, '未支付'),
        (2, '已支付'),
    )
    status = models.SmallIntegerField(verbose_name='支付状态', choices=status_choice)

    # unique = True 唯一索引，查询速度快，且该字段不可重复
    order = models.CharField(verbose_name='订单号', max_length=64, unique=True)
    user = models.ForeignKey(verbose_name='用户', to='UserInfo', on_delete=models.CASCADE)
    price_policy = models.ForeignKey(verbose_name='价格策略', to='PricePolicy', on_delete=models.CASCADE)

    count = models.IntegerField(verbose_name='数量（年）', help_text='0表示无限期')

    price = models.IntegerField(verbose_name='实际支付')

    start_datetime = models.DateTimeField(verbose_name='开始时间', null=True, blank=True)
    end_datetime = models.DateTimeField(verbose_name='结束时间', null=True, blank=True)

    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Project(models.Model):
    """项目表"""
    COLOR_CHOICES = (
        (1, '#56b8eb'),
        (2, '#f28033'),
        (3, '#ebc656'),
        (4, '#a2d148'),
        (5, '#20BFA4'),
        (6, '#7461c2'),
        (7, '#20bfa3'),
    )

    name = models.CharField(verbose_name='项目名', max_length=32)
    color = models.SmallIntegerField(verbose_name='颜色', choices=COLOR_CHOICES, default=1)
    defs = models.CharField(verbose_name='项目描述', max_length=255, null=True, blank=True)
    use_space = models.BigIntegerField(verbose_name='项目已使用空间(B)', default=0, help_text='字节')
    star = models.BooleanField(verbose_name='星标', default=False)

    bucket = models.CharField(verbose_name='COS桶', max_length=128)
    region = models.CharField(verbose_name='COS区域', max_length=32)

    join_count = models.SmallIntegerField(verbose_name='参与人数', default=1)
    creator = models.ForeignKey(verbose_name='创建者', to='UserInfo', on_delete=models.CASCADE)
    create_datetime = models.DateTimeField(verbose_name='项目创建时间', auto_now_add=True)


class ProjectUser(models.Model):
    """项目参与者表"""
    user = models.ForeignKey(verbose_name='项目参与者', to='UserInfo', on_delete=models.CASCADE)
    project = models.ForeignKey(verbose_name='参与项目', to='Project', on_delete=models.CASCADE)
    star = models.BooleanField(verbose_name='星标', default=False)

    create_datetime = models.DateTimeField(verbose_name='加入时间', auto_now_add=True)


class Wiki(models.Model):
    project = models.ForeignKey(verbose_name='项目', to='Project', on_delete=models.CASCADE)
    article_title = models.CharField(verbose_name='标题', max_length=32)
    content = models.TextField(verbose_name='内容')

    depth = models.IntegerField(verbose_name='目录深度', default=1)
    parent_article = models.ForeignKey(verbose_name='上级文章', to='self', on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='children')

    def __str__(self):
        return self.article_title


class FileRepository(models.Model):
    """文件库"""
    project = models.ForeignKey(verbose_name='项目', to='Project', on_delete=models.CASCADE)
    file_type_choices = (
        (1, '文件'),
        (2, '文件夹')
    )
    file_type = models.SmallIntegerField(verbose_name='类型', choices=file_type_choices)
    name = models.CharField(verbose_name='文件夹名称', max_length=32, help_text='文件/文件夹名')
    key = models.CharField(verbose_name='文件存储在COS的key', max_length=128, null=True, blank=True)
    file_size = models.BigIntegerField(verbose_name='文件大小(B)', null=True, blank=True, help_text='字节')
    file_path = models.CharField(verbose_name='文件路径', max_length=255, null=True, blank=True)

    parent = models.ForeignKey(verbose_name='上级目录', to='self', related_name='child', null=True, blank=True,
                                on_delete=models.CASCADE)

    update_user = models.ForeignKey(verbose_name='最后更新者', to='UserInfo', on_delete=models.CASCADE)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
