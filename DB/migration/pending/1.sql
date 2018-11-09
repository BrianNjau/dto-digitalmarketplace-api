DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'case_study_assessment_status_enum') THEN
        create type "public"."case_study_assessment_status_enum" as enum ('unassessed', 'approved', 'rejected');
    END IF;
END$$;


create sequence if not exists "public"."case_study_assessment_domain_criteria_id_seq";

create sequence if not exists "public"."case_study_assessment_id_seq";

create sequence if not exists "public"."domain_criteria_id_seq";

create table if not exists "public"."case_study_assessment" (
    "id" integer not null default nextval('case_study_assessment_id_seq'::regclass),
    "case_study_id" integer not null,
    "user_id" integer not null,
    "comment" character varying,
    "status" case_study_assessment_status_enum not null,
    CONSTRAINT case_study_assessment_pkey PRIMARY KEY (id),
    CONSTRAINT case_study_assessment_case_study_id_fkey FOREIGN KEY (case_study_id)
        REFERENCES public.case_study (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT case_study_assessment_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public."user" (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

create table if not exists "public"."case_study_assessment_domain_criteria" (
    "id" integer not null default nextval('case_study_assessment_domain_criteria_id_seq'::regclass),
    "domain_criteria_id" integer not null,
    "case_study_assessment_id" integer not null,
    CONSTRAINT case_study_assessment_domain_criteria_pkey PRIMARY KEY (id),
    CONSTRAINT case_study_assessment_domain_criteria_domain_criteria_id_fkey FOREIGN KEY (domain_criteria_id)
        REFERENCES public.domain_criteria (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT case_study_assessment_domain_crit_case_study_assessment_id_fkey FOREIGN KEY (case_study_assessment_id)
        REFERENCES public.case_study_assessment (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


CREATE TABLE if not exists "public"."domain_criteria"
(
    id integer NOT NULL DEFAULT nextval('domain_criteria_id_seq'::regclass),
    name character varying COLLATE pg_catalog."default" NOT NULL,
    domain_id integer NOT NULL,
    CONSTRAINT domain_criteria_pkey PRIMARY KEY (id),
    CONSTRAINT domain_criteria_domain_id_fkey FOREIGN KEY (domain_id)
        REFERENCES public.domain (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


CREATE UNIQUE INDEX if not exists case_study_assessment_domain_criteria_pkey ON public.case_study_assessment_domain_criteria USING btree (id);

CREATE UNIQUE INDEX if not exists case_study_assessment_pkey ON public.case_study_assessment USING btree (id);

CREATE UNIQUE INDEX if not exists domain_criteria_pkey ON public.domain_criteria USING btree (id);
