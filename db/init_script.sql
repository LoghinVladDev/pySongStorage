create table artist (
    id int primary key auto_increment,
    name varchar(128) unique not null
);

create table album (
    id int primary key auto_increment,
    name varchar(128) unique not null,
    release_year int
);

create table song (
    id int primary key auto_increment,
    file_name varchar(128) unique not null,

    song_name varchar(128) not null ,
    artist_id int,
    album_id int,

    release_year int,

    duration_sec int,

    constraint foreign key fk_song_album_id (album_id) references album(id) on delete set null,
    constraint foreign key fk_song_artist_id (artist_id) references artist(id) on delete cascade
);

create table tag (
    id int primary key auto_increment,
    name varchar(64) unique not null
);

create table song_tag (
    id int primary key auto_increment,

    song_id int not null,
    tag_id int not null,
    value varchar(64) not null,

    constraint unique ( song_id, tag_id ),

    constraint foreign key fk_song_tag_song_id (song_id) references song(id) on delete cascade,
    constraint foreign key fk_song_tag_tag_id (tag_id) references tag(id) on delete cascade
);

insert into tag(name) values
                             ('codec'),
                             ('channels'),
                             ('sample rate'),
                             ('bit rate');