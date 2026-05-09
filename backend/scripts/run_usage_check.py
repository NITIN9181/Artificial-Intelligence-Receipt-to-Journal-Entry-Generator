import asyncio
import sys
import os

# Add the project root to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tasks.usage_monitor import check_usage

if __name__ == "__main__":
    asyncio.run(check_usage())
