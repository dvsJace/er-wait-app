# app/__init__.py
import logging
import sys

# 1. Create the base 'app' logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# 2. Only add the handler if it doesn't already have one (prevents double logs)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(levelname)s:     %(name)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 3. Allow logs to bubble up to Uvicorn if you want, 
# or set to False to keep them separate
logger.propagate = True