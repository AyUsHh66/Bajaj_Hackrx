# database.py

# 1. Make sure you have run this command in your terminal:
# pip install -U langchain-neo4j
# database.py
from langchain_neo4j import Neo4jGraph
from config import settings

# --- DEBUGGING PRINT STATEMENTS ---
# This will show us the exact credentials being used by Celery
print("--- DATABASE CONNECTION ATTEMPT ---")
print(f"Attempting to connect with:")
print(f"  URI: {settings.NEO4J_URI}")
print(f"  USER: {settings.NEO4J_USERNAME}")
print("-----------------------------------")
# --- END DEBUGGING ---

# Your existing code
graph = Neo4jGraph(
    url=settings.NEO4J_URI,
    username=settings.NEO4J_USERNAME,
    password=settings.NEO4J_PASSWORD
)