create table hadiths (
    id uuid not null default extensions.uuid_generate_v4 (),
    source_id uuid not null,
    chapter_id uuid not null,
    hadith_no integer not null,
    text_ar text not null,
    text_en text not null,
    text_vector extensions.vector null,
    constraint hadiths_pkey primary key (id),
    constraint hadiths_source_id_chapter_id_hadith_no_key unique (
        source_id,
        chapter_id,
        hadith_no
    ),
    constraint hadiths_chapter_id_fkey foreign KEY (chapter_id) references chapters (id),
    constraint hadiths_source_id_fkey foreign KEY (source_id) references sources (id)
);

create table chapters (
    id uuid not null default extensions.uuid_generate_v4 (),
    source_id uuid not null,
    chapter_no integer not null,
    chapter_name character varying(255) not null,
    constraint chapters_pkey primary key (id),
    constraint chapters_source_id_chapter_no_key unique (source_id, chapter_no),
    constraint chapters_source_id_fkey foreign KEY (source_id) references sources (id)
);

create table sources (
    id uuid not null default extensions.uuid_generate_v4 (),
    name character varying(255) not null,
    description text null,
    is_active boolean not null default true,
    constraint sources_pkey primary key (id),
    constraint sources_name_key unique (name)
);

create view v_hadith_details as
select
    h.id,
    TRIM(
        both
        from s.name
    ) as source_name,
    c.chapter_no,
    TRIM(
        both
        from c.chapter_name
    ) as chapter_name,
    h.hadith_no,
    h.text_en
from
    hadiths h
    join chapters c on h.chapter_id = c.id
    join sources s on h.source_id = s.id
where
    s.is_active = true
order by (
        TRIM(
            both
            from s.name
        )
    ), c.chapter_no, h.hadith_no;