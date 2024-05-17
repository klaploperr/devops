create user replicator with replication encrypted password 'replicator_password';
select pg_create_physical_replication_slot('replication_slot');

create database tg_bot;
grant all privileges on database tg_bot to postgres;
CREATE TABLE emails(id SERIAL PRIMARY KEY, email VARCHAR(50));
CREATE TABLE phones(id SERIAL PRIMARY KEY, numbers VARCHAR(15));
