# 离线脚本：区别于web进行时的程序，无需启动django项目就可对项目进行修改的脚本文件
# 当然在运行离线脚本时需要进行相关配置
import os
import sys
import django

# os.path.abspath(__file__)获取当前离线脚本的绝对路径os.path.dirname读取路径所在的文件目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)  # 将目录添加到sys的路径识别中，这样才可以读取django项目的settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BugMangement.settings")
django.setup()  # 完成以上配置后才能对django项目进行离线配置

# 只有完成了上述内容后才可以继续编写需要的功能以及导入对应的包