# Task Queue Example

A Flask application demonstrating asynchronous task processing using Celery and Redis, featuring a modern web interface for task management.

## Features

- Asynchronous addition of numbers with a 10-second delay
- Real-time task status updates
- Task history with visual status indicators
- Task management (submit, monitor, delete)
- Task queue statistics
- Task deletion with full cleanup (history and queue)
- Docker support with health checks

## Tech Stack

- Frontend: HTML5, CSS3, JavaScript
- Backend: Flask, Celery
- Queue/Storage: Redis
- Container: Docker

## Quick Start with Docker

1. Clone the repository

2. Start all services:
```bash
docker compose up --build
```

3. Access the web interface at http://localhost:5001

## Manual Setup

### Prerequisites
- Python 3.9+
- Redis Server
- Virtual Environment (recommended)

### Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start Redis server (if not running)
4. Run Celery worker:
```bash
celery -A tasks worker --loglevel=info
```

5. Start Flask application:
```bash
python app.py
```

6. Access the web interface at http://localhost:5001