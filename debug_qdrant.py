import qdrant_client
from qdrant_client import QdrantClient

# print(f"Qdrant Client Version: {qdrant_client.__version__}")
try:
    client = QdrantClient(":memory:")
    print("Client type:", type(client))
    print("Has 'search'?", hasattr(client, 'search'))
    print("Has 'query_points'?", hasattr(client, 'query_points'))

    # List all methods starting with s
    print("Methods starting with 's':", [m for m in dir(client) if m.startswith('s')])
    print("Methods starting with 'q':", [m for m in dir(client) if m.startswith('q')])
except Exception as e:
    print(f"Error initializing client: {e}")
    print("Module dir:", dir(qdrant_client))
