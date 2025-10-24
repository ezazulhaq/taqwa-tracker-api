
-- Audit logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR NOT NULL,
    email VARCHAR,
    ip_address VARCHAR,
    user_agent VARCHAR,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    details VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index on event_type for faster filtering
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
