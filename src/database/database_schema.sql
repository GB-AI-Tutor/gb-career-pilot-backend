-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.admission_requirements (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  program_id integer NOT NULL,
  min_fsc_percentage numeric NOT NULL CHECK (min_fsc_percentage >= 0::numeric AND min_fsc_percentage <= 100::numeric),
  required_entry_test text NOT NULL,
  matric_weightage numeric DEFAULT 10.00,
  fsc_weightage numeric DEFAULT 40.00,
  test_weightage numeric DEFAULT 50.00,
  last_closing_aggregate numeric NOT NULL,
  quota_category character varying DEFAULT 'Open Merit'::character varying,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT admission_requirements_pkey PRIMARY KEY (id),
  CONSTRAINT admission_requirements_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.programs(id)
);

CREATE TABLE public.programs (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  university_id integer NOT NULL,
  name text NOT NULL,
  duration_years integer NOT NULL,
  estimated_total_fee numeric NOT NULL,
  has_specific_scholarships boolean DEFAULT false,
  description_embedding USER-DEFINED,
  created_at timestamp with time zone DEFAULT now(),
  field_of_study text,
  CONSTRAINT programs_pkey PRIMARY KEY (id),
  CONSTRAINT programs_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id)
);
CREATE TABLE public.universities (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL CHECK (name::text = lower(name::text)),
  city character varying NOT NULL,
  country character varying DEFAULT 'Pakistan'::character varying,
  sector character varying NOT NULL CHECK (sector::text = ANY (ARRAY['Public'::character varying, 'Private'::character varying, 'Semi-Government'::character varying]::text[])),
  website text,
  ranking_national integer,
  qs_ranking integer,
  founded_year integer,
  has_hostel boolean DEFAULT false,
  has_scholarships boolean DEFAULT false,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT universities_pkey PRIMARY KEY (id)
);
CREATE TABLE public.user_favorite_universities (
  user_id uuid NOT NULL,
  university_id integer NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_favorite_universities_pkey PRIMARY KEY (user_id, university_id),
  CONSTRAINT user_favorite_universities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id),
  CONSTRAINT user_favorite_universities_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id)
);
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  email text NOT NULL UNIQUE,
  full_name text NOT NULL,
  phone text,
  fsc_percentage numeric,
  city text,
  field_of_interest text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  password text UNIQUE,
  refresh_token text UNIQUE,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);

CREATE TABLE public.messages (
  id integer NOT NULL DEFAULT nextval('messages_id_seq'::regclass),
  conversation_id uuid,
  role character varying CHECK (role::text = ANY (ARRAY['user'::character varying, 'assistant'::character varying, 'system'::character varying, 'tool'::character varying]::text[])),
  content text,
  created_at timestamp without time zone DEFAULT now(),
  tool_calls jsonb,
  tool_call_id text,
  CONSTRAINT messages_pkey PRIMARY KEY (id),
  CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id)
);
CREATE TABLE public.conversations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  title character varying,
  created_at timestamp without time zone DEFAULT now(),
  memory jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT conversations_pkey PRIMARY KEY (id),
  CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
