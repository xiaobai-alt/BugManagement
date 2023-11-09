# 本脚本对价格策略离线操作
import base
from user import models


def run():
    exist = models.PricePolicy.objects.filter(category=1, title='免费版').exists()
    if not exist:
        models.PricePolicy.objects.create(
            category=3,
            title='svip版',
            price=199,
            project_num=30,
            project_member=30,
            project_space=2000,
            project_size=500,
        )


if __name__ == '__main__':
    run()
