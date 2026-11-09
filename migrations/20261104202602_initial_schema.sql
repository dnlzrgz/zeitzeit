-- updated_at is maintained by the database.
CREATE FUNCTION set_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- Users
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    email text UNIQUE NOT NULL CHECK (
        email <> '' AND email = lower(btrim(email)) AND length(email) <= 254
    ),
    display_name text NOT NULL CHECK (length(btrim(display_name)) BETWEEN 1 AND 254),
    password_hash text NOT NULL, -- argon2id PHC string
    timezone text NOT NULL DEFAULT 'UTC', -- IANA name
    week_start smallint NOT NULL DEFAULT 1 CHECK (week_start BETWEEN 0 AND 6), -- 0 = Sunday
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Auth tokens (web sessions & personal API tokens)
CREATE TABLE auth_tokens (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind text NOT NULL CHECK (kind IN ('session', 'api')),
    name text NOT NULL CHECK (length(btrim(name)) > 0), -- "laptop", "agent", etc
    token_hash bytea NOT NULL UNIQUE, -- SHA-256 of the random token
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    expires_at   timestamptz, -- NULL = never
    revoked_at timestamptz,
    CHECK (expires_at IS NULL OR expires_at > created_at)
);

-- Projects
CREATE TABLE projects (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name text NOT NULL CHECK (length(name) BETWEEN 1 AND 200 AND name = btrim(name)),
    archived_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, user_id)
);

CREATE UNIQUE INDEX projects_user_name_uq ON projects(user_id, lower(name));

-- Tags
CREATE TABLE tags (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name text NOT NULL CHECK (length(name) BETWEEN 1 AND 100 AND name = btrim(name)),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, user_id)
);

CREATE UNIQUE INDEX tags_user_name_uq ON tags(user_id, lower(name));

-- Time entries
CREATE TABLE time_entries (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id uuid,
    description text NOT NULL DEFAULT '',
    started_at timestamptz NOT NULL,
    stopped_at timestamptz, -- NULL = running
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, user_id), -- FK target for time_entry_tags

    -- Overlapping entries are allowed on purpose.
    CHECK (stopped_at IS NULL OR stopped_at > started_at),

    -- Project must belong to the same user.
    FOREIGN KEY (project_id, user_id) REFERENCES projects(id, user_id) ON DELETE SET NULL (project_id)
);

CREATE INDEX time_entries_user_started_idx ON time_entries(user_id, started_at);

-- ONE running timer per user, enforced in the database.
CREATE UNIQUE INDEX one_running_timer_per_user ON time_entries(user_id) WHERE stopped_at IS NULL;

-- Entries + Tags
CREATE TABLE time_entry_tags (
    time_entry_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    user_id uuid NOT NULL,
    PRIMARY KEY (time_entry_id, tag_id),

    FOREIGN KEY (time_entry_id, user_id) REFERENCES time_entries(id, user_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id, user_id) REFERENCES tags(id, user_id) ON DELETE CASCADE
);

-- updated_at triggers
CREATE TRIGGER users_set_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER auth_tokens_set_updated_at BEFORE UPDATE ON auth_tokens
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER projects_set_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER tags_set_updated_at BEFORE UPDATE ON tags
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER time_entries_set_updated_at BEFORE UPDATE ON time_entries
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
