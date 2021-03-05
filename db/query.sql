
create table public.user (
user_id int primary key,
user_name text,
post_count int,
follower_count int,
following_count int,
name text,
bio text,
website text,
profile_img text
);

create table public.post (
	id text primary key,
	time bigint,
	comment_count int,
	like_count int,
	thumbnail text,
	short_code text,
	is_video int default 0,
	user_id int references public.user(user_id)
);
