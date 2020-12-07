create table if not exists channels
(
    id              text
        constraint channels_pk
            primary key,
    url             text,
    name            text,
    downloadvideos  text default True,
    downloadstreams text default True
);

create unique index if not exists channels_id_uindex
    on channels (id);

create unique index if not exists channels_url_uindex
    on channels (url);

create table if not exists videos
(
    id        text
        constraint videos_pk
            primary key,
    url       text,
    channelid text
        references channels,
    filename  int,
    name      text
);

create unique index if not exists videos_id_uindex
    on videos (id);

