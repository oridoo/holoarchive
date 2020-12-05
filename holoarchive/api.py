from holoarchive import ytdl, db

def add_channel(data):
    url_list = str(data["url"]).split(",")
    for url in url_list:
        meta = ytdl.extract_info(url,download=False)
        if meta and not db.channel_exists(url.rsplit('/', 1)[-1]):
            db_tuple = (meta.get("entries")[0]["uploader_id"], url, meta.get("entries")[0]["uploader"],
                        str(bool(data["dlvideo"])),str(bool(data["dlstream"])))
            db.add_channel(db_tuple)
