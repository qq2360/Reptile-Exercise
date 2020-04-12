import getopt
import sys
import datetime
import calendar
import aiohttp
import aiofiles
import asyncio
import os
import multiprocessing
from enum import Enum

base_uri = 'https://i.pximg.net'
origin_uri = 'https://original.img.cheerfun.dev'


class ModeEnum(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


async def real_download(task_list):
    async with aiohttp.ClientSession() as session:
        for task in task_list:
            if task['image_type'] != 'manga':
                header = {
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Encoding': 'gzip,deflate,br',
                    'Connection': 'keep-alive',
                    'Referer': 'https://pixivic.com/illusts/' + str(task['image_id']),
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/74.0.3729.131 Safari/537.36'
                }
                async with session.get(url := task['image_url'], headers=header) as response:
                    if response.status == 200:
                        if os.path.exists(downloadDir := os.path.abspath('.') + '/images'):
                            # noinspection PyBroadException
                            try:
                                async with aiofiles.open(filePath := downloadDir + url[url.rfind('/'):], 'wb') as image:
                                    await image.write(await response.content.read())
                            except:
                                os.remove(filePath)
                        else:
                            os.mkdir(downloadDir)
                            await real_download(task_list)
                    else:
                        print(str(response.status) + "!" + "Resource:" + url)
    return


def download(task_list):
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(new_loop.create_task(real_download(task_list)))


# Todo('Make multi-page download work')
async def main(date, which_mode, page_v):
    header = {
        'Origin': 'https://pixivic.com',
        'Referer': 'https://pixivic.com/?VNK=d2x231f3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/74.0.3729.131 Safari/537.36'
    }
    api_url = "https://api.pixivic.com/ranks?page=" + str(page_v) + "&date=" + str(date) + "&mode=" + str(
        which_mode) + "&pageSize=90"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=header) as response:
            resource_json = await response.json()
    image_list = get_image_info(resource_json)
    size = len(image_list) // 5
    for tasks in [image_list[i:i + size] for i in range(0, len(image_list), size)]:
        multiprocessing.Process(target=download, args=(tasks,)).start()
    return


def format_date(year_v, month_v, day_v):
    s_year = str(year_v)
    s_month = str(month_v)
    s_day = str(day_v)
    if month_v < 10 and day_v < 10:
        return s_year + "-0" + s_month + "-0" + s_day
    elif month_v >= 10 and day_v >= 10:
        return s_year + "-" + s_month + "-" + s_day
    return [s_year + "-" + s_month + "-0" + s_day, s_year + "-0" + s_month + "-" + s_day][month_v < 10 or not day_v < 10]


def auto_set_time():
    local_day = datetime.datetime.today().day
    local_month = datetime.datetime.today().month
    local_year = datetime.datetime.today().year
    local_day -= 3
    if local_day <= 0:
        local_month -= 1
        if local_month <= 0:
            local_year -= 1
            local_month = 12
            local_day += calendar.monthrange(local_year, local_month)[1]
    return format_date(local_year, local_month, local_day)


def get_image_info(json):
    data = json['data']
    image_list = []
    for image_message in data:
        for url in image_message['imageUrls']:
            if base_uri in (unprocessed_url := url['original']):
                image_list.append({'image_id': image_message['id'], 'artist_id': image_message['artistId'],
                                   'title': image_message['title'], 'image_type': image_message['type'],
                                   'author': image_message['artistPreView']['name'],
                                   'image_url': unprocessed_url.replace(base_uri, origin_uri)})
                break
    return image_list


if __name__ == '__main__':
    opts = None
    day = None
    month = None
    year = None
    mode = None
    start = None
    stop = None
    isAutoSetTime = True
    UseDefaultMode = True
    page = 1
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:m:y:p:",
                                   ["day=", "month=", "year=", "mode=", "pages=", "start=", "stop="])
    except getopt.GetoptError as e:
        print(e.msg)
        exit(1)
    for opt, arg in opts:
        if opt == "-h":
            print('Usage:\n \
    -h    Print this message.\n \
    -d <value>   Set resource day.\n \
    -m <value>   Set resource month.\n \
    -y <value>   Set resource year.\n \
    -p <value> Set resource page.\n \
    --day=<value> See -d.\n \
    --month=<value> See -m.\n \
    --year=<value> See -y.\n \
    --mode=<value> Set get resource mode.Value must is one of these:day,week,month.If check value failed,try to use default config.\n \
    --page=<value> See -p \
    --start=<value> Set the page to start downloading \
    --stop=<value> Set the page to stop downloading')
            exit(0)
        elif opt in ("-d", "--day"):
            day = arg
            isAutoSetTime = False
        elif opt in ("-m", "--month"):
            month = arg
            isAutoSetTime = False
        elif opt in ("-y", "--year"):
            year = arg
            isAutoSetTime = False
        elif opt in "--mode":
            mode = arg
            UseDefaultMode = False
        elif opt in ("-p", "--pages"):
            page = arg
        elif opt in '--start':
            start = arg
        elif opt in '--stop':
            stop = arg
    loop = asyncio.get_event_loop()
    for date_object in (day, month, year):
        if not isAutoSetTime and date_object is None:
            raise ValueError("Date is invalid.")
        else:
            for enum in ModeEnum.__members__.values():
                if mode == enum.value:
                    break
            else:
                if UseDefaultMode:
                    mode = ModeEnum.DAY.value
                else:
                    raise ValueError('Mode is invalid.')
            loop.run_until_complete(main(auto_set_time(), mode, page))
            break
    else:
        loop.run_until_complete(main(format_date(year, month, day), mode, page))
