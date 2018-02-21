create type "public"."brief_response_answer_question_enum" as enum ('essentialRequirements', 'niceToHaveRequirements', 'availability', 'dayRate', 'specialistName', 'attachedDocumentURL');

create sequence "public"."brief_response_answer_id_seq";

create sequence "public"."brief_response_contact_id_seq";

create table "public"."brief_response_answer" (
    "id" integer not null default nextval('brief_response_answer_id_seq'::regclass),
    "brief_response_id" integer not null,
    "question_enum" brief_response_answer_question_enum not null,
    "answer" character varying not null
);


create table "public"."brief_response_contact" (
    "id" integer not null default nextval('brief_response_contact_id_seq'::regclass),
    "brief_id" integer not null,
    "supplier_code" bigint not null,
    "email_address" character varying not null
);


alter table "public"."brief_response" add column "withdrawn_at" timestamp without time zone;

CREATE UNIQUE INDEX brief_response_answer_pkey ON brief_response_answer USING btree (id);

CREATE UNIQUE INDEX brief_response_contact_pkey ON brief_response_contact USING btree (id);

CREATE INDEX ix_brief_response_answer_answer ON brief_response_answer USING btree (answer);

CREATE INDEX ix_brief_response_answer_question_enum ON brief_response_answer USING btree (question_enum);

CREATE INDEX ix_brief_response_contact_email_address ON brief_response_contact USING btree (email_address);

CREATE INDEX ix_brief_response_withdrawn_at ON brief_response USING btree (withdrawn_at);

alter table "public"."brief_response_answer" add constraint "brief_response_answer_pkey" PRIMARY KEY using index "brief_response_answer_pkey";

alter table "public"."brief_response_contact" add constraint "brief_response_contact_pkey" PRIMARY KEY using index "brief_response_contact_pkey";

alter table "public"."brief_response_answer" add constraint "brief_response_answer_brief_response_id_fkey" FOREIGN KEY (brief_response_id) REFERENCES brief_response(id);

alter table "public"."brief_response_contact" add constraint "brief_response_contact_brief_id_fkey" FOREIGN KEY (brief_id) REFERENCES brief(id);

alter table "public"."brief_response_contact" add constraint "brief_response_contact_supplier_code_fkey" FOREIGN KEY (supplier_code) REFERENCES supplier(code);

