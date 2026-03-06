

-- Create the function that maps the metadata to your public.users table
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  -- Check if email was just confirmed AND user isn't already in our public table
  IF (OLD.email_confirmed_at IS NULL AND NEW.email_confirmed_at IS NOT NULL) THEN
    IF NOT EXISTS (SELECT 1 FROM public.users WHERE id = NEW.id) THEN
      insert into public.users (
        id, email, full_name, phone, fsc_percentage, city, field_of_interest
      )
      values (
        new.id,
        new.email,
        new.raw_user_meta_data ->> 'full_name',
        new.raw_user_meta_data ->> 'phone',
        (new.raw_user_meta_data ->> 'fsc_percentage')::numeric,
        new.raw_user_meta_data ->> 'city',
        new.raw_user_meta_data ->> 'field_of_interest'
      );
    END IF;
  END IF;
  return new;
end;
$$;

--  Attach the trigger to the auth.users table
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after UPDATE on auth.users
  for each row execute procedure public.handle_new_user();
