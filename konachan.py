# from bs4 import BeautifulSoup //Only dev environment
# import click //Only dev environment
# import aiohttp //Only dev environment
import re
import asyncio
import os
import importlib
from urllib.request import urlopen


def check_and_load_lib(libname: str):
    try:
        return importlib.import_module(libname)
    except ImportError:
        print("Unable to find {} library.Installing...".format(libname))
        if os.system("pip install {}".format(libname if libname != "bs4" else "beautifulsoup4")) != 0:
            print("Unable to download {} library.".format(libname))
            exit(0)
        else:
            check_and_load_lib(libname)


BeautifulSoup = getattr(check_and_load_lib("bs4"), "BeautifulSoup")
click = check_and_load_lib("click")
aiohttp = check_and_load_lib("aiohttp")


async def download(tasks: list, save_dir: str):
    pattern = re.compile(r"[A-Z]\w.*")
    async with aiohttp.ClientSession() as session:
        for task in tasks:
            async with session.get(task) as request:
                file_path = "{}/{}".format(save_dir, re.search(pattern, task).group())
                if request.status != 200:
                    print("[Debug] Http status code isn't 200!This is a problem.")
                    continue
                if not os.path.exists(save_dir):
                    os.mkdir(save_dir)
                elif not os.path.exists(file_path):
                    with open(file_path, "wb") as stream:
                        stream.write(await request.content.read())


# ToDo("Make the multi-page download work.")
@click.command()
@click.option('--search', default="", help='Search name(or tag).')
def cli(search):
    loop = asyncio.get_event_loop()
    messages = []
    html = urlopen("https://konachan.net/post?tags={}".format(search)).read().decode('utf-8')
    soup = BeautifulSoup(html, 'lxml')
    for content in soup.find_all("a", class_="directlink largeimg"):
        messages.append(content['href'])
    messages_size = len(messages)
    if messages_size != 0:
        every_thread_count = len(messages) // 2
        tasks = [messages[i:i + every_thread_count] for i in range(0, len(messages), every_thread_count)]
        loop.run_until_complete(
            asyncio.wait(map(lambda task: asyncio.ensure_future(download(task, "illustrations")), tasks)))
    else:
        print("Not found any illustration.")


if __name__ == "__main__":
    cli(None)  # 动态语言的通病，IDE不能准确识别对象的类型
    pass
