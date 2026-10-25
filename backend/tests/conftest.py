import os

# Tests must never send traces to Langfuse, even when the repo .env has keys.
# Set before any rewardlab import: load_dotenv() does not override existing vars.
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
os.environ["LANGFUSE_SECRET_KEY"] = ""
os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
