DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'permission_type_enum') THEN
        create type "public"."permission_type_enum" as enum ('create_drafts', 'publish_opportunities', 'answer_seller_questions', 'download_responses', 'create_work_orders', 'download_reporting_data');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'team_status_enum') THEN
        create type "public"."team_status_enum" as enum ('created', 'completed', 'deleted');
    END IF;
END$$;

create sequence if not exists "public"."brief_question_id_seq";

create sequence if not exists "public"."team_id_seq";

create sequence if not exists "public"."team_member_id_seq";

create sequence if not exists "public"."team_member_permission_id_seq";

create table if not exists "public"."brief_question" (
    "id" integer not null default nextval('brief_question_id_seq'::regclass),
    "brief_id" integer not null,
    "supplier_code" bigint not null,
    "data" json not null,
    "created_at" timestamp without time zone not null,
    constraint "brief_question_pkey" PRIMARY KEY (id),
    constraint "brief_question_brief_id_fkey" FOREIGN KEY (brief_id) 
        REFERENCES public.brief(id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    constraint "brief_question_supplier_code_fkey" FOREIGN KEY (supplier_code)
        REFERENCES public.supplier(code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


create table if not exists "public"."team" (
    "id" integer not null default nextval('team_id_seq'::regclass),
    "name" character varying not null,
    "email_address" character varying,
    "status" team_status_enum not null,
    constraint "team_pkey" PRIMARY KEY using index "team_pkey"
);


create table if not exists "public"."team_member" (
    "id" integer not null default nextval('team_member_id_seq'::regclass),
    "is_team_lead" boolean not null,
    "team_id" integer not null,
    "user_id" integer not null,
    constraint "team_member_pkey" PRIMARY KEY ("id"),
    constraint "team_member_team_id_fkey" FOREIGN KEY (team_id)
        REFERENCES public.team(id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    constraint "team_member_user_id_fkey" FOREIGN KEY (user_id)
        REFERENCES public."user"(id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


create table if not exists "public"."team_member_permission" (
    "id" integer not null default nextval('team_member_permission_id_seq'::regclass),
    "team_member_id" integer not null,
    "permission" permission_type_enum not null,
    constraint "team_member_permission_pkey" PRIMARY KEY ("id"),
    constraint "team_member_permission_team_member_id_fkey" FOREIGN KEY (team_member_id)
        REFERENCES public.team_member(id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE INDEX if not exists ix_brief_question_created_at ON public.brief_question USING btree (created_at);

CREATE INDEX if not exists ix_team_member_permission_permission ON public.team_member_permission USING btree (permission);
