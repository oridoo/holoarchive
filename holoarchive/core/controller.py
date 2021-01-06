import os
import subprocess
import threading
import time
from multiprocessing import Process

import youtube_dlc
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

from holoarchive import db, config, ytdl_dict

ytdl = youtube_dlc.YoutubeDL(ytdl_dict)


def video_downloader(link):
    """
    Function for downloading a video from youtube
    and adding record to the database
    :param link: url of the video
    :return:
    """
    meta = ytdl.extract_info(str(link), download=True)
    filename = ytdl.prepare_filename(meta)
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
            filename = ytdl.prepare_filename(meta)
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            proc = subprocess.call(
                f"python -m streamlink -Q --hls-live-restart --ffmpeg-video-transcode libx265 "
                f"--hls-segment-timeout 40 --hls-segment-attempts 2 --hls-timeout 300 "
                f'-o "{filename}" "{link}" best', shell=True)
            if os.path.isfile(filename):
                ie = ytdl.process_info(meta)
                ytdl.post_process(filename, ie)
                db_tuple = (meta["id"], link, meta["title"], meta["uploader_id"], filename)
                db.add_video(db_tuple)
                time.sleep(30)
            else: return
    except youtube_dlc.DownloadError:
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

            for thread, url in self.video_threads:
                thread.join(timeout=2)
                if not thread.is_alive():
                    self.active_videos.remove(url)
                    self.video_threads.remove((thread,url))

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
                url = str("https://www.youtube.com/watch?v=" + vidid)
                print("[holoarchive] Attempting download of: " + url)
                thread = Process(name=vidid, target=video_downloader, args=(url,))
                thread.start()
                self.video_threads.append((thread,url))
                self.active_videos.append(vidid)
                time.sleep(5)

    def _fetch_streams(self):
        """
        Fetcher loop for fetching streams
        :return:
        """
        #pool = ThreadPoolExecutor()
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
                        thread = Process(name=url, target=stream_downloader, args=(url,))
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
                meta = ytdl.extract_info(chanurl, download=False)
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
        driver_path = config.GlobalConf.ChromeDriverPath
        options = webdriver.ChromeOptions()
        caps = webdriver.DesiredCapabilities.CHROME
        if config.GlobalConf.SeleniumProxy:
            prox = Proxy()
            prox.proxy_type = ProxyType.MANUAL
            prox.http_proxy = config.GlobalConf.SeleniumProxy
            prox.add_to_capabilities(caps)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument("--headless")
        options.add_argument("--disable-logging")
        options.add_argument("--use-fake-ui-for-media-stream")
        driver = webdriver.Chrome(driver_path, options=options, desired_capabilities=caps)
        driver.implicitly_wait(5)
        try:
            while True:
                for i in self.channels:
                    if (i["id"] == channel["id"] and i["downloadstreams"] == "False") or channel not in self.channels:
                        return
                try:
                    driver.get("https://www.youtube.com/embed/live_stream?channel=" + chanid)
                    div = driver.find_element_by_class_name('ytp-title-link')
                    url = div.get_attribute('href')
                    if url:
                        self.add_stream(url)
                except:
                    continue
                time.sleep(30)
        finally:
            print("[holoarchive] Killing stream fetcher for " + channel["name"])
            driver.close()
            driver.quit()
            return


ctrl = Controller()
