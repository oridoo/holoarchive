from __future__ import unicode_literals

import argparse
import json
import os
import sys
import threading
import time

import enlighten
import youtube_dl as yt
from selenium import webdriver

parser = argparse.ArgumentParser(
    description="Download all videos and capture livestreams from a list of youtube channels.")  # TODO

parser.add_argument("-g", "--generate-config", action="store_true", help="generate new config and exit")
args = parser.parse_args()


def ConfGen():
    defaultconf = dict(ChromeDriverDir="chromedriver", DataDirectory="Data", DownloadStreams="True",
                       DownloadVideos="True", Format="bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
                       StreamSleep=300, VideoSleep=3600, ffmpegDir="")
    json.dump(defaultconf, open("config.json", "w"), indent=4)
    print("New config file was generated.")
    sys.exit()


if not os.path.isfile("config.json"):
    ConfGen()

config = json.load(open("config.json"))

status_format = '{program}{fill}Videos status: {statusvid}{fill}Streams Status: {statusstr}{fill} Streams: {streams}'
manager = enlighten.get_manager()
status_bar = manager.status_bar(status_format=status_format,
                                color='underline_bold_slategray_on_dimgray',
                                program="YTArchiver",
                                position=3,
                                statusvid="Unknown",
                                statusstr="Unknown",
                                streams="0",
                                autorefresh=True,
                                min_delta=0.2
                                )


def GetData():
    file = open(
        str(os.path.join(config["DataDirectory"], "channels.txt")),
        encoding="utf-8-sig",
        mode="r")
    channels = file.readlines()
    file = open(
        str(os.path.join(config["DataDirectory"], "downloaded.txt")),
        encoding="utf-8-sig",
        mode="r")
    downloaded = file.readlines()
    return downloaded, channels


# noinspection PyTypeChecker
def DownloadThread():
    status_bar.update(statusvid="Initializing", force=True)
    while True:
        ids = []
        ytdl = yt.YoutubeDL({
            "download_archive": str(config["DataDirectory"]) + "/downloaded.txt",
            "encoding": "utf-8-sig",
            "simulate": False,
            "format": config["Format"],
            "outtmpl": os.path.join(config["DataDirectory"], "%(uploader)s",
                                    "%(title)s - %(uploader)s - %(upload_date)s.%(ext)s"),
            "sleep_interval": 5,
            "quiet": False,
            "ffmpeg_location": config["ffmpegDir"],
            "merge-output-format": "mp4",
            "prefer_ffmpeg": True
        })
        bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| ' + \
                     u'Channels:{count_0:{len_total}d} ' + \
                     u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
        # noinspection PyTypeChecker
        status_bar.update(statusvid="Fetching data", force=True)
        downloaded, channels = GetData()
        chan_counter = manager.counter(total=len(channels), unit="channels", desc="Fetching:", color="green",
                                       position=2)
        chan_counter.refresh()
        chan_counter.update(0)

        for i in channels:
            for attempt in range(3):
                try:
                    meta = ytdl.extract_info(i, download=False)
                    break
                except:
                    print("Exception occured. Trying again...")
                    continue

            for x in meta.get("entries"):
                ids.append(x.get("id"))
            chan_counter.update()

        status_bar.update(statusvid="Downloading videos", force=True)
        vid_counter = manager.counter(total=len(ids), unit="videos", desc="Downloading:", color="blue", position=1)
        vid_counter.refresh()
        vid_counter.update(0)

        for i in ids:
            for attempt in range(3):
                try:
                    ytdl.download(["https://www.youtube.com/watch?v=" + i])
                    vid_counter.update()
                    break
                except:
                    continue

        chan_counter.close()
        vid_counter.close()

        time.sleep(config["VideoSleep"])


def StreamWorker(link):
    ytdl = yt.YoutubeDL({
        "download_archive": str(config["DataDirectory"]) + "/downloaded.txt",
        "encoding": "utf-8-sig",
        "outtmpl": os.path.join(config["DataDirectory"], "%(uploader)s",
                                "%(title)s - %(uploader)s - %(upload_date)s.%(ext)s"),
        "quiet": False,

    })

    try:
        print("Attempting download of: " + link)
        meta = ytdl.extract_info(link, download=False)
        if meta:
            filename = ytdl.prepare_filename(meta)
            os.system("python -m streamlink --hls-live-restart --ffmpeg-video-transcode h265 --force -o " + str(
                '"{}"'.format(filename)) + " " + link + " best")
            if os.path.isfile(filename):
                ytdl.record_download_archive(meta)
    except:
        pass


def StreamThread():
    downloading = []
    threads = []
    status_bar.update(statusstr="Initializing", force=True)
    if not config["ffmpegDir"]:
        raise FileNotFoundError("FFMpeg path not found. Check your config.")

    driver_path = config["ChromeDriverDir"]
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument("headless")
    options.add_argument("log-level=3")
    while True:
        urls = []
        chanids = []
        downloaded, channels = GetData()
        status_bar.update(statusstr="Fetching", force=True)
        print("Fetching active streams...")
        driver = webdriver.Chrome(driver_path, options=options)
        driver.implicitly_wait(10)
        for i in channels:
            chanids.append(i.rsplit('/', 1)[-1])
        for i in chanids:
            try:
                driver.get("https://www.youtube.com/embed/live_stream?channel=" + i)
                time.sleep(2)
                div = driver.find_element_by_class_name('ytp-title-text')
                urls.append(div.find_element_by_css_selector('a').get_attribute('href'))
            except:
                return
        driver.quit()
        urls = list(filter(None, urls))
        urls = list(set(urls) - set(downloading))
        status_bar.update(statusstr="Starting Downloads", force=True)
        try:
            for i in list(urls):
                thread = threading.Thread(target=StreamWorker, args=(i,))
                thread.start()
                time.sleep(10)
                if thread.is_alive():
                    print("Downloading: " + i)
                    downloading.append(i)
                    threads.append(thread)
        except:
            pass

        for i in threads:
            if not i.is_alive():
                threads.remove(i)
        status_bar.update(statusstr="Downloading", streams=str(len(threads)), force=True)
        time.sleep(config["StreamSleep"])


def main():
    time.sleep(1)
    if config["DownloadVideos"] == "False" and config["DownloadStreams"] == "False":
        print("No module enabled. Exiting...")
    else:
        if config["DownloadVideos"] == "True":
            print("Starting Video Downloader module...")
            threading.Thread(target=DownloadThread).start()
        else:
            print("Video Downloader module is disabled.")
            status_bar.update(statusvid="Disabled", force=True)
        if config["DownloadStreams"] == "True":
            print("Starting Stream Downloader module...")
            threading.Thread(target=StreamThread).start()
        else:
            print("Stream Downloader module is disabled.")
            status_bar.update(statusstr="Disabled", force=True)


if __name__ == "__main__":
    main()