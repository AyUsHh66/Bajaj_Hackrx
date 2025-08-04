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