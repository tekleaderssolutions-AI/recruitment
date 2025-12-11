#!/bin/bash
# Render startup script

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -c "import migrations; migrations.init_db()"

# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port $PORT
