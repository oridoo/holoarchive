import os
import subprocess
import threading
import time, datetime
from multiprocessing import Process
import requests

import dateparser
import yt_dlp as youtube_dl
#import youtube_dl
from bs4 import BeautifulSoup

from holoarchive import db, config, ytdl_dict

ytdl = youtube_dl.YoutubeDL(ytdl_dict)
ytdl_f = youtube_dl.YoutubeDL({
    "extract_flat": "in_playlist"
})

def video_downloader(link):
    """
    Function for downloading a video from youtube
    and adding record to the database
    :param link: url of the video
    :return:
    """
    possible_ext = [".mp4", ".webm", ".mkv", ".ts"]
    meta = ytdl.extract_info(str(link), download=True)
    filename = ytdl.prepare_filename(meta)
    if not os.path.isfile(filename):
        path, ext = os.path.splitext(filename)
        for i in possible_ext:
            fn = path + i
            if os.path.isfile(fn):
                filename = fn
                break
    if os.path.isfile(filename):
        db_tuple = (meta["id"], link, meta["title"], meta["uploader_id"], filename)
        db.add_video(db_tuple)


def stream_downloader(link):
    """
    Function for downloading stream using streamlink
    and adding record of it to the database
    :param link: url of the stream
    :return:
    """
    if not link:
        return
    try:
        meta = ytdl.extract_info(link, download=False)
        if meta:
            filename_gen = ytdl.prepare_filename(meta)
            if not os.path.exists(os.path.dirname(filename_gen)):
                os.makedirs(os.path.dirname(filename_gen))
            path, ext = os.path.splitext(filename_gen)
            filename = path + ".mp4"
            proc = subprocess.call(
                f"python -m streamlink -Q --hls-live-restart "
                f"--hls-segment-timeout 40 --hls-segment-attempts 2 --hls-timeout 300 "
                f'-o "{filename}" "{link}" best', shell=True)
            if os.path.isfile(filename) or os.path.isfile(filename_gen):
                db_tuple = (meta["id"], link, meta["title"], meta["uploader_id"], filename)
                db.add_video(db_tuple)
                ytdl.post_process(filename, ie_info=meta)
                time.sleep(30)

            else: return
    except youtube_dl.DownloadError:
        return


class Controller:
    """
    Controller object for managing
    the archiving daemon
    """

    def __init__(self):
        if not os.path.isfile(db.dbfile):
            db.init_db()
        self.channels = db.select_all_channels()
        self.videos = set()
        self.active_videos = []
        self.streams = set()
        self.active_streams = []
        self.fetchv_threads = []
        self.fetchs_threads = []
        self.video_threads = []
        self.stream_threads = []
        self.download_videos = False
        self.download_streams = False

    def start(self):
        """
        Starts all the daemons
        :return:
        """
        threading.Thread(name="updater", target=self._updater, daemon=True).start()
        threading.Thread(name="video_fetch", target=self._fetch_videos, daemon=True).start()
        threading.Thread(name="stream_fetch", target=self._fetch_streams, daemon=True).start()
        threading.Thread(name="video_download", target=self._download_videos, daemon=True).start()
        threading.Thread(name="stream_download", target=self._download_streams, daemon=True).start()

    def add_videos(self, ids):
        """
        Function for adding list of videos to the object
        :param ids: List of video ids
        :return:
        """
        ids = list(filter(None, ids))
        for i in ids:
            if (i not in self.videos) and (i not in self.active_videos):
                self.videos.add(i)

    def add_stream(self, url):
        """
        Function for adding stream url to the object
        :param ids: Video url
        :return:
        """
        if url in self.streams or url in self.active_streams:
            return
        self.streams.add(url)

    def start_video_download(self, vidid):
        url = str("https://www.youtube.com/watch?v=" + vidid)
        print("[holoarchive] Attempting download of: " + url)
        thread = Process(name=vidid, target=video_downloader, args=(url,), daemon=True)
        thread.start()
        self.video_threads.append((thread, vidid))
        self.active_videos.append(vidid)

    def _updater(self):
        """
        Updater loop checking for db updates
        and dead threads.
        :return:
        """
        while True:
            self.channels = db.select_all_channels()
            for i in self.fetchv_threads:
                if not i[0].is_alive():
                    self.fetchv_threads.remove(i)

            for thread, id in self.video_threads:
                thread.join(timeout=2)
                if not thread.is_alive():
                    self.active_videos.remove(id)
                    self.video_threads.remove((thread,id))

            for i in self.fetchs_threads:
                if not i[0].is_alive():
                    self.fetchs_threads.remove(i)

            for thread, url in self.stream_threads:
                thread.join(timeout=2)
                if not thread.is_alive():
                    self.active_streams.remove(url)
                    self.stream_threads.remove((thread,url))

            if len(self.videos) > 0: self.download_videos = True
            if len(self.streams) > 0: self.download_streams = True
            time.sleep(5)

    def _fetch_videos(self):
        """
        Fetcher loop for fetching videos
        :return:
        """
        while True:
            for i in self.channels:
                if i["downloadvideos"] == "True" and not any([tid for tid in self.fetchv_threads if tid[1]==i["id"]]):
                    print("[holoarchive] Starting video fetcher for " + i["name"])
                    thread = threading.Thread(target=self.video_fetcher, args=(i,), daemon=True)
                    thread.start()
                    self.fetchv_threads.append([thread,i["id"]])

            time.sleep(60)

    def _download_videos(self):
        """
        Downloader loop checking for
        queued videos and downloading them
        :return:
        """
        while True:
            if (len(self.video_threads) < int(
                    config.GlobalConf.MaxVideoThreads)) and self.download_videos and self.videos:
                vidid = self.videos.pop()
                self.start_video_download(vidid)
                time.sleep(5)

    def _fetch_streams(self):
        """
        Fetcher loop for fetching streams
        :return:
        """
        while True:
            for i in self.channels:

                if i["downloadstreams"] == "True" and not any([tid for tid in self.fetchs_threads if tid[1]==i["id"]]):
                    print("[holoarchive] Starting stream fetcher for " + i["name"])
                    thread = threading.Thread(target=self.stream_fetcher, args=(i,), daemon=True)
                    thread.start()
                    self.fetchs_threads.append([thread,i["id"]])

            time.sleep(30)

    def _download_streams(self):
        """
        Fetcher loop for fetching streams
        :return:
        """
        while True:
            if (self.download_streams is True) and (len(self.streams) > 0):
                #thread = pool.submit(stream_downloader, url)
                procs = []
                for i in range(5):
                    if len(self.streams) > 0:
                        url = self.streams.pop()
                        print("[holoarchive] Attempting capture of: " + url)
                        thread = threading.Thread(name=url, target=stream_downloader, args=(url,), daemon=True)
                        thread.start()
                        procs.append(thread)
                time.sleep(30)
                for i in procs:
                    if i.is_alive():
                        self.active_streams.append(i.name)
                        self.stream_threads.append((i,i.name))

    def video_fetcher(self, channel):
        """
        Function for fetching videos from youtube channel
        :param chanurl: URL of the channel
        :return:
        """
        chanurl = channel["url"]
        try:
            while True:
                for i in self.channels:
                    if (i["id"] == channel["id"] and i["downloadvideos"] == "False") or channel not in self.channels:
                        return
                meta = ytdl_f.extract_info(chanurl, download=False)
                if meta:
                    ids = []
                    for entry in meta["entries"]:
                        ids.append(entry["id"])

                    if len(ids) > 0:
                        result = db.videos_filter(ids)
                        self.add_videos(result)
                time.sleep(1800)
        finally:
            print("[holoarchive] Killing video fetcher for " + channel["name"])
            return

    def stream_fetcher(self, channel):
        """
        Function for fetching stream urls from channel
        :param chanid: ID of the youtube channel
        :return:
        """

        chanid = channel["id"]
        proxy = None
        if config.GlobalConf.ScraperProxy:
            proxy = {"http" : config.GlobalConf.ScraperProxy}

        try:
            while True:
                for i in self.channels:
                    if (i["id"] == channel["id"] and i["downloadstreams"] == "False") or channel not in self.channels:
                        return
                try:
                    req = requests.get("https://www.youtube.com/embed/live_stream?channel=" + chanid, proxies=proxy)
                    soup = BeautifulSoup(req.content, "html.parser")
                    div = soup.find("div", attrs={"class" : "submessage"})
                    url = div.find("a")["href"]
                    if url:
                        meta = None
                        for i in range(3):
                            try:
                                meta = ytdl.extract_info(url,download=False)
                                break
                            except youtube_dl.DownloadError as e:
                                rdate = str(e).removeprefix("ERROR: This live event will begin ")
                                rdate = dateparser.parse(rdate)
                                date = datetime.datetime.now()
                                sleeptime = rdate - date
                                sleeptime = sleeptime.seconds - 20
                                if sleeptime < 3600 and sleeptime > 30:
                                    time.sleep(sleeptime)

                                elif sleeptime > 3600:
                                    time.sleep(720)

                        if meta: self.add_stream(url)
                except:
                    continue
                time.sleep(30)
        finally:
            print("[holoarchive] Killing stream fetcher for " + channel["name"])
            return


ctrl = Controller()
