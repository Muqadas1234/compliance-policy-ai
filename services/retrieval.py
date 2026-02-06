"""
Policy Retrieval Service
Retrieves relevant compliance policies from Qdrant based on document text.
Uses HuggingFace embeddings (FREE - no API key needed!)
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()


class PolicyRetriever:
    """Handles retrieval of relevant policies from vector database"""
    
    def __init__(
        self,
        qdrant_url: str = None,
        qdrant_path: str = None,
        collection_name: str = None,
        embedding_model: str = None
    ):
        """
        Initialize the policy retriever
        
        Args:
            qdrant_url: URL for Qdrant instance
            collection_name: Name of the Qdrant collection
            embedding_model: HuggingFace embedding model name
        """
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_path = qdrant_path or os.getenv("QDRANT_PATH")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "compliance_policies")
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        
        # Initialize HuggingFace embeddings (FREE - no API key needed!)
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.embedding_model
        )
        
        # Set global settings
        Settings.embed_model = self.embed_model
        
        # Initialize Qdrant client (local path or remote URL)
        if self.qdrant_path:
            self.qdrant_client = QdrantClient(path=self.qdrant_path)
        else:
            self.qdrant_client = QdrantClient(url=self.qdrant_url)
        
        # Initialize index
        self.index = self._load_index()
    
    def _load_index(self) -> VectorStoreIndex:
        """Load existing index from Qdrant"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                raise ValueError(
                    f"Collection '{self.collection_name}' not found. "
                    "Please run ingestion.py first to create the policy database."
                )
            
            # Initialize vector store
            vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=self.collection_name
            )
            
            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            # Load index
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context
            )
            
            print(f"[OK] Loaded policy index from collection '{self.collection_name}'")
            return index
            
        except Exception as e:
            print(f"[ERROR] Error loading index: {e}")
            raise
    
    def retrieve_policies(
        self,
        doc_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant policies for a given document text.
        This is the MAIN FUNCTION that Teammate 2 will use.
        
        Args:
            doc_text: The document text to analyze
            top_k: Number of top policies to retrieve (default: 5)
            similarity_threshold: Minimum similarity score (default: 0.5)
            
        Returns:
            List of dictionaries containing policy information
        """
        try:
            # Create retriever
            retriever = self.index.as_retriever(
                similarity_top_k=top_k
            )
            
            # Retrieve relevant nodes
            nodes = retriever.retrieve(doc_text)
            
            # Format results
            results = []
            for node in nodes:
                # Skip if score is below threshold
                if node.score < similarity_threshold:
                    continue
                
                result = {
                    'policy_id': node.metadata.get('policy_id', 'UNKNOWN'),
                    'category': node.metadata.get('category', 'General'),
                    'title': node.metadata.get('title', 'Untitled'),
                    'text': node.text,
                    'score': round(node.score, 3),
                    'metadata': node.metadata
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Error retrieving policies: {e}")
            raise
    
    def format_policies_for_agent(self, policies: List[Dict[str, Any]]) -> str:
        """Format retrieved policies into a readable string for AI agents"""
        if not policies:
            return "No relevant policies found."
        
        formatted = "RELEVANT COMPLIANCE POLICIES:\n\n"
        
        for i, policy in enumerate(policies, 1):
            formatted += f"--- Policy {i} ---\n"
            formatted += f"ID: {policy['policy_id']}\n"
            formatted += f"Category: {policy['category']}\n"
            formatted += f"Title: {policy['title']}\n"
            formatted += f"Relevance Score: {policy['score']}\n\n"
            formatted += f"{policy['text']}\n"
            formatted += "\n" + "="*60 + "\n\n"
        
        return formatted


# Main function for Teammate 2
def retrieve_policies(
    doc_text: str, top_k: int = 5, similarity_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Simple wrapper function for easy import by Teammate 2.
    
    Usage:
        from services.retrieval import retrieve_policies
        policies = retrieve_policies(document_text)
    """
    retriever = PolicyRetriever()
    return retriever.retrieve_policies(
        doc_text, top_k=top_k, similarity_threshold=similarity_threshold
    )


def test_retrieval():
    """Test the retrieval system"""
    print("\n" + "="*60)
    print("TESTING POLICY RETRIEVAL SYSTEM")
    print("="*60 + "\n")
    
    retriever = PolicyRetriever()
    
    # Test 1
    print("[Test 1] Expense Reimbursement Query")
    print("-" * 60)
    test_doc = "Employee submitted expense report for $3,500 including business class flight"
    
    policies = retriever.retrieve_policies(test_doc, top_k=3)
    print(f"\nFound {len(policies)} relevant policies:\n")
    
    for i, policy in enumerate(policies, 1):
        print(f"{i}. {policy['policy_id']}: {policy['title']}")
        print(f"   Category: {policy['category']}")
        print(f"   Relevance: {policy['score']}\n")
    
    print("="*60)
    print("[OK] RETRIEVAL TEST COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_retrieval()
