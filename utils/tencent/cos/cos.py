from qcloud_cos import CosConfig, CosClientError, CosServiceError
from qcloud_cos import CosS3Client
from django.conf import settings
from qcloud_cos.cos_threadpool import SimpleThreadPool
from sts.sts import Sts
import json
import os

secret_id = settings.TENCENT_COS_ID  # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
secret_key = settings.TENCENT_COS_KEY  # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
region = 'ap-nanjing'  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket


def create_bucket(bucket, region):
    # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    response = client.create_bucket(
        Bucket=bucket,  # 桶名
        ACL='public-read',  # 公共读 private 私有 /  public-read 公共读私有写 / public-read-write 公共读公共写
    )

    # 配置跨域
    cors_config = {
        'CORSRule': [
            {
                'MaxAgeSeconds': 500,
                'AllowedOrigin': '*',
                'AllowedMethod': ['GET', 'PUT', 'HEAD', 'POST', 'DELETE'],
                'AllowedHeader': '*',
                'ExposeHeader': '*',
            }

        ]
    }
    client.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration=cors_config
    )


def img_upload(bucket, region, key, img_object):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    # 使用高级接口断点续传，失败重试时不会上传已成功的分块(这里重试10次)
    for i in range(0, 10):
        try:
            response = client.upload_file_from_buffer(
                Bucket=bucket,
                Key=key,  # 上传后的文件名称
                Body=img_object,  # 接收对象
            )
            return "https://{}.cos.{}.myqcloud.com/{}".format(bucket, region, key)
            break
        except CosClientError or CosServiceError as e:
            print(e)


def file_delete(bucket, region, key):
    secret_id = settings.TENCENT_COS_ID  # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    secret_key = settings.TENCENT_COS_KEY  # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    region = 'ap-nanjing'  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
    # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    response = client.delete_object(
        Bucket=bucket,
        Key=key
    )


def file_check(bucket, region, key):
    secret_id = settings.TENCENT_COS_ID  # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    secret_key = settings.TENCENT_COS_KEY  # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    region = 'ap-nanjing'  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
    # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    data = client.head_object(
        Bucket=bucket,
        Key=key
    )
    return data


# 删除文件夹
def delete_cos_dir(bucket, region, folder):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    pool = SimpleThreadPool()
    marker = ""
    while True:
        file_infos = []

        # 列举一页100个对象
        response = client.list_objects(Bucket=bucket, Prefix=folder, Marker=marker, MaxKeys=100)

        if "Contents" in response:
            contents = response.get("Contents")
            file_infos.extend(contents)
            pool.add_task(delete_files, file_infos, bucket)

        # 列举完成，退出
        if response['IsTruncated'] == 'false':
            break

        # 列举下一页
        marker = response["NextMarker"]

    pool.wait_completion()
    return None


# 多文件批量删除
def delete_files(file_infos, bucket):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    # 构造批量删除请求
    delete_list = []
    for file in file_infos:
        delete_list.append({"Key": file['Key']})

    response = client.delete_objects(Bucket=bucket, Delete={"Object": delete_list})
    print(response)


def get_credential(bucket, region):
    """获取临时凭证"""
    config = {
        # 临时密钥有效时长，单位是秒
        'duration_seconds': 600,
        'secret_id': settings.TENCENT_COS_ID,
        # 固定密钥
        'secret_key': settings.TENCENT_COS_KEY,
        # 换成你的 bucket
        'bucket': bucket,
        # 换成 bucket 所在地区
        'region': region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        # 'allow_prefix': ['exampleobject', 'exampleobject2'],
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            'name/cos:PutObject',
            # 'name/cos:PostObject',
            # 分片上传
            # 'name/cos:InitiateMultipartUpload',
            # 'name/cos:ListMultipartUploads',
            # 'name/cos:ListParts',
            # 'name/cos:UploadPart',
            # 'name/cos:CompleteMultipartUpload'
        ],
        # 临时密钥生效条件，关于condition的详细设置规则和COS支持的condition类型可以参考 https://cloud.tencent.com/document/product/436/71306
        # "condition": {
        #     "ip_equal": {
        #         "qcs:ip": [
        #             "10.217.182.3/24",
        #             "111.21.33.72/24",
        #         ]
        #     }
        # }
    }

    try:
        sts = Sts(config)
        response = sts.get_credential()
        return response
    except Exception as e:
        print(e)


def delete_bucket(bucket, region):
    """删除桶"""
    # 删除桶中文件
    # 删除碎片文件
    # 删除桶
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    try:
        # 找到文件&删除
        while True:
            # 找到所有文件
            objects = client.list_objects(bucket) # 由于list最大返回值1000，多做几次循环
            contents = objects.get('Contents')
            # contents用于判断是否获取完成
            if not contents:
                break
            # 批量删除
            del_objects = {
                "Quiet": "true",
                "Objects": [{'Key': item["Key"]} for item in contents]
            }
            client.delete_objects(bucket, del_objects)
            # 判断截断是否有后续
            if objects['IsTruncated'] == 'false':
                break

        # 找到碎片&删除
        while True:
            part_upload = client.list_multipart_uploads(bucket)
            uploads = part_upload.get('Upload')
            if not uploads:
                break
            for item in uploads:
                client.abort_multipart_upload(bucket, item['Key'], item['UploadId'])
            if part_upload['IsTruncated'] == 'false':
                break

        # 删除桶
        client.delete_bucket(bucket)
    except CosServiceError as e:
        pass




