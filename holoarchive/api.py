import shutil, os
import requests

from bs4 import BeautifulSoup
import humanize
from yt_dlp import YoutubeDL

from holoarchive import ytdl_dict, db, core, config

ytdl = YoutubeDL(ytdl_dict)


def add_channel(data):
    """
    POST API for adding a channel to the database
    :param data: Dictionary from the request
    :return:
    """
    url_list = str(data["url"]).split(",")

    for url in url_list:
        name = False
        for i in range(3):
            try:
                req = requests.get(url)
                soup = BeautifulSoup(req.content, "html.parser")
                meta = soup.find("meta", attrs={"property": "og:title"})
                name = meta["content"]
                break
            except:
                pass
        id = url.rsplit('/', 1)[-1]
        print(id)
        if name and not db.channel_exists(id):
            db_tuple = (url.rsplit('/', 1)[-1], url, name,
                        str(bool(data["dlvideo"])), str(bool(data["dlstream"])))
            db.add_channel(db_tuple)
    return True


def remove_channel(data):
    """
    POST API for removing a channel record from the database
    :param data: List of channel IDs to remove
    :return:
    """
    for id in data:
        db.remove_channel(id)
        print("Removed: ", id)
    else:
        return True

def check_online(vidid):
    meta = None
    try:
        meta = ytdl.extract_info(vidid, download=False)
    except: pass
    if meta:
        return True
    else:
        return False

def check_offline(vidid):
    if db.video_exists(vidid):
        video = db.select_video(vidid)
        if os.path.isfile(video["filename"]):
            return True
        else:
            db.remove_video(vidid)
            return None
    else:
        return None

def remove_video(data):
    vidid = data["vidid"]
    if check_offline(vidid):
        video = db.select_video(vidid)
        db.remove_video(vidid)
        if bool(data["fs"]):
            os.remove(video["filename"])
        return True
    else:
        return False

def add_video(data):
    if bool(data["force"]):
        core.ctrl.start_video_download(data["vidid"])
        return True
    else:
        core.ctrl.add_videos([data["vidid"]])
        return True

def get_status():
    """
    GET API for getting status of the daemon
    :rtype: dict
    """
    #disk_usage = shutil.disk_usage(config.GlobalConf.DataDirectory)._asdict()
    #for k, v in disk_usage.items():
    #    disk_usage[k] = humanize.naturalsize(v)
    channel_count = len(core.ctrl.channels)
    video_count = len(core.ctrl.videos)
    active_streams = core.ctrl.active_streams
    active_videos = core.ctrl.active_videos
    active_fetchers = len(core.ctrl.fetchv_threads) + len(core.ctrl.fetchs_threads)
    videos_downloaded_count = db.video_count()
    downloading_streams = str(core.ctrl.download_streams)
    downloading_videos = str(core.ctrl.download_videos)
    status = dict(#disk=disk_usage,
                  chan_count=channel_count,
                  vid_count=video_count,
                  a_streams=active_streams,
                  a_videos=active_videos,
                  a_fetchers=active_fetchers,
                  down_count=videos_downloaded_count,
                  dl_streams=downloading_streams,
                  dl_videos=downloading_videos
                  )
    return status
