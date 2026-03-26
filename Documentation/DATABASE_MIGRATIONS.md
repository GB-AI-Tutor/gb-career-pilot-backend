# Database Migrations with Alembic

This project uses Supabase (PostgreSQL) for database management. You can optionally use Alembic for database migrations and version control.

## Setup Alembic (Optional)

If you want to version control your database schema changes:

```bash
# 1. Install Alembic
pip install alembic

# 2. Initialize Alembic in your project
alembic init migrations

# 3. Configure alembic.ini with your database URL
# Edit the sqlalchemy.url line:
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/gb_career_db

# 4. Create your first migration
alembic revision --autogenerate -m "Initial migration"

# 5. Apply migrations
alembic upgrade head
```

## Using Supabase Migrations (Recommended)

Supabase has built-in migration support. Create migration files in `/supabase/migrations/`:

```bash
# Create migration directory
mkdir -p supabase/migrations

# Create migration file (timestamp_description.sql format)
# Example: supabase/migrations/20260322_create_users_table.sql
```

### Migration File Example:

```sql
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

## Current Database Schema

The GB Career Pilot database includes these tables:

1. **users** - Student accounts
2. **universities** - University information
3. **programs** - Degree programs
4. **admission_requirements** - Eligibility criteria
5. **conversations** - Chat history
6. **messages** - Individual chat messages
7. **user_favorite_universities** - Bookmarks

## Best Practices

1. **Always backup before migrations** - Use Supabase backup feature
2. **Test migrations locally first** - Use a local PostgreSQL instance
3. **Version control migration files** - Commit them to git
4. **Document breaking changes** - Add comments in migration files
5. **Use transactions** - Wrap DDL statements in BEGIN/COMMIT blocks

## Rollback Strategy

```sql
-- Example rollback migration
-- supabase/migrations/20260322_rollback_users_table.sql

DROP TABLE IF EXISTS users CASCADE;
```

## Notes

- Supabase manages database schema through their dashboard
- Alembic is optional and mainly useful for complex migration logic
- For simple schema changes, use Supabase SQL Editor
- Always test migrations in a staging environment first
