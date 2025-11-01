# Secure Login System with JWT

**Short description:**  
> This project is a secure authentication system built with Python and Flask. It features **JWT-based authentication**, user registration, login, and optional multi-factor authentication (MFA). The system demonstrates best practices for backend security and token management.

---

## 🚀 Features

- User registration with password hashing
- Users can change their username, email, and password securely
- Secure login with JWT authentication
- Token expiration and refresh handling
- Optional multi-factor authentication (MFA)
- Protected routes for authenticated users

---

## 🛠️ Tech Stack

**Frontend:**  
- HTML  
- CSS  
- JavaScript  

**Backend:**  
- Python  
- Flask  

**Database / Storage:**  
- MySQL  
- Redis  

---

## ⚙️ Installation & Setup

### 1️⃣ Setup Repository

git clone https://github.com/Code613x/login-example.git
cd login-example/web
pip install -r requirements.txt

### 2️⃣ Set up Redis

You can either:

1. **Run Redis using Docker**:

```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

2. **Or install Redis locally**:

* Windows: use [Redis for Windows](https://github.com/tporadowski/redis/releases)
* Linux/macOS: `sudo apt install redis-server` or `brew install redis`

Make sure Redis is running on the default port `6379`.

### 3️⃣ Set up MySQL

1. Install MySQL locally or via Docker.
2. Create a new database for the project.
3. Run the `schema.sql` file in the main directory to create the necessary tables.

### 4️⃣ Configure Environment Variables

Create a `.env` file in the project root with these variables:

```
SECRET_KEY=<your-secret-key>
JWT_SECRET_KEY=<your-jwt-secret>
DATABASE_URL=mysql+pymysql://<user>:<password>@localhost/<database_name>
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 5️⃣ Run the Backend

```bash
python app.py
```

The backend will start at `http://localhost:5000`.

```
```
