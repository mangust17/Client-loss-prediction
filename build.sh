#!/bin/bash
cd frontend
npm install
npm run build
cd ../backend
pip install -r requirements.txt
gunicorn -b 0.0.0.0:$PORT wsgi:app
