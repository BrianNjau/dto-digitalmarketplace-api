alter table "public"."brief_assessor" add column "created_at" timestamp without time zone not null;

alter table "public"."brief_assessor" add column "updated_at" timestamp without time zone not null;

alter table "public"."brief_assessor" add column "view_day_rates" boolean not null;
