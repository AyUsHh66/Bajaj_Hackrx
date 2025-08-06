"""
Document processing service for parsing and ingesting documents into Neo4j.

This service handles the complete document processing pipeline:
1. Document Parsing: Uses LlamaParse to extract text from PDFs and other formats
2. Text Chunking: Creates hierarchical parent-child chunks for better retrieval
3. Graph Extraction: Uses LLM to extract entities and relationships from text
4. Neo4j Ingestion: Stores chunks as vectors and graphs in Neo4j database

Key Components:
- DocumentProcessor: Main class orchestrating the entire pipeline
- Pydantic Models: Node, Relationship, Graph for structured LLM output
- Hierarchical Chunking: Parent chunks (1024 chars) with child chunks (400 chars)
- Graph Entity Extraction: Batch processing to identify entities and relationships
- Multi-modal Support: Can handle images and complex document structures

The service uses:
- LlamaParse for document parsing
- Ollama for local LLM inference
- HuggingFace embeddings for vector representations
- Neo4j for storage and retrieval
"""

# processing_service.py

import os
import base64
import json
from io import BytesIO
from PIL import Image
from typing import List, Dict, Tuple

from llama_parse import LlamaParse
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Neo4jVector
from langchain_community.graphs.graph_document import (
    Node as LangchainNode,
    Relationship as LangchainRelationship,
    GraphDocument,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from config import settings
from database import graph

# --- Pydantic Models for Structured Output ---
class Node(BaseModel):
    id: str
    type: str

class Relationship(BaseModel):
    source: Node
    target: Node
    type: str

class Graph(BaseModel):
    nodes: List[Node]
    relationships: List[Relationship]

# --------------------------------------------------------------------

class DocumentProcessor:
    def __init__(self, file_path: str, file_name: str):
        self.file_path = file_path
        self.file_name = file_name
        self.llm = ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL, format="json")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

    def process(self) -> Dict:
        try:
            print(f"Starting processing for: {self.file_name}")
            parsed_json = self._parse_document()
            parent_chunks, child_chunks = self._create_chunks(parsed_json)
            graph_documents = self._extract_graph_entities(child_chunks)
            self._ingest_into_neo4j(parent_chunks, child_chunks, graph_documents)
            print(f"Successfully processed and ingested: {self.file_name}")
            
            total_nodes = sum(len(doc.nodes) for doc in graph_documents)
            total_relationships = sum(len(doc.relationships) for doc in graph_documents)

            return {
                "filename": self.file_name,
                "total_parent_chunks": len(parent_chunks),
                "total_child_chunks": len(child_chunks),
                "total_graph_nodes": total_nodes,
                "total_graph_relationships": total_relationships,
            }
        except Exception as e:
            print(f"Task failed for file {self.file_name}: {e}")
            raise

    def _parse_document(self) -> List[Dict]:
        print("Parsing document with LlamaParse...")
        parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY, result_type="markdown", verbose=True
        )
        return parser.get_json_result(self.file_path)

    def _create_chunks(self, parsed_json: List[Dict]) -> Tuple[List[Document], List[Document]]:
        print("Creating hierarchical chunks...")
        pages_data = parsed_json[0]["pages"]
        full_text = "\n\n".join([page['md'] for page in pages_data])
        
        parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
        parent_docs = parent_splitter.create_documents([full_text], metadatas=[{"source": self.file_name}])
        
        child_docs: List[Document] = []
        for i, doc in enumerate(parent_docs):
            _id = f"parent_{i}"
            child_docs_for_parent = child_splitter.split_documents([doc])
            for child_doc in child_docs_for_parent:
                child_doc.metadata["parent_id"] = _id
                child_doc.metadata["source"] = self.file_name
            child_docs.extend(child_docs_for_parent)
            doc.metadata["id"] = _id
        return parent_docs, child_docs

    def _extract_graph_entities(self, chunks: List[Document]) -> List[GraphDocument]:
        print("Extracting graph entities with JSON parser...")
        
        parser = JsonOutputParser(pydantic_object=Graph)
        prompt = ChatPromptTemplate.from_template(
            "Extract a knowledge graph from the text. "
            "Focus on identifying clear entities and their relationships. "
            "Format the output as a JSON object with 'nodes' and 'relationships' keys, "
            "following these instructions: {format_instructions}\n"
            "Text: {input}"
        )
        extractor = prompt | self.llm | parser

        all_nodes = []
        all_relationships = []
        for i in range(0, len(chunks), 5):
            batch_chunks = chunks[i:i+5]
            batch_text = "\n\n".join([chunk.page_content for chunk in batch_chunks])
            
            print(f"  - Processing batch {i//5 + 1}...")
            try:
                graph_data = extractor.invoke({"input": batch_text, "format_instructions": parser.get_format_instructions()})
                all_nodes.extend(graph_data.get('nodes', []))
                all_relationships.extend(graph_data.get('relationships', []))
            except Exception as e:
                print(f"  - Error processing batch {i//5 + 1}: {e}")
                continue 
        
        unique_nodes_set = set()
        for node in all_nodes:
            if isinstance(node, dict) and node.get('id'):
                node_type = node.get('type') or 'Unknown'
                unique_nodes_set.add((node.get('id'), node_type))

        nodes = [LangchainNode(id=id, type=type) for id, type in unique_nodes_set if id is not None]

        relationships = []
        for rel in all_relationships:
            if not isinstance(rel, dict): continue
            
            source_node_data = rel.get('source')
            target_node_data = rel.get('target')

            if not isinstance(source_node_data, dict) or not isinstance(target_node_data, dict): continue

            source_id = source_node_data.get('id')
            target_id = target_node_data.get('id')
            rel_type = rel.get('type')

            if not source_id or not target_id or not rel_type:
                continue
            
            # --- FINAL FIX: Provide a default for the node 'type' if it's missing or None ---
            source_type = source_node_data.get('type') or 'Unknown'
            target_type = target_node_data.get('type') or 'Unknown'
            
            source = LangchainNode(id=source_id, type=source_type)
            target = LangchainNode(id=target_id, type=target_type)
            # ------------------------------------------------------------------------------
            
            relationships.append(
                LangchainRelationship(source=source, target=target, type=rel_type)
            )
        
        return [GraphDocument(nodes=nodes, relationships=relationships, source=chunks[0])]

    def _ingest_into_neo4j(self, parent_chunks: List[Document], child_chunks: List[Document], graph_documents: List[GraphDocument]):
        print("Ingesting data into Neo4j...")
        Neo4jVector.from_documents(
            documents=parent_chunks,
            embedding=self.embeddings,
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
            index_name="parent_chunks",
            node_label="ParentChunk"
        )
        for chunk in child_chunks:
            graph.query(
                """
                MATCH (pc:ParentChunk {id: $parent_id})
                MERGE (c:ChildChunk {id: apoc.create.uuid(), text: $text})
                MERGE (c)-[:CHILD_OF]->(pc)
                """,
                params={"parent_id": chunk.metadata["parent_id"], "text": chunk.page_content}
            )
        graph.add_graph_documents(graph_documents)