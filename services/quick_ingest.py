import sys
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()

print("Loading model...", flush=True)
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.embed_model = embed_model

print("Connecting to Qdrant with longer timeout...", flush=True)
client = QdrantClient(url="http://localhost:6333", timeout=120)  # 2 minute timeout

print("Loading policies...", flush=True)
with open("data/policies.txt") as f:
    text = f.read()

sections = [s.strip() for s in text.split("=" * 80) if s.strip() and "END OF" not in s]
docs = [Document(text=s, metadata={"source": "policies"}) for s in sections]
print(f"Got {len(docs)} documents", flush=True)

# Check if collection exists
try:
    collections = client.get_collections()
    if "compliance_policies" in [c.name for c in collections.collections]:
        print("Collection already exists, using it...", flush=True)
    else:
        print("Creating new collection (may take 30 seconds)...", flush=True)
        client.create_collection(
            collection_name="compliance_policies",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print("✓ Collection created", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
    sys.exit(1)

print("Ingesting (this takes 2-3 minutes)...", flush=True)
vector_store = QdrantVectorStore(client=client, collection_name="compliance_policies")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(docs, storage_context=storage_context, show_progress=True)

print("\n✓ DONE! Test with: python services/retrieval.py")
