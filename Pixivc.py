#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import calendar
import datetime
import getopt
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor,wait,ALL_COMPLETED

import aiofiles
import aiohttp
import asyncio
import requests

base_uri = "https://i.pximg.net"
origin_uri = "https://original.img.cheerfun.dev"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 "
                  "Safari/537.36 "
}

downloadHeaders = {
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Encoding": "gzip,deflate,br",
    "Connection": "keep-alive",
    "Referer": "https://pixivic.com/dailyRank",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 "
                  "Safari/537.36 "
}

currentTime = datetime.datetime.now()

# Change these field
mode = ""
date = ""
downloadDir = os.path.abspath('.') + "/images"
pages = 0
async_mode = False


def AutoSetTime(m):
    global date
    if m == "day":
        date = datetime.datetime.strftime(currentTime, '%Y-%m-%d')[:-2] + str(currentTime.day - 3)
    elif m == "week":
        if d := currentTime.day - 7 < 0:
            day = calendar.monthrange(currentTime.year, currentTime.month - 1)[1] + d
            if currentTime.month - 1 == 0:
                month = 12
                year = currentTime.year - 1
            else:
                month = currentTime.month - 1
                year = currentTime.year
        else:
            day = currentTime.day - 7
            month = currentTime.month
            year = currentTime.year
        if month < 10:
            if day < 10:
                date = str(year) + "-0" + str(month) + "-0" + str(day)
            else:
                date = str(year) + "-0" + str(month) + "-" + str(day)
        else:
            date = str(year) + str(month) + str(day)
    elif m == "month":
        date = datetime.datetime.strftime(currentTime, '%Y-%m-%d')[:-2] + "01"
    return


async def async_download(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=downloadHeaders) as res:
            if res.status == 200:
                if os.path.exists(downloadDir):
                    # noinspection PyBroadException
                    try:
                        async with aiofiles.open(downloadDir + url[url.rfind("/"):], "wb") as image:
                            await image.write(await res.content.read())
                    except:
                        os.remove(downloadDir + url[url.rfind("/"):])
                else:
                    os.mkdir(downloadDir)
                    async_download(downloadDir)
            else:
                print(str(res.status) + "!" + "Resource:" + url)
    return


def download(url):
    d_r = requests.get(url, headers=downloadHeaders)
    if d_r.status_code == 200:
        if os.path.exists(downloadDir):
            with open(downloadDir + url[url.rfind("/"):], "wb") as image:
                image.write(d_r.content)
        else:
            os.mkdir(downloadDir)
            download(downloadDir)
    else:
        print(str(d_r.status_code)+"!"+"Resource:"+url)
    return


def main(argv):
    global date, async_mode
    global mode
    global pages
    global downloadDir
    try:
        opts, args = getopt.getopt(argv, "hd:m:p:", ["help", "date=", "mode=", "pages=", "dir=", "enable-async-io"])
    except getopt.GetoptError:
        print("Error:Invaild args.")
        sys.exit()
    for opt, arg in opts:
        if opt == "-h":
            print("usage:<this file>.py -d <date> -m <mode> -p <pages> --dir <downloadDir> [--enable-async-io]")
            sys.exit()
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ("-m", "--mode"):
            mode = arg
            if opt not in ("-d", "--date"):
                AutoSetTime(mode)
        elif opt in ("-p", "--pages"):
            pages = int(arg)
        elif opt in "--dir":
            downloadDir = arg
        elif opt in "--enable-async-io":
            async_mode = True
    for page in range(1, pages + 1):
        with ThreadPoolExecutor(5) as pool:
            apiurl = "https://api.pixivic.com/ranks?page=" + str(page) + "&date=" + date + "&mode=" + mode
            r = requests.get(apiurl, headers=headers)
            r.encoding = 'utf-8'
            tasks = []
            real_DownloadURL_list=[]
            real_FileName_list=[]
            for datas in r.json()["data"]:
                for i_data in datas["imageUrls"]:
                    if base_uri in (image_URL := i_data["original"]):
                        r_DownloadURL = image_URL.replace(base_uri, origin_uri)
                        real_DownloadURL_list.append(r_DownloadURL)
                        real_FileName_list.append(r_DownloadURL[r_DownloadURL.rfind("/") + 1:])

            for index in range(len(real_DownloadURL_list)):
                real_DownloadURL=real_DownloadURL_list[index]
                real_FileName=real_FileName_list[index]
                if not os.path.exists(downloadDir+"/"+str(real_FileName)):
                    if async_mode:
                        loop = asyncio.get_event_loop()
                        tasks.append(pool.submit(loop.run_until_complete,loop.create_task(async_download(real_DownloadURL))))
                        if index % 5 == 0:
                            wait(tasks,return_when=ALL_COMPLETED)
                            for i in range(0,5):
                                real_DownloadURL_list[i]=None
                                real_FileName_list[i]=None
                    else:
                        tasks.append(pool.submit(download,real_DownloadURL))
                        if index % 5 == 0:
                            wait(tasks,return_when=ALL_COMPLETED)
                            for i in range(0,5):
                                real_DownloadURL_list[i]=None
                                real_FileName_list[i]=None
                else:
                    print("Find Resource:"+real_FileName)
    print("Done!Please to check your set dir.")
    print("Your dir:" + downloadDir)
    return


if __name__ == "__main__":
    main(sys.argv[1:])
