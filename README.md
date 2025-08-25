# Project Setup Guide

## 1) Create virtual environment and activate it
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate   # On Linux/Mac
```
## Copy .env.example and replace API key
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac

## 3) Install requirements
```bash
pip install -r requirements.txt
```

## 4) Download and run Redis (on port 6379)
Make sure Redis is installed and running:
```bash
redis-server
```

## 5) Add your own workflow to Runpod folder

## 6) Run the script
```bash
python bot.py
```
