-- creates the actual tables in postgreSQL

CREATE TABLE lab_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image VARCHAR(255) NOT NULL,  -- so Kubernetes can pull the correct Docker image
    port INTEGER NOT NULL,
    description TEXT
);

CREATE TABLE lab_sessions (
    id SERIAL PRIMARY KEY,
    lab_type_id INTEGER REFERENCES lab_types(id) NOT NULL,
    pod_name VARCHAR(255),
    url VARCHAR(255),  -- URL to access the lab environment
    status VARCHAR(50) CHECK (status IN ('running', 'stopped', 'expired')) DEFAULT 'running',
    start_time TIMESTAMP DEFAULT NOW(),
    expiration_time TIMESTAMP  -- tells cleanup worker when to delete labs
);

-- Enforces only one running lab at a time at the database level.
-- A partial unique index only indexes rows where status = 'running',
-- so the uniqueness constraint applies only to that subset.
CREATE UNIQUE INDEX one_running_lab ON lab_sessions (status) WHERE status = 'running';

-- Maybe add USER table for authentication and authorization later
