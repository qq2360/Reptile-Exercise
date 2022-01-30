##
#
#   author: QaBns(github account:qq2360)
#   date: 2022.01.30
#   description:This script allows you to download the illustrations on konachan automatically.
#               Please be careful not to use the script for illegal purposes.
#               Otherwise, all consequences will be borne by the illegal users.
#
##

import re
import asyncio
import os
import importlib
import hashlib
import warnings
from itertools import chain
from urllib.request import urlopen, Request
from sys import version_info
from io import BytesIO


def check_and_load_lib(libname: str):
    try:
        return importlib.import_module(libname)
    except ImportError:
        print(f"Unable to find {libname} library.Installing...")
        if os.system("pip install {}".format(libname if libname != "bs4" else "beautifulsoup4")) != 0:
            print(f"Unable to download {libname} library.")
            exit(0)
        else:
            return importlib.reload(libname)


BeautifulSoup = getattr(check_and_load_lib("bs4"), "BeautifulSoup")
click = check_and_load_lib("click")
aiohttp = check_and_load_lib("aiohttp")
UseLegacyCheck = False

def md5_check(path, bytes):
    warnings.warn("The legacy md5 check is deprecated.",DeprecationWarning)
    file_md5_obj = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            data = f.read(128*1024)
            if not data:
                break
            file_md5_obj.update(data)
    file_md5 = file_md5_obj.hexdigest()
    bytes_md5 = hashlib.md5(bytes).hexdigest()
    return file_md5 == bytes_md5


def dHash_check(path,bytes):
    from PIL import Image
    import numpy as np
    def compare(image):
        different = []
        for i in range(8):
            for pixel in range(8):
                different.append(image[i,pixel] > image[i,pixel+1])
        return different
    
    image = Image.open(path)
    remote_image = Image.open(BytesIO(bytes))
    image = np.array(image.resize((9,8),Image.ANTIALIAS).convert('L'),'f')
    remote_image = np.array(remote_image.resize((9,8),Image.ANTIALIAS).convert('L'),'f')
    hash1 = compare(image)
    hash2 = compare(remote_image)
    dist = sum([a != b for a,b in zip(hash1,hash2)])
    similarity = 1 - dist * 1.0 / 64
    return similarity
    
async def download(tasks: list, save_dir: str):
    file_path = None
    pattern = re.compile(r"[A-Z]\w.*")
    try:
        async with aiohttp.ClientSession() as session:
            for task in tasks:
                async with session.get(task) as request:
                    file_path = f"{save_dir}/{re.search(pattern,task).group()}"
                    if request.status != 200:
                        print(
                            "[Debug] Http status code isn't 200!This is a problem.")
                        continue
                    if not os.path.exists(save_dir):
                        os.mkdir(save_dir)
                    byte_array = await request.content.read()
                    if not os.path.exists(file_path) or not (md5_check(file_path,byte_array) if UseLegacyCheck else dHash_check(file_path, byte_array)):
                        with open(file_path, "wb") as stream:
                            stream.write(byte_array)
                    print(f"Download {task} is done!")
    except aiohttp.ClientError as error:
        print("aiohttp client error:", error)
    except asyncio.exceptions.TimeoutError:
        print(
            f"Connect time out!File path:{file_path}.The file will be remove...")
        os.remove(file_path)


def analyze_html_page(search: str, page: int):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"
    }
    try:
        html = urlopen(Request(
            f"https://konachan.net/post?page={page}&tags={search}", headers=header)).read().decode('utf-8')
        # soup = BeautifulSoup(html, 'lxml')  # Use lxml to analyze html content
        soup = BeautifulSoup(html, "html.parser")  # Use python3 implementation
        return map(lambda content: content['href'], soup.find_all("a", class_="directlink largeimg"))
    except:
        raise RuntimeError("Have a error during analyze html process.")


def check_int_arg(ctx, parma, value):
    if value <= 0:
        raise click.BadParameter(
            "The value of this parameter must be greater than 0")
    return value


@click.command()
@click.option('--search', type=str, default="", help='Search name(or tag).(Use English!!!)')
@click.option('--from-start', type=int, default="1", help='Which page start?', callback=check_int_arg)
@click.option('--stop-at', type=int, default="1", help='Which page stop?', callback=check_int_arg)
@click.option('--use-legacy-check',type=bool,default=False,help='Use the legacy check.')
def cli(search, from_start, stop_at,use_legacy_check):
    global UseLegacyCheck
    UseLegacyCheck = use_legacy_check
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    messages = list(chain(*[analyze_html_page(search, page)
                            for page in range(from_start, stop_at + 1)]))
    messages_size = len(messages)
    if messages_size != 0:
        every_task_count = messages_size // 2
        tasks = [messages[i:i + every_task_count]
                 for i in range(0, messages_size, every_task_count)]
        loop.run_until_complete(
                asyncio.gather(*(map(lambda task: asyncio.ensure_future(
                    download(task, "illustrations"),loop=loop), tasks)))
        )
        print("Everything is ok!")
    else:
        print("Not found any illustration.")


if __name__ == "__main__":
    if version_info.major != 3 or version_info.minor < 7:
        raise RuntimeError("Please use Python 3.7 or later.")
    cli(None, None, None)
    pass
