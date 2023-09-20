DROP DATABASE IF EXISTS apiknights;

CREATE DATABASE apiknights;

\c apiknights

CREATE TABLE archetypes (
    archetype_id SERIAL PRIMARY KEY,
    class_name VARCHAR NOT NULL,
    archetype_name VARCHAR NOT NULL,
    trait VARCHAR NOT NULL,
    position VARCHAR NOT NULL,
    attack_type VARCHAR NOT NULL,
    ranges JSON NOT NULL,
    cost_on_e1 BOOLEAN,
    cost_on_e2 BOOLEAN,
    block_on_e1 BOOLEAN,
    block_on_e2 BOOLEAN
);

CREATE TABLE modules (
    module_id SERIAL PRIMARY KEY,
    module_name VARCHAR NOT NULL,
    level_1_trait_upgrade VARCHAR NOT NULL,
    level_1_stats JSON NOT NULL,
    level_2_talent JSON NOT NULL,
    level_2_stats JSON NOT NULL,
    level_3_talent JSON NOT NULL,
    level_3_stats JSON NOT NULL
);

CREATE TABLE skills (
    skill_id SERIAL PRIMARY KEY,
    skill_name VARCHAR NOT NULL,
    sp_type VARCHAR NOT NULL,
    activation_type VARCHAR NOT NULL,
    l1 JSON NOT NULL,
    l2 JSON NOT NULL,
    l3 JSON NOT NULL,
    l4 JSON NOT NULL,
    l5 JSON NOT NULL,
    l6 JSON NOT NULL,
    l7 JSON NOT NULL,
    m1 JSON,
    m2 JSON,
    m3 JSON
);

CREATE TABLE operators (
    operator_id SERIAL PRIMARY KEY,
    operator_name VARCHAR NOT NULL,
    gamepress_url_name VARCHAR NOT NULL,
    gamepress_link VARCHAR NOT NULL,
    rarity INT NOT NULL,
    archetype_id INT NOT NULL REFERENCES archetypes(archetype_id),
    description VARCHAR,
    quote VARCHAR,
    alter INT REFERENCES operators(operator_id),
    resist INT NOT NULL,
    redeploy INT NOT NULL,
    cost INT NOT NULL,
    block INT NOT NULL,
    interval FLOAT NOT NULL,
    level_stats JSON NOT NULL,
    potentials JSON NOT NULL,
    trust_stats JSON NOT NULL,
    skill_1_id INT REFERENCES skills(skill_id),
    skill_2_id INT REFERENCES skills(skill_id),
    skill_3_id INT REFERENCES skills(skill_id),
    talents JSON NOT NULL,
    module_1_id INT REFERENCES modules(module_id),
    module_2_id INT REFERENCES modules(module_id),
    limited BOOLEAN NOT NULL,
    en_released BOOLEAN NOT NULL,
    en_recruitable BOOLEAN NOT NULL,
    en_release_date DATE,
    en_recruitment_added DATE,
    cn_released BOOLEAN NOT NULL,
    cn_recruitable BOOLEAN NOT NULL,
    cn_release_date DATE,
    cn_recruitment_added DATE
);

CREATE TABLE tags (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR NOT NULL
);

CREATE TABLE operators_tags (
    operator_tag_id SERIAL PRIMARY KEY,
    operator_id INT REFERENCES operators(operator_id),
    tag_id INT REFERENCES tags(tag_id)
);