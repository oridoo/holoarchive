import os

from flask import Flask

from holoarchive.config import GlobalConf, FlaskConf



app = Flask(__name__)
app.config.from_object(FlaskConf)


ytdl_dict = dict({
    "encoding": "utf-8-sig",
    "simulate": False,
    "format": GlobalConf.YTDLFormat,
    "outtmpl": os.path.join(GlobalConf.DataDirectory, "%(uploader)s",
                            "%(title)s - %(uploader)s - %(id)s.%(ext)s"),
    "sleep_interval": 5,
    "quiet": False,
    'writethumbnail': True,
    "postprocessors": [ {'key': 'FFmpegMetadata'},
                        ],
    "ffmpeg_location": GlobalConf.FFMpegPath,
    "merge-output-format": "mp4",
    "prefer_ffmpeg": True,
    "continuedl": True,
    "noprogress": True
})
