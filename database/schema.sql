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
    lab_type_id INTEGER REFERENCES lab_types(id),
    pod_name VARCHAR(255),
    url VARCHAR(255),  -- URL to access the lab environment
    status VARCHAR(50) DEFAULT 'running',
    start_time TIMESTAMP DEFAULT NOW(),
    expiration_time TIMESTAMP  -- tells cleanup worker when to delete labs
);

-- Maybe add USER table for authentication and authorization later