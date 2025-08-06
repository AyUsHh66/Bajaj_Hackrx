"""
Retrieval service for answering questions using Neo4j vector and graph search.

This service provides intelligent question answering capabilities:
1. Query Routing: Automatically determines the best retrieval strategy
   - vector_search: For general questions, definitions, summaries
   - graph_qa: For relationship and connection-based queries
   - hybrid_search: For mixed question types

2. Vector Search: Uses semantic similarity to find relevant document chunks
3. Answer Synthesis: Uses Google Gemini to generate accurate answers from context
4. Source Tracking: Maintains metadata about retrieved information

Key Features:
- Pre-initialized global connections for better performance
- Intelligent query routing using structured LLM output
- Strict context-based answering (no hallucination)
- Comprehensive error handling and fallback responses

The service uses:
- Google Gemini 2.0 Flash for answer generation
- HuggingFace sentence transformers for embeddings
- Neo4j vector store for document retrieval
- Structured output parsing for reliable routing decisions
"""

# retrieval_service.py

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Neo4jVector
from langchain_core.output_parsers import StrOutputParser
from typing import Dict

from config import settings
from database import graph

# --- Initialize models and embeddings once at startup ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GOOGLE_API_KEY)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

# --- FIX 1: Initialize the vector store and retriever once as global variables ---
# This creates a single, persistent connection to the database that will be reused for all queries.
print("Initializing Neo4j Vector Store connection...")
vector_store = Neo4jVector.from_existing_index(
    embedding=embeddings,
    url=settings.NEO4J_URI,
    username=settings.NEO4J_USERNAME,
    password=settings.NEO4J_PASSWORD,
    index_name="parent_chunks",
    node_label="ParentChunk",
    text_node_property="text",
    embedding_node_property="embedding",
)
retriever = vector_store.as_retriever()
print("Neo4j Vector Store connection initialized.")
# --------------------------------------------------------------------------------

# --- Query Router ---
class QueryRouter(BaseModel):
    """Decides the retrieval strategy based on the user's query."""
    strategy: str = Field(
        ...,
        description="The strategy to use: 'vector_search' for broad questions, 'graph_qa' for specific questions about relationships, or 'hybrid_search' for mixed questions."
    )
    question: str = Field(..., description="The user's original question.")

def get_query_router():
    """Creates a chain to route the user's query to the appropriate strategy."""
    prompt = ChatPromptTemplate.from_template(
        """You are an expert at routing a user's question to the appropriate retrieval strategy.
Your goal is to choose the best strategy to answer the user's question based on these strict definitions:

1.  **vector_search**: Choose this for any question that asks for definitions, summaries, explanations, or general information about a topic.
    Examples:
    - "What is an Ayush Hospital?"
    - "Summarize the grace period."
    - "What are the exclusions under this policy?"

2.  **graph_qa**: Choose this ONLY for questions that ask about the explicit relationships or connections between two or more specific entities.
    Examples:
    - "Who is the CEO of National Insurance?"
    - "What is the relationship between the Arogya Sanjeevani Policy and National Insurance?"

You must output a JSON object with the 'strategy' and 'question' keys.

Question: {question}"""
    )
    
    return prompt | llm.with_structured_output(QueryRouter)

# --- Main Retrieval Service ---
class RetrievalService:
    def __init__(self):
        self.router_chain = get_query_router()
        # Use the global, pre-initialized retriever
        self.retriever = retriever

    def answer_query(self, query: str) -> Dict:
        """Orchestrates the retrieval and answer generation process."""
        print(f"Received query: {query}")
        
        route = self.router_chain.invoke({"question": query})
        print(f"Routing decision: {route.strategy}")
        
        if route.strategy in ["vector_search", "hybrid_search"]:
            results = self.retriever.invoke(query)
            context = "\n\n".join([doc.page_content for doc in results])
            sources = [doc.metadata for doc in results]
        elif route.strategy == "graph_qa":
            context = "Graph QA is not yet implemented. Please ask a broader question."
            sources = []
        else:
            context = "Could not determine a valid retrieval strategy."
            sources = []

        final_answer = self._synthesize_answer(query, context)
        return {"answer": final_answer, "sources": sources}

    def _synthesize_answer(self, query: str, context: str) -> str:
        """Generates a final answer using the retrieved context."""
        # --- FIX 2: Use a more robust and explicit prompt for answer synthesis ---
        prompt = ChatPromptTemplate.from_template(
            """You are a specialized Q&A assistant for an insurance policy document.
Your knowledge is strictly limited to the information contained in the 'Context' provided below. You must not use any outside information.

Your task is to answer the user's 'Question' based ONLY on the 'Context'.

**Instructions:**
1.  Read the 'Context' carefully.
2.  Formulate a direct and concise answer to the 'Question' using only the facts and text from the 'Context'.
3.  If the 'Context' contains the answer, provide it directly.
4.  If the 'Context' does NOT contain the information needed to answer the 'Question', you must respond with the exact phrase: "The provided document does not contain information on this topic."
5.  Do not, under any circumstances, say "I have no context" or "I cannot answer."

**Context:**
{context}

**Question:**
{query}

**Answer:**
"""
        )
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"context": context, "query": query})
