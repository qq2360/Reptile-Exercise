#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import requests
import os
import sys
import getopt
import datetime
import calendar
import aiohttp
import aiofiles
import asyncio

base_uri="https://i.pximg.net"
origin_uri="https://original.img.cheerfun.dev"
headers={
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
    }

downloadHeaders={
    "Accept":"image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Encoding":"gzip,deflate,br",
    "Connection":"keep-alive",
    "Referer":"https://pixivic.com/dailyRank",
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
    }

currentTime=datetime.datetime.now()

#Change these field
mode=""
date=""
downloadDir=os.path.abspath('.')+"/images"
pages=0
async_mode=False

def AutoSetTime(mode):
    global date
    if mode == "day":
        date=datetime.datetime.strftime(currentTime.date(),'%Y-%m-%d')[:-2]+str(currentTime.day-3)
    elif mode == "week":
        day=""
        month=""
        year=""
        if d:=currentTime.day-7 < 0:
            day=calender.monthrange(currentTime.year,currentTime.month-1)[1]+d
            if currentTime.month-1==0:
                month=12
                year=currentTime.year-1
            else:
                month=currentTime.month-1
                year=currentTime.year
        else:
            day=currentTime.day-7
            month=currentTime.month
            year=currentTime.year
        if month < 10:
            if day < 10:
                date=str(year)+"-0"+str(month)+"-0"+str(day)
            else:
                date=str(year)+"-0"+str(month)+"-"+str(day)
        else:
            date=str(year)+str(month)+str(day)
    elif mode == "month":
        date=datetime.datetime.strftime(currentTime.date(),'%Y-%m-%d')[:-2]+"01"

async def async_download(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=downloadHeaders) as res:
            if res.status == 200:
                if os.path.exists(downloadDir):
                    async with aiofiles.open(downloadDir+url[url.rfind("/"):],"wb") as image:
                        await image.write(await res.content.read())
                else:
                    os.mkdir(downloadDir)
            else:
                print(str(res.status) +"!")

def download(url):
    d_r=requests.get(url,headers=downloadHeaders)
    with open(downloadDir+url[url.rfind("/"):],"wb") as image:
        image.write(d_r.content)


def main(argv):
    global date
    global mode
    global pages
    global downloadDir
    try:
        opts,args=getopt.getopt(argv,"hd:m:p:",["help","date=","mode=","pages=","dir=","enable-async-io"])
    except getopt.GetoptError:
        print("Error:Invaild args.")
        sys.exit()
    for opt,arg in opts:
        if opt == "-h":
            print("usage:<this file>.py -d <date> -m <mode> -p <pages> --dir <downloadDir> [--enable-async-io]")
            sys.exit()
        elif opt in ("-d","--date"):
            date = arg
        elif opt in ("-m","--mode"):
            mode = arg
            if opt not in ("-d","--date"):
                AutoSetTime(mode)
        elif opt in ("-p","--pages"):
            pages = int(arg)
        elif opt in "--dir":
            downloadDir = arg
        elif opt in "--enable-async-io":
            async_mode=True
    for page in range(1,pages+1):
        loop=asyncio.get_event_loop()
        apiurl="https://api.pixivic.com/ranks?page="+str(page)+"&date="+date+"&mode="+mode
        r=requests.get(apiurl,headers=headers)
        r.encoding='utf-8'
        for datas in r.json()["data"]:
            for i_data in datas["imageUrls"]:
                if base_uri in (image_URL:=i_data["original"]):
                    if async_mode:
                        loop.run_until_complete(loop.create_task(async_download(image_URL.replace(base_uri,origin_uri))))
                    else:
                        download(image_URL.replace(base_uri,origin_uri))
    print("Done!Please to check your set dir.")
    print("Your dir:"+downloadDir)

if __name__ == "__main__":
    main(sys.argv[1:])
