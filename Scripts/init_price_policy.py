# 本脚本对价格策略离线操作
import base
from user import models


def run():
    # exist = models.PricePolicy.objects.filter(category=1, title='免费版').exists()
    # if not exist:
    #     models.PricePolicy.objects.create(
    #         category=1,
    #         title='标准用户版',
    #         price=0,
    #         project_num=5,
    #         project_member=10,
    #         project_space=5, # 项目总空间大小G
    #         project_size=100,  #  单项目最大容量MB
    #     )
    # exist = models.PricePolicy.objects.filter(category=2, title='vip版').exists()
    # if not exist:
    #     models.PricePolicy.objects.create(
    #         category=2,
    #         title='vip版',
    #         price=99,
    #         project_num=15,
    #         project_member=20,
    #         project_space=10,  # 项目总空间大小G
    #         project_size=500,  # 单项目最大容量MB
    #     )
    exist = models.PricePolicy.objects.filter(category=3, title='svip版').exists()
    if not exist:
        models.PricePolicy.objects.create(
            category=3,
            title='svip版',
            price=199,
            project_num=30,
            project_member=40,
            project_space=20,  # 项目总空间大小G
            project_size=1000,  # 单项目最大容量MB
        )

if __name__ == '__main__':
    run()
