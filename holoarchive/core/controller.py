import os
import threading
import time

from selenium import webdriver
from youtube_dlc import YoutubeDL

from holoarchive import db, config, ytdl_dict

ytdl = YoutubeDL(ytdl_dict)


def video_downloader(link):
    print("Attempting download of: " + link)
    meta = ytdl.extract_info(str(link), download=True)
    filename = ytdl.prepare_filename(meta)
    if os.path.isfile(filename):
        db_tuple = (meta["id"], link, meta["title"], meta["uploader_id"], filename)
        db.add_video(db_tuple)


def stream_downloader(link):
    try:
        print("Attempting capture of: " + link)
        meta = ytdl.extract_info(link, download=False)
        if meta:
            filename = ytdl.prepare_filename(meta)
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            os.system(
                f"python -m streamlink --hls-live-restart --ffmpeg-video-transcode h265 --force "
                f'-o "{filename}" "{link}" best')
            if os.path.isfile(filename):
                db_tuple = (meta["id"], link, meta["title"], meta["uploader_id"], filename)
                db.add_video(db_tuple)
    except:
        pass


class Controller:
    def __init__(self):
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
        threading.Thread(name="updater", target=self._updater).start()
        threading.Thread(name="video_fetch", target=self._fetch_videos).start()
        threading.Thread(name="stream_fetch", target=self._fetch_streams).start()
        threading.Thread(name="video_download", target=self._download_videos).start()
        threading.Thread(name="stream_download", target=self._download_streams).start()

    def add_videos(self, ids):
        for i in ids:
            if i not in self.videos or self.active_videos:
                self.videos.add(i)

    def add_stream(self, url):
        if url not in self.streams or self.active_streams:
            self.streams.add(url)

    def _updater(self):
        while True:
            self.channels = db.select_all_channels()
            for i in self.fetchv_threads:
                if not i.is_alive():
                    self.fetchv_threads.remove(i)

            for i in self.video_threads:
                if not i.is_alive():
                    self.active_videos.remove(i.name)
                    self.video_threads.remove(i)

            for i in self.fetchs_threads:
                if not i.is_alive():
                    self.fetchs_threads.remove(i)

            time.sleep(5)

    def _fetch_videos(self):
        while True:
            for i in self.channels:
                if bool(i["downloadvideos"]):
                    thread = threading.Thread(target=self.video_fetcher, args=(i["url"],))
                    thread.start()
                    self.fetchv_threads.append(thread)
            for i in self.fetchv_threads:
                threading.Thread.join(i)
            self.download_videos = True
            time.sleep(360)

    def _download_videos(self):
        while True:
            if (len(self.video_threads) <= int(
                    config.GlobalConf.MaxVideoThreads)) and self.download_videos and self.videos:
                vidid = self.videos.pop()
                url = str("https://www.youtube.com/watch?v=" + vidid)
                thread = threading.Thread(name=vidid, target=video_downloader, args=(url,))
                thread.start()
                self.video_threads.append(thread)
                self.active_videos.append(vidid)
                time.sleep(5)

    def _fetch_streams(self):
        while True:
            for i in self.channels:
                if bool(i["downloadstreams"]):
                    thread = threading.Thread(target=self.stream_fetcher, args=([i["id"]],))
                    thread.start()
                    self.fetchs_threads.append(thread)
            for i in self.fetchs_threads:
                threading.Thread.join(i)
            self.download_streams = True
            time.sleep(20)

    def _download_streams(self):
        while True:
            if self.download_streams and self.streams:
                url = self.streams.pop()
                thread = threading.Thread(target=stream_downloader, args=(url,))
                thread.start()
                self.stream_threads.append(thread)

    def video_fetcher(self, chanurl):
        meta = ytdl.extract_info(chanurl, download=False)
        if meta:
            ids = []
            for entry in meta["entries"]:
                ids.append(entry["id"])
            result = db.videos_filter(ids)
            self.add_videos(result)

    def stream_fetcher(self, chanid):
        driver_path = config.GlobalConf.ChromeDriverPath
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument("headless")
        options.add_argument("--disable-logging")
        driver = webdriver.Chrome(driver_path, options=options)
        driver.implicitly_wait(5)
        try:
            driver.get("https://www.youtube.com/embed/live_stream?channel=" + chanid)
            div = driver.find_element_by_class_name('ytp-title-text')
            url = div.find_element_by_css_selector('a').get_attribute('href')
            driver.quit()
            self.add_stream(url)
        except:
            pass


ctrl = Controller()