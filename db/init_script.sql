create table artist (
    id int primary key auto_increment,
    name varchar(128) unique not null
);

create table song (
    id int primary key auto_increment,
    file_name varchar(128) unique not null,

    song_name varchar(128) not null ,
    artist_id int not null,

    release_date date,

    constraint foreign key fk_song_artist_id (artist_id) references artist(id) on delete cascade
);

create table tag (
    id int primary key auto_increment,
    value varchar(64) unique not null
);

create table song_tag (
    id int primary key auto_increment,

    song_id int not null,
    tag_id int not null,

    constraint unique ( song_id, tag_id ),

    constraint foreign key fk_song_tag_song_id (song_id) references song(id) on delete cascade,
    constraint foreign key fk_song_tag_tag_id (tag_id) references tag(id) on delete cascade
);