"""
Policy Ingestion Service
Loads compliance policies from text file, chunks them, creates embeddings, and stores in Qdrant.
Uses HuggingFace embeddings (FREE - no API key needed!)
"""

import os
import re
import sys
from typing import List, Dict
from dotenv import load_dotenv
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()


class PolicyIngestor:
    """Handles ingestion of compliance policies into vector database"""
    
    def __init__(
        self,
        policies_path: str = "data/policies.txt",
        qdrant_url: str = None,
        qdrant_path: str = None,
        collection_name: str = None,
        embedding_model: str = None
    ):
        """
        Initialize the policy ingestor
        
        Args:
            policies_path: Path to the policies text file
            qdrant_url: URL for Qdrant instance
            collection_name: Name of the Qdrant collection
            embedding_model: HuggingFace embedding model name
        """
        self.policies_path = policies_path
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_path = qdrant_path or os.getenv("QDRANT_PATH")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "compliance_policies")
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        
        # Initialize HuggingFace embeddings (FREE - no API key needed!)
        print("[*] Loading HuggingFace embedding model (first time may take a minute)...")
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.embedding_model
        )
        print("[OK] Embedding model loaded")
        
        # Set global settings for LlamaIndex
        Settings.embed_model = self.embed_model
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize Qdrant client (local path or remote URL)
        if self.qdrant_path:
            self.qdrant_client = QdrantClient(path=self.qdrant_path)
        else:
            self.qdrant_client = QdrantClient(url=self.qdrant_url)
        
    def load_policies(self) -> str:
        """Load policies from text file"""
        if not os.path.exists(self.policies_path):
            raise FileNotFoundError(f"Policies file not found: {self.policies_path}")
        
        with open(self.policies_path, 'r', encoding='utf-8') as f:
            policies_text = f.read()
        
        print(f"[OK] Loaded policies from {self.policies_path}")
        print(f"  Total characters: {len(policies_text)}")
        return policies_text
    
    def parse_policies(self, policies_text: str) -> List[Document]:
        """
        Parse policies text into structured documents
        Each policy section becomes a separate document
        """
        # Identify policy blocks by title line to keep title + body together
        policy_pattern = re.compile(r"^POLICY\s+\d+:\s+(.+)$", re.MULTILINE)
        matches = list(policy_pattern.finditer(policies_text))
        documents = []

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(policies_text)
            section = policies_text[start:end].strip()

            if "Policy ID:" not in section:
                continue
            
            # Extract policy metadata - IMPROVED PARSING
            lines = section.split('\n')
            policy_id = None
            category = None
            title = match.group(1).strip() if match.group(1) else None
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Extract title - look for "POLICY X: TITLE" format
                if line.startswith("POLICY") and ":" in line:
                    # Extract everything after the colon
                    title = line.split(":", 1)[1].strip()
                
                # Extract Policy ID
                if "Policy ID:" in line:
                    policy_id = line.split("Policy ID:")[1].strip()
                
                # Extract Category
                if "Category:" in line:
                    category = line.split("Category:")[1].strip()
                
                # Stop after finding header info (usually in first 15 lines)
                if i > 15:
                    break
            
            # Create document with metadata
            doc = Document(
                text=section,
                metadata={
                    "policy_id": policy_id if policy_id else "UNKNOWN",
                    "category": category if category else "General",
                    "title": title if title else "Untitled Policy",
                    "source": "company_policies"
                }
            )
            documents.append(doc)
        
        print(f"[OK] Parsed {len(documents)} policy documents")
        
        # Debug: Show first 3 policies parsed
        print("\nSample parsed policies:")
        for i, doc in enumerate(documents[:3], 1):
            print(f"  {i}. {doc.metadata['policy_id']}: {doc.metadata['title']}")
        
        return documents
    
    def create_collection(self, vector_size: int = 384):
        """Create Qdrant collection if it doesn't exist (384 for bge-small-en-v1.5)"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                print(f"[WARN] Collection '{self.collection_name}' already exists")
                recreate = os.getenv("QDRANT_RECREATE", "").lower() in ("1", "true", "yes")
                if recreate:
                    self.qdrant_client.delete_collection(self.collection_name)
                    print(f"[OK] Deleted existing collection")
                elif sys.stdin.isatty():
                    response = input("Delete and recreate? (y/n): ")
                    if response.lower() == 'y':
                        self.qdrant_client.delete_collection(self.collection_name)
                        print(f"[OK] Deleted existing collection")
                    else:
                        print("[OK] Using existing collection")
                        return
                else:
                    print("[OK] Using existing collection (set QDRANT_RECREATE=true to rebuild)")
                    return
            
            # Create new collection
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"[OK] Created collection '{self.collection_name}'")
            
        except Exception as e:
            print(f"[ERROR] Error creating collection: {e}")
            raise
    
    def ingest_to_qdrant(self, documents: List[Document]) -> VectorStoreIndex:
        """
        Ingest documents into Qdrant vector store
        
        Args:
            documents: List of Document objects to ingest
            
        Returns:
            VectorStoreIndex for querying
        """
        try:
            # Create collection
            self.create_collection()
            
            # Initialize Qdrant vector store
            vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=self.collection_name
            )
            
            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            # Create index and ingest documents
            print("[*] Creating embeddings and ingesting into Qdrant...")
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                show_progress=True
            )
            
            print(f"[OK] Successfully ingested {len(documents)} documents into Qdrant")
            return index
            
        except Exception as e:
            print(f"[ERROR] Error during ingestion: {e}")
            raise
    
    def run_ingestion(self) -> VectorStoreIndex:
        """
        Main ingestion pipeline
        
        Returns:
            VectorStoreIndex for querying
        """
        print("\n" + "=" * 60)
        print("COMPLYFLOW AI - POLICY INGESTION PIPELINE")
        print("=" * 60 + "\n")
        
        # Step 1: Load policies
        print("[1/3] Loading policies...")
        policies_text = self.load_policies()
        
        # Step 2: Parse into documents
        print("\n[2/3] Parsing policies...")
        documents = self.parse_policies(policies_text)
        
        # Step 3: Ingest to Qdrant
        print("\n[3/3] Ingesting to Qdrant...")
        index = self.ingest_to_qdrant(documents)
        
        print("\n" + "=" * 60)
        print("[OK] INGESTION COMPLETE!")
        print("=" * 60 + "\n")
        
        return index


def main():
    """Run the ingestion pipeline"""
    ingestor = PolicyIngestor()
    index = ingestor.run_ingestion()
    
    print("[OK] Policy database ready for retrieval!")
    print("  Run: python services/retrieval.py to test")


if __name__ == "__main__":
    main()
