from qcloud_cos import CosConfig, CosClientError, CosServiceError
from qcloud_cos import CosS3Client
from django.conf import settings
from qcloud_cos.cos_threadpool import SimpleThreadPool



# response = client.delete_object(
#     Bucket='chenhao-1319494266',
# )
def delete_cos_dir(region, folder):
    bucket = 'chenhao-1319494266'
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


def delete_files(file_infos, bucket):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    # 构造批量删除请求
    delete_list = []
    for file in file_infos:
        delete_list.append({"Key": file['Key']})

    response = client.delete_objects(Bucket=bucket, Delete={"Object": delete_list})
    print(response)


if __name__ == '__main__':
    secret_id = settings.TENCENT_COS_ID  # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    secret_key = settings.TENCENT_COS_KEY  # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    region = 'ap-nanjing'  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
    # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

    folder = 'test-folder/'

    delete_cos_dir(region, folder)
