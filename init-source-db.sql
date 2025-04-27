-- Create the database if it doesn't exist (Docker entrypoint usually handles this, but good practice)
CREATE DATABASE IF NOT EXISTS sourcedb;

-- Switch to the target database
USE sourcedb;

-- Drop the table if it exists (optional, useful for testing/re-running)
DROP TABLE IF EXISTS users;

-- Create the users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some fake data
INSERT INTO users (name, email) VALUES
('Alice Wonderland', 'alice@example.com'),
('Bob The Builder', 'bob@example.com'),
('Charlie Chaplin', 'charlie@example.com'),
('Diana Prince', 'diana@example.com'),
('Ethan Hunt', 'ethan@example.com');

-- Grant privileges to the user defined in .env (sourceuser)
-- This user is created by the docker-entrypoint
GRANT ALL PRIVILEGES ON sourcedb.* TO 'sourceuser'@'%';
FLUSH PRIVILEGES;
