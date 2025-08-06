"""
Neo4j database connection test script.

This utility script tests the connection to the Neo4j database and verifies:
1. Basic connectivity using the neo4j Python driver
2. Authentication with provided credentials
3. APOC (Awesome Procedures on Cypher) plugin availability

The script is useful for:
- Debugging database connection issues
- Verifying Neo4j setup before running the main application
- Checking if required APOC procedures are installed

Environment variables used:
- NEO4J_URI: Database connection string (default: bolt://localhost:7687)
- NEO4J_USERNAME: Database username (default: neo4j)
- NEO4J_PASSWORD: Database password (default: Ayush@321)
"""

# test_neo4j.py
import os
from neo4j import GraphDatabase

# Make sure these match your docker-compose.yml and .env file
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "Ayush@321") # Use the password from your docker-compose file

try:
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        print(f"✅ Successfully connected to Neo4j at {URI}")
        result = session.run("SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'apoc' RETURN count(*) as apoc_count")
        count = result.single()["apoc_count"]
        if count > 0:
            print(f"✅ Success! Found {count} APOC procedures.")
        else:
            print(f"❌ Failure! Connected to the database, but it has no APOC procedures installed.")
    driver.close()
except Exception as e:
    print(f"🚨 Connection failed: {e}")