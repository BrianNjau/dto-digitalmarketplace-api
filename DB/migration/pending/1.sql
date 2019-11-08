alter table "public"."brief_response" add column "submitted_at" timestamp without time zone;

alter table "public"."brief_response" add column "updated_at" timestamp without time zone;

CREATE INDEX ix_brief_response_submitted_at ON brief_response USING btree (submitted_at);

CREATE INDEX ix_brief_response_updated_at ON brief_response USING btree (updated_at);
