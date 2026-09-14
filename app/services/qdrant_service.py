"""Qdrant Vector Database Service handling hybrid search (Dense + Sparse RRF)."""

from typing import List, Optional
import uuid
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding, SparseTextEmbedding
from langchain_core.documents import Document

from app.config import settings, logger


class QdrantVectorService:
    """Service for managing Qdrant vector collections and executing hybrid search queries."""

    _client: Optional[QdrantClient] = None
    _dense_model: Optional[TextEmbedding] = None
    _sparse_model: Optional[SparseTextEmbedding] = None

    COLLECTION_NAME: str = settings.QDRANT_COLLECTION_NAME

    @classmethod
    def get_client(cls) -> QdrantClient:
        """Initialize and return singleton QdrantClient instance connected to Qdrant server."""
        if cls._client is None:
            try:
                cls._client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=5.0)
                logger.info(f"Connected to Qdrant server at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            except Exception as err:
                logger.error(f"Failed to connect to Qdrant server: {err}")
                raise RuntimeError(f"Failed to connect to Qdrant server: {err}") from err
        return cls._client


    @classmethod
    def get_dense_model(cls) -> TextEmbedding:
        """Lazy load Dense Embedding Model (BAAI/bge-small-en-v1.5)."""
        if cls._dense_model is None:
            logger.info("Loading FastEmbed Dense Model: 'BAAI/bge-small-en-v1.5'...")
            cls._dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return cls._dense_model

    @classmethod
    def get_sparse_model(cls) -> SparseTextEmbedding:
        """Lazy load Sparse Embedding Model (Qdrant/bm25)."""
        if cls._sparse_model is None:
            logger.info("Loading FastEmbed Sparse Model: 'Qdrant/bm25'...")
            cls._sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        return cls._sparse_model

    @classmethod
    def init_collection(cls) -> None:
        """Ensure Qdrant collection exists with dual Dense & Sparse vector configurations."""
        client = cls.get_client()
        collections = [c.name for c in client.get_collections().collections]

        if cls.COLLECTION_NAME not in collections:
            logger.info(f"Creating Qdrant collection '{cls.COLLECTION_NAME}' with dense (384d) and sparse BM25 vectors...")
            client.create_collection(
                collection_name=cls.COLLECTION_NAME,
                vectors_config={
                    "dense": models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False,
                        )
                    )
                },
            )
            logger.info(f"Qdrant collection '{cls.COLLECTION_NAME}' created successfully.")

    @classmethod
    def upsert_documents(cls, chunks: List[Document]) -> int:
        """Generate Dense + Sparse embeddings and upsert document payload chunks into Qdrant.

        Args:
            chunks (List[Document]): List of LangChain Document objects.

        Returns:
            int: Number of points upserted.
        """
        if not chunks:
            return 0

        cls.init_collection()
        client = cls.get_client()

        texts = [doc.page_content for doc in chunks]

        # Generate Dense Embeddings
        dense_model = cls.get_dense_model()
        dense_embeddings = list(dense_model.embed(texts))

        # Generate Sparse Embeddings
        sparse_model = cls.get_sparse_model()
        sparse_embeddings = list(sparse_model.embed(texts))

        points = [
            models.PointStruct(
                id=uuid.uuid4().hex,
                vector={
                    "dense": dense_vec.tolist(),
                    "sparse": models.SparseVector(
                        indices=sparse_emb.indices.tolist(),
                        values=sparse_emb.values.tolist(),
                    ),
                },
                payload={
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "page_number": doc.metadata.get("page_number", 1),
                    "category": doc.metadata.get("category", "general"),
                    "product_name": doc.metadata.get("product_name", ""),
                    "brand": doc.metadata.get("brand", ""),
                },
            )
            for doc, dense_vec, sparse_emb in zip(chunks, dense_embeddings, sparse_embeddings)
        ]

        client.upsert(collection_name=cls.COLLECTION_NAME, points=points)
        logger.info(f"Successfully upserted {len(points)} hybrid points to Qdrant collection '{cls.COLLECTION_NAME}'.")
        return len(points)

    @classmethod
    def hybrid_search(cls, query: str, top_k: int = 4) -> List[Document]:
        """Perform Hybrid Search using Dense + Sparse Prefetch queries fused via Reciprocal Rank Fusion (RRF).

        Args:
            query (str): User natural language enquiry string.
            top_k (int): Number of top context chunks to retrieve.

        Returns:
            List[Document]: List of matching LangChain Document objects with score metadata.
        """
        client = cls.get_client()
        collections = [c.name for c in client.get_collections().collections]

        if cls.COLLECTION_NAME not in collections:
            logger.warning(f"Collection '{cls.COLLECTION_NAME}' does not exist in Qdrant.")
            return []

        # Embed query dense
        dense_model = cls.get_dense_model()
        dense_query_vec = list(dense_model.embed([query]))[0].tolist()

        # Embed query sparse
        sparse_model = cls.get_sparse_model()
        sparse_query_obj = list(sparse_model.embed([query]))[0]
        sparse_query_vec = models.SparseVector(
            indices=sparse_query_obj.indices.tolist(),
            values=sparse_query_obj.values.tolist(),
        )

        try:
            # Prefetch Dense + Sparse, fused using Reciprocal Rank Fusion (RRF)
            response = client.query_points(
                collection_name=cls.COLLECTION_NAME,
                prefetch=[
                    models.Prefetch(
                        query=dense_query_vec,
                        using="dense",
                        limit=top_k * 2,
                    ),
                    models.Prefetch(
                        query=sparse_query_vec,
                        using="sparse",
                        limit=top_k * 2,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
            )

            documents: List[Document] = [
                Document(
                    page_content=hit.payload.get("text", ""),
                    metadata={
                        "source": hit.payload.get("source", ""),
                        "page_number": hit.payload.get("page_number", 1),
                        "category": hit.payload.get("category", "general"),
                        "product_name": hit.payload.get("product_name", ""),
                        "brand": hit.payload.get("brand", ""),
                        "score": hit.score,
                    },
                )
                for hit in response.points
            ]
            return documents
        except Exception as err:
            logger.error(f"Error during Qdrant Hybrid Search: {err}")
            return []

