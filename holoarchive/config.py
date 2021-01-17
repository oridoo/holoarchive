import configparser
import os

config = configparser.ConfigParser()

conffile = os.getenv("HOLOARCHIVE_CONFIG") or \
           os.path.join(os.path.dirname(__file__), "../config.ini")


if not os.path.isfile(conffile):
    config["Global"] = dict(datadirectory=os.path.join(os.path.dirname(__file__), '../Data'),
                            ffmpeg_path="",
                            chromedriver_path="",
                            ytdl_format="bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
                            max_video_threads="3",
                            sscraper_proxy="")
    config["Flask"] = dict(secretkey="9cglace094k7")

    config.write(open(conffile, "w"))

else:
    config.read(conffile)

if not os.path.isdir(config["Global"]["DataDirectory"]):
    os.makedirs(config["Global"]["DataDirectory"])


class FlaskConf(object):
    SECRET_KEY = config["Flask"]["SecretKey"]


class GlobalConf(object):
    DataDirectory = config["Global"]["DataDirectory"]
    FFMpegPath = config["Global"]["ffmpeg_path"]
    YTDLFormat = config["Global"]["ytdl_format"]
    MaxVideoThreads = config["Global"]["max_video_threads"]
    ScraperProxy = config["Global"]["scraper_proxy"]
