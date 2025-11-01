CREATE TABLE user_auth (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    user_role VARCHAR(255) DEFAULT 'free_user',
    mfa_secret VARCHAR(255),
    mfa_enabled BOOLEAN DEFAULT FALSE
);

CREATE TABLE refresh_tokens (
    token_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_auth(user_id) ON DELETE CASCADE
);

CREATE TABLE roles (
    role_index INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    role_permission JSON NOT NULL
);

