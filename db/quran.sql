CREATE TABLE languages (
    language_code varchar(3) NOT NULL,
    language_name varchar(255) NOT NULL,
    PRIMARY KEY (language_code)
);

CREATE TABLE translators (
    translator_id SERIAL NOT NULL,
    name varchar(255) NOT NULL,
    language_code varchar(3),
    full_name text DEFAULT ''::text,
    is_active boolean DEFAULT true,
    PRIMARY KEY (translator_id),
    CONSTRAINT translators_language_code_fkey FOREIGN key (language_code) REFERENCES languages (language_code)
);

CREATE TABLE surahs (
    surah_id integer NOT NULL,
    name varchar(255) NOT NULL,
    name_transliteration varchar(255),
    name_en varchar(255),
    total_ayas integer NOT NULL,
    "type" varchar(255),
    order_revealed integer,
    rukus integer,
    PRIMARY KEY (surah_id)
);

CREATE TABLE ayahs (
    ayah_id SERIAL NOT NULL,
    surah_id integer,
    ayah_number integer NOT NULL,
    arabic_text_simple text,
    arabic_text_simple_min text,
    arabic_text_simple_plain text,
    arabic_text_simple_clean text,
    arabic_text_uthmani text,
    arabic_text_original text,
    PRIMARY KEY (ayah_id),
    CONSTRAINT ayahs_surah_id_fkey FOREIGN key (surah_id) REFERENCES surahs (surah_id)
);

CREATE TABLE translations (
    translation_id SERIAL NOT NULL,
    ayah_id integer,
    translator_id integer,
    translation_text text,
    PRIMARY KEY (translation_id),
    CONSTRAINT translations_ayah_id_fkey FOREIGN key (ayah_id) REFERENCES ayahs (ayah_id),
    CONSTRAINT translations_translator_id_fkey FOREIGN key (translator_id) REFERENCES translators (translator_id)
);

--DROP VIEW IF EXISTS v_surah_details;
CREATE OR REPLACE VIEW v_surah_details AS
SELECT
    s.surah_id AS surah_no,
    s.name AS surah_name_ar,
    s.name_en AS surah_name,
    a.ayah_number AS ayah_no,
    TRIM(
        BOTH
        FROM a.arabic_text_original
    ) AS arabic_text,
    TRIM(
        BOTH
        FROM t.translation_text
    ) AS translation_text,
    r.full_name AS translator_full_name,
    r.name AS translator_name
FROM (
        (
            (
                ayahs a
                JOIN surahs s ON ((a.surah_id = s.surah_id))
            )
            JOIN translations t ON ((a.ayah_id = t.ayah_id))
        )
        JOIN translators r ON (
            (
                r.translator_id = t.translator_id
            )
        )
    )
WHERE (r.is_active = true)
ORDER BY r.translator_id, s.surah_id, a.ayah_number;