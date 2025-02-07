from datetime import datetime
import os
import sys
import requests
from PIL import Image
import qrcode
import pyperclip
import shutil
import webbrowser
import subprocess
import platform

version = "2.2"
# 通过 Gitee API 获取远端版本号

# response = requests.get(
#     "https://gitee.com/api/v5/repos/ayong007/Picture-processing/tags"
# )
#
# if response.status_code == 200:
#     remote_version = response.json()[0]["name"].lstrip("v")
#     # 比较 version1 和 version2 的大小
#     if remote_version > version:
#         print("GitHub 有新版本，请前往更新")
#         # 打开指定的网址
#         url = "https://github.com/007ayong/Picture-processing/releases/latest"
#         webbrowser.open(url)
#         sys.exit()
# else:
#     print('提醒：检查版本更新失败……')

# 判断当前目录下是否有临时缓存文件夹
if not os.path.exists('./tmp'):
    os.mkdir('./tmp')
# 判断当前目录下是否有img文件夹
if not os.path.exists('./img'):
    os.mkdir('./img')
# 获取当前日期
current_date = datetime.now().date()
# 遍历img文件夹中的文件
for filename in os.listdir('./img'):
    file_path = os.path.join('./img', filename)
    # 检查文件的创建日期
    if os.path.isfile(file_path):
        created_time_timestamp = os.path.getctime(file_path)
        created_time = datetime.fromtimestamp(created_time_timestamp).date()

        # 计算文件创建日期与当前日期的差距
        days_difference = (current_date - created_time).days

        # 如果文件创建日期在7天前，删除文件
        if days_difference >= 7:
            os.remove(file_path)
            print(f"已删除文件: {filename}")

# 输入商品ID
goods_id = input("请输入商品 ID (多个产品以,隔开):")
# 判断输入是否包含中文逗号，如果有转换为英文逗号
if '，' in goods_id:
    goods_id = goods_id.replace('，', ',')
# 如果商品ID为空，则输出错误信息
if goods_id == "":
    print("商品 ID 不能为空")
    exit()

# 将输入的商品ID以“,”分割
goods_id = goods_id.split(",")

while True:
    current_date = datetime.now().strftime("%y%m%d")
    date = input(f"请输入日期(例如{current_date}): ")
    if not date:
        print("已默认使用当前系统日期")
        date = current_date
        break
    if len(date) == 6 and date.isdigit():
        break
    print("日期格式有误，请输入 6 位数字")

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 将商品ID循环执行
for i in goods_id:
    # 定义图像链接为：https://union.lizhi.io/partner/product/[商品ID]/poster
    url = f"https://union.lizhi.io/partner/product/{i}/poster?cid=53qvofdc"
    # 设置忽略系统代理
    session = requests.Session()
    session.trust_env = False
    try:
        # 请求图像链接
        response = session.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败，将引发异常
        # 测试 Content-Disposition 的内容格式是否正确
        # print(response.headers['Content-Disposition'])

        # 如果请求成功
        if response.headers['Content-Type'] == 'application/octet-stream':
            # 从返回头获取图像文件名
            # 「attachment; filename="PhotosRevive_qrcode.jpg"; filename*=UTF-8''PhotosRevive_qrcode.jpg」
            # 分别按文件名的头、尾部分进行切割
            filename = response.headers['Content-Disposition'].split('filename="')[1].split('.jpg"')[0]

            # 将文件名使用 raw_uncode_escape 转义
            filename = filename.encode('raw_unicode_escape').decode('utf-8')
            # 将图像以 日期_filename 保存到临时文件夹
            with open(f"./tmp/{date}_{filename}", 'wb') as f:
                f.write(response.content)
                # 打印下载进度
                print(f"正在处理：{str(goods_id.index(i) + 1)}/{str(len(goods_id))} {filename}")

            # 将图片转换为PIL格式
            img = Image.open(f"./tmp/{date}_{filename}")
            # 生成180*180px的二维码，容错率为L
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            # 定义二维码链接为 https://lizhi.shop/site/products/id/[商品ID]?cid=53qvofdc&hmsr=wechat&hmpl=p[日期]
            qr_url = f"https://lizhi.shop/site/products/id/{i}?cid=53qvofdc&hmsr=wechat&hmpl=p{date}"
            # 将二维码内容设置为：
            qr.add_data(qr_url)
            # 生成二维码，并更改图像大小为180*180px
            qr.make_image()
            # 图像尺寸设置为180*180px
            code_img = qr.make_image(fill_color="black", back_color="white").resize((180, 180))
            # 将code_img贴到图片上760,172位置
            img.paste(code_img, (760, 172))
            # 图片以png格式保存到 img 文件夹
            img.save(f"./img/{date}_{filename}.png", 'PNG')

        else:
            try:
                json_response = response.json()
                if 'message' in json_response and 'error' in json_response['message']:
                    error_message = json_response['message']['error']
                    print(f"错误：图像源文件请求失败，错误信息：{error_message}")
                else:
                    print("未能解析错误信息")
            except ValueError:
                print("错误：无法解析 JSON 响应")

    except requests.exceptions.RequestException as e:
        # 捕获请求异常，输出错误信息，跳过错误的商品ID
        print(f"请求商品ID {i} 时发生异常：{e}")
        continue

# 删除整个临时文件夹
shutil.rmtree('./tmp')

# 如果商品ID只有1个，则输出：原文链接：qr_url
if len(goods_id) == 1:
    qr_url=f"https://lizhi.shop/site/products/id/{goods_id[0]}?cid=53qvofdc&hmsr=wechat&hmpl=p{date}"
    print(f"阅读原文链接：{qr_url}")
    # 将链接复制到剪切板
    pyperclip.copy(qr_url)
    # 禁止跳出
    input("已将链接复制到剪切板，按回车键打开图片目录")

# 如果商品ID数量不为1，则输出：原文链接：商城首页
else:
    web_url = f"https://lizhi.shop/?cid=53qvofdc&hmsr=wechat&hmpl=p{date}"
    print(f"阅读原文链接：{web_url}")
    # 将链接复制到剪切板
    pyperclip.copy(web_url)
    # 禁止跳出
    input("已将链接复制到剪切板，按回车键打开图片目录")

# 获取系统类型名称
os_name = platform.system()

# 使用命令打开文件夹
if os_name == 'Windows':
    subprocess.Popen(r'explorer img')
elif os_name == 'Darwin':
    subprocess.Popen(['open', 'img'])