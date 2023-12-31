import os
import sqlite3

dbfile = os.getenv("HOLOARCHIVE_DB") or \
         os.path.join(os.path.dirname(__file__), "../db.sqlite")

ddlscript = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "db/holoarchive.ddl")

sqlite3.enable_callback_tracebacks(True)


def connection():
    """
    Creates connection to the database
    :return: returns sql connection
    """
    conn = None
    try:
        conn = sqlite3.connect(dbfile)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn


def init_db():
    """
    Initializes database
    :return:
    """
    conn = connection()
    if conn:
        c = sqlite3.Cursor(conn)
        c.executescript(open(ddlscript).read())
        conn.close()


def add_channel(channel):
    """
    Add channel record to database
    :param channel: (id,url,name,downloadvideos,downloadstreams)
    :return:
    """
    conn = connection()
    if conn:
        sql = """INSERT INTO channels(id,url,name,downloadvideos,downloadstreams)
                 VALUES (?,?,?,?,?)"""
        c = sqlite3.Cursor(conn)
        c.execute(sql, channel)
        conn.commit()
        conn.close()
        return True
    else:
        return False


def add_video(video):
    """
    Add video record to database
    :param video: (id,url,name,channelid,filename)
    :returns: bool
    """
    conn = connection()
    if conn:
        sql = """INSERT INTO videos(id,url,name,channelid,filename)
                     VALUES (?,?,?,?,?)"""
        print(f"[holoarchive] Adding video {video[0]} to the database")
        c = sqlite3.Cursor(conn)
        c.execute(sql, video)
        conn.commit()
        conn.close()
        return True
    else:
        return False


def channel_exists(chanid=str):
    """
    Checks if record with channel ID exists
    :param chanid: Channel ID to check
    :returns: Boolean
    """
    conn = connection()
    if conn:
        sql = f"SELECT EXISTS(SELECT 1 FROM channels WHERE id=?)"
        c = sqlite3.Cursor(conn)
        c.execute(sql, [chanid])
        result = bool(c.fetchall()[0][0])
        conn.close()
        return result
    else:
        return None

def video_exists(vidid=str):
    """
    Checks if record with channel ID exists
    :param chanid: Channel ID to check
    :returns: Boolean
    """
    conn = connection()
    if conn:
        sql = f"SELECT EXISTS(SELECT 1 FROM videos WHERE id=?)"
        c = sqlite3.Cursor(conn)
        c.execute(sql, [vidid])
        result = bool(c.fetchall()[0][0])
        conn.close()
        return result
    else:
        return None


def videos_filter(vidids):
    """
    Returns list of not downloaded videos
    :param vidids: list of video ids
    :return: list of videos not in database
    """
    conn = connection()
    if conn:
        sql = "SELECT EXISTS(SELECT 1 FROM videos WHERE id=?)"
        result = []
        for i in vidids:
            c = sqlite3.Cursor(conn)
            c.execute(sql, [i])
            if not bool(c.fetchall()[0][0]):
                result.append(i)
            c.close()
        conn.close()
        return result
    else:
        return None


def select_all_channels():
    """
    Lists all records of channels in the database
    :return: List of dictionaries(rows)
    """
    conn = connection()
    if conn:
        sql = "SELECT * FROM channels"
        # conn.row_factory = sqlite3.Row
        c = sqlite3.Cursor(conn)
        c.execute(sql)
        colname = [d[0] for d in c.description]
        rows = c.fetchall()
        conn.close()
        result = [dict(zip(colname, r)) for r in rows]

        return result
    else:
        return None

def select_video(vidid):
    """
    Lists all records of channels in the database
    :return: List of dictionaries(rows)
    """
    conn = connection()
    if conn:
        sql = "SELECT * FROM videos WHERE id=?"
        # conn.row_factory = sqlite3.Row
        c = sqlite3.Cursor(conn)
        c.execute(sql,[vidid])
        colname = [d[0] for d in c.description]
        row = c.fetchall()[0]
        conn.close()
        result = dict(zip(colname, row))

        return result
    else:
        return None

def remove_channel(chanid=str):
    """
    Removes a channel from database
    :returns: bool
    :param chanid: db id of channel to remove
    """
    conn = connection()
    if conn:
        sql = "DELETE FROM channels WHERE id=?"
        c = sqlite3.Cursor(conn)
        c.execute(sql, [chanid])
        conn.commit()
        conn.close()
        return True
    else:
        return False


def video_count():
    """
    Checks for count of video records
    :return: List of dictionaries(rows)
    """
    conn = connection()
    if conn:
        sql = "SELECT COUNT(*) FROM videos"
        c = sqlite3.Cursor(conn)
        c.execute(sql)
        result = c.fetchone()[0]
        conn.close()
        return result
    else:
        return None

def remove_video(vidid=str):
    """
    Removes a video from database
    :returns: bool
    :param chanid: db id of channel to remove
    """
    conn = connection()
    if conn:
        sql = "DELETE FROM videos WHERE id=?"
        c = sqlite3.Cursor(conn)
        c.execute(sql, [vidid])
        conn.commit()
        conn.close()
        return True
    else:
        return False