# retrieval_service.py

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_community.vectorstores import Neo4jVector
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from typing import Dict

from config import settings
from database import graph

# --- FIX: Tell the ChatOllama model to expect JSON output ---
llm = ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL, format="json")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

# --- Query Router (Pydantic V2 Model) ---
class QueryRouter(BaseModel):
    """Decides the retrieval strategy based on the user's query."""
    strategy: str = Field(
        ...,
        description="The strategy to use: 'vector_search', 'graph_qa', or 'hybrid_search'."
    )
    question: str = Field(..., description="The user's original question.")

def get_query_router():
    # --- FIX: Use the more reliable JsonOutputParser ---
    parser = JsonOutputParser(pydantic_object=QueryRouter)
    
    prompt = ChatPromptTemplate.from_template(
        "You are an expert at routing a user's question to the appropriate retrieval strategy. "
        "Based on the user's question, decide whether to use 'vector_search' for broad questions, "
        "'graph_qa' for specific questions about relationships, or 'hybrid_search' for mixed questions. "
        "Format the output as a JSON object with 'strategy' and 'question' keys. "
        "These are the format instructions: {format_instructions}\n"
        "Question: {question}"
    )
    
    return prompt | llm | parser

# --- Main Retrieval Service ---
class RetrievalService:
    def __init__(self):
        self.router_chain = get_query_router()
        self.parser = JsonOutputParser(pydantic_object=QueryRouter)
        self.vector_store = Neo4jVector.from_existing_index(
            embedding=embeddings,
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
            index_name="parent_chunks",
            node_label="ParentChunk",
            text_node_property="text",
            embedding_node_property="embedding",
        )
        self.retriever = self.vector_store.as_retriever()

    def answer_query(self, query: str) -> Dict:
        """Orchestrates the retrieval and answer generation process."""
        print(f"Received query: {query}")
        
        # --- FIX: Pass the format instructions to the router chain ---
        route_data = self.router_chain.invoke({
            "question": query,
            "format_instructions": self.parser.get_format_instructions()
        })
        route = QueryRouter(**route_data)
        
        print(f"Routing decision: {route.strategy}")
        
        results = self.retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in results])
        
        final_answer = self._synthesize_answer(query, context)
        return {"answer": final_answer, "sources": [doc.metadata for doc in results]}

    def _synthesize_answer(self, query: str, context: str) -> str:
        """Generates a final answer using the retrieved context."""
        prompt = ChatPromptTemplate.from_template(
            """Answer the question based only on the context provided.
            Context: {context}
            Question: {query}"""
        )
        # Use a non-JSON llm instance for the final answer
        synthesis_llm = ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL)
        chain = prompt | synthesis_llm | StrOutputParser()
        return chain.invoke({"context": context, "query": query})