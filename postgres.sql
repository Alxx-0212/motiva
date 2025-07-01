--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Debian 14.18-1.pgdg120+1)
-- Dumped by pg_dump version 14.18 (Debian 14.18-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: task_priority_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.task_priority_enum AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH'
);


ALTER TYPE public.task_priority_enum OWNER TO postgres;

--
-- Name: task_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.task_status_enum AS ENUM (
    'ACTIVE',
    'COMPLETED'
);


ALTER TYPE public.task_status_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: tasks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tasks (
    task_id uuid NOT NULL,
    task_name character varying(100) NOT NULL,
    task_description text,
    user_id uuid NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    start_time_utc timestamp with time zone NOT NULL,
    end_time_utc timestamp with time zone NOT NULL,
    priority public.task_priority_enum,
    status public.task_status_enum NOT NULL,
    original_timezone character varying(50),
    recurrence_rule text
);


ALTER TABLE public.tasks OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    hashed_password text NOT NULL,
    bio text,
    timezone character varying(50) NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tasks (task_id, task_name, task_description, user_id, created_at, updated_at, start_time_utc, end_time_utc, priority, status, original_timezone, recurrence_rule) FROM stdin;
df43aa0a-c684-43c3-a945-21215f856e30	Presentation	\N	6e40564d-0ad3-4ec7-828d-84c4970e98b3	2025-06-30 10:41:29.710144+00	2025-06-30 11:14:11.939703+00	2025-08-16 15:00:00+00	2025-08-21 20:00:00+00	\N	ACTIVE	UTC	\N
1438123d-6d10-436d-bf31-e9bd05a9d7c6	Bake a Cake	\N	6e40564d-0ad3-4ec7-828d-84c4970e98b3	2025-06-30 14:18:31.840955+00	2025-07-01 02:42:57.55907+00	2025-07-23 12:00:00+00	2025-07-23 14:00:00+00	\N	ACTIVE	UTC	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, email, hashed_password, bio, timezone, created_at, updated_at) FROM stdin;
6e40564d-0ad3-4ec7-828d-84c4970e98b3	user	user@example.com	$2b$12$Zay8j2GD9RY1CZvWSeHl3u0Zva6lhzQaBkVDxuF4C7eZ9nkxE5Uei	Just a user	UTC	2025-06-28 14:58:57.708064+00	2025-06-28 14:58:57.708064+00
\.


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (task_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: tasks tasks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

