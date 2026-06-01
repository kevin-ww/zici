import multiprocessing

# Use Uvicorn workers — required for FastAPI (ASGI), not standard WSGI workers
worker_class = "uvicorn.workers.UvicornWorker"

# Rule of thumb: 2 × CPU cores + 1
# Overridden by the WEB_CONCURRENCY env var on Render/Railway/Heroku
workers = int(__import__("os").environ.get("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))

# Bind to PORT env var (set by Render/Railway) or default to 8000
bind = f"0.0.0.0:{__import__('os').environ.get('PORT', '8000')}"

# Kill and restart a worker that hasn't responded in 30 seconds
timeout = 30

# Keep-alive connections for load balancers
keepalive = 5

# Graceful shutdown — finish in-flight requests before stopping
graceful_timeout = 10

# Log to stdout so platform log aggregators pick it up
accesslog = "-"
errorlog = "-"
loglevel = "info"
