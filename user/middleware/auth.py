import datetime

from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect, reverse
from user import models
from django.conf import settings


# 为了方便对request取值及前端获取策略，定义一个类用于request存储用户及其价格策略
class Bugmanage(object):
    def __init__(self):
        self.user = None
        self.price_policy = None
        self.project = None


# 中间件可以帮助我们处理许多效果
class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """利用中间件识别用户是否登录"""
        # 通过实例化对象直接定义user和价格策略为空
        request.bug_management = Bugmanage()
        user_id = request.session.get('user_id')
        user_object = models.UserInfo.objects.filter(id=user_id).first()
        request.bug_management.user = user_object
        """
        # 首先设置无需登录也可以访问的页面白名单,在settings中设置
        若白名单中有该网址，不做过滤，若不存在，做判断，若没有登录，禁止访问，跳转到登录界面
        """

        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return

        if not request.bug_management.user:
            return redirect('/')

        """我们还需要在用户登录后获取用户的权限（价格策略），以便加载不同的功能"""
        # 首先获取用户的最新交易记录，找记录表中其id值最大的一条记录, -id反向查询
        _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()
        # 在判断交易是否过期
        current_datetime = datetime.datetime.now()
        if _object.end_datetime and _object.end_datetime < current_datetime:
            # 如果存在结束时间且已经过期
            _object = models.Transaction.objects.filter(user=user_object, status=2, price_policy__category=1).first()

        request.bug_management.price_policy = _object.price_policy

    def process_view(self, request, view, args, kwargs):
        if not request.path_info.startswith('/manage_project/'):
            return
        project_id = kwargs.get('project_id')

        # 首先判断项目是否为登陆者所有，创建or参与
        project_object = models.Project.objects.filter(creator=request.bug_management.user, id=project_id).first()
        if project_object:
            # 如果为登陆者所有，就可以通过
            request.bug_management.project = project_object
            return
        project_join_object = models.ProjectUser.objects.filter(user=request.bug_management.user, project_id=project_id).first()
        if project_join_object:
            request.bug_management.project = project_object
            return

        return redirect(reverse('user:management'))
