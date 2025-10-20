@echo off
docker run -d --name redis -p 6379:6379 redis:latest
pip install -r requirements.txt