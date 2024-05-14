"""
分页组件使用示例：

    obj = Pagination(request.GET.get('page',1),len(USER_LIST),request.path_info)
    page_user_list = USER_LIST[obj.start:obj.end]
    page_html = obj.page_html()

    return render(request,'index.html',{'users':page_user_list,'page_html':page_html})


"""


class Pagination(object):

    # def __init__(self, current_page, all_count, base_url, query_params, per_page_num=30, pager_count=11):
    #     """
    #     封装分页相关数据
    #     :param current_page: 当前页
    #     :param all_count:    数据库中的数据总条数
    #     :param per_page_num: 每页显示的数据条数
    #     :param base_url: 分页中显示的URL前缀
    #     :param query_params: QueryDict对象，内部含有所有当前的URL的原条件
    #     :param pager_count:  最多显示的页码个数
    #     """
    #
    #     try:
    #         current_page = int(current_page)
    #     except Exception as e:
    #         current_page = 1
    #
    #     if current_page < 1:
    #         current_page = 1
    #
    #     self.current_page = current_page
    #
    #     self.all_count = all_count
    #     self.per_page_num = per_page_num
    #
    #     self.base_url = base_url
    #
    #     # 总页码
    #     all_pager, tmp = divmod(all_count, per_page_num)
    #     if tmp:
    #         all_pager += 1
    #     self.all_pager = all_pager
    #
    #     self.pager_count = pager_count
    #     self.pager_count_half = int((pager_count - 1) / 2)
    def __init__(self, current_page, all_count, base_url, query_params, per_page=30, pager_page_count=11):
        """
        封装分页相关数据
        :param current_page: 当前页
        :param all_count:    数据库中的数据总条数
        :param per_page: 每页显示的数据条数
        :param base_url: 分页中显示的URL前缀
        :param query_params: QueryDict对象，内部含有所有当前的URL的原条件
        :param pager_page_count:  最多显示的页码个数
        """
        self.base_url = base_url
        try:
            self.current_page = int(current_page)
            if self.current_page <= 0:
                self.current_page = 1
        except Exception as e:
            self.current_page = 1

        query_params = query_params.copy()
        query_params._mutable = True
        self.query_params = query_params
        self.all_count = all_count
        self.per_page = per_page
        self.pager_page_count = pager_page_count

        # 总页码
        pager_count, b = divmod(all_count, per_page)
        if b != 0:
            pager_count += 1
        self.pager_count = pager_count

        half_pager_page_count = int(pager_page_count / 2)
        self.half_pager_page_count = half_pager_page_count

    @property
    def start(self):
        return (self.current_page - 1) * self.per_page

    @property
    def end(self):
        return self.current_page * self.per_page

    def page_html(self):
        if self.all_count == 0:
            return ""
        # 如果总页码 < 11个：
        if self.pager_count <= self.pager_page_count:
            pager_start = 1
            pager_end = self.pager_count
        # 总页码  > 11
        else:
            # 当前页如果<=页面上最多显示11/2个页码
            if self.current_page <= self.half_pager_page_count:
                pager_start = 1
                pager_end = self.pager_page_count

            # 当前页大于5
            else:
                # 页码翻到最后
                if (self.current_page + self.half_pager_page_count) > self.pager_count:
                    pager_end = self.pager_count
                    pager_start = self.pager_count - self.pager_page_count + 1
                else:
                    pager_start = self.current_page - self.half_pager_page_count
                    pager_end = self.current_page + self.half_pager_page_count

        page_list = []

        # first_page = '<li><a href="%s?page=%s">首页</a></li>' % (self.base_url, 1,)
        # page_list.append(first_page)

        if self.current_page <= 1:
            prev_page = '<li><a href="#">上一页</a></li>'
        else:
            self.query_params['page'] = self.current_page - 1
            prev_page = '<li><a href="%s?%s">上一页</a></li>' % (self.base_url, self.query_params.urlencode())

        page_list.append(prev_page)

        for i in range(pager_start, pager_end + 1):
            self.query_params['page'] = i
            if i == self.current_page:
                tpl = '<li class="active"><a href="%s?%s">%s</a></li>' % (
                self.base_url, self.query_params.urlencode(), i,)
            else:
                tpl = '<li><a href="%s?%s">%s</a></li>' % (self.base_url, self.query_params.urlencode(), i,)
            page_list.append(tpl)

        if self.current_page >= self.pager_count:
            next_page = '<li><a href="#">下一页</a></li>'
        else:
            self.query_params['pages'] = self.current_page + 1
            next_page = '<li><a href="%s?%s">下一页</a></li>' % (self.base_url, self.query_params.urlencode(),)
        page_list.append(next_page)

        if self.all_count:
            tpl = '<li class="disable"><a>共%s条数据，页码%s/%s页</a></li>' % (
            self.all_count, self.current_page, self.pager_count,)
            page_list.append(tpl)
        # last_page = '<li><a href="%s?page=%s">尾页</a></li>' % (self.base_url, self.pager_count,)
        # page_list.append(last_page)
        page_str = ''.join(page_list)

        return page_str
