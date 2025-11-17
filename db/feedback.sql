-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users (id),
    content TEXT NOT NULL,
    category VARCHAR,
    email_sent BOOLEAN NOT NULL DEFAULT FALSE,
    email VARCHAR NOT NULL DEFAULT ''
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_feedback_user_id ON feedback (user_id);

-- Create index on created_at for chronological queries
CREATE INDEX idx_feedback_created_at ON feedback (created_at);