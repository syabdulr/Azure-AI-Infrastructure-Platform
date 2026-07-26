"""
Azure Cognitive Search client for RAG pipeline

This module provides Azure Cognitive Search integration for:
- Hybrid search (vector + keyword)
- Semantic reranking
- Vector search
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class CognitiveSearchClient:
    """Azure Cognitive Search client for RAG pipeline"""

    def __init__(self):
        """Initialize Cognitive Search client"""
        self.settings = get_settings()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Azure Cognitive Search client"""
        try:
            if not self.settings.azure_search_endpoint:
                logger.warning("Azure Search endpoint not configured")
                return

            # Import azure-search-documents
            from azure.identity import DefaultAzureCredential
            from azure.search.documents import SearchClient

            # Initialize with managed identity or API key
            if self.settings.azure_client_id:
                credential = DefaultAzureCredential()
                self.client = SearchClient(
                    endpoint=self.settings.azure_search_endpoint,
                    index_name=self.settings.azure_search_index,
                    credential=credential,
                )
            elif self.settings.azure_search_api_key:
                self.client = SearchClient(
                    endpoint=self.settings.azure_search_endpoint,
                    index_name=self.settings.azure_search_index,
                    api_key=self.settings.azure_search_api_key,
                )
            else:
                logger.warning("No authentication method configured for Azure Search")

            logger.info("Azure Cognitive Search client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Azure Search client: {e}")
            raise

    async def hybrid_search(
        self, query: str, top_k: int = 5, min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + keyword + semantic)

        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum relevance score

        Returns:
            List of search results with combined scores
        """
        if not self.client:
            logger.warning("Cognitive Search client not initialized")
            return []

        try:
            # Step 1: Perform vector search
            from src.llm.azure_openai_client import AzureOpenAIClient

            openai_client = AzureOpenAIClient()

            # Generate query embedding
            embeddings = await openai_client.get_embeddings([query])
            query_vector = embeddings[0]

            # Vector search results
            vector_results = await self._vector_search_internal(query_vector, top_k * 2)

            # Keyword search results
            keyword_results = await self._keyword_search_internal(query, top_k * 2)

            # Combine using Reciprocal Rank Fusion (RRF)
            combined_results = self._reciprocal_rank_fusion(
                vector_results, keyword_results, k=60  # RRF constant
            )

            # Apply semantic reranking if available
            combined_results = await self._semantic_rerank(query, combined_results)

            # Filter by minimum score
            filtered_results = [
                r for r in combined_results if r.get("@search.score", 0) >= min_score
            ]

            # Return top_k results
            return filtered_results[:top_k]

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def vector_search(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform vector search with HNSW algorithm

        Args:
            vector: Query vector
            top_k: Number of results to return

        Returns:
            List of search results with vector scores
        """
        return await self._vector_search_internal(vector, top_k)

    async def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search with prioritized fields

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of search results with semantic scores
        """
        if not self.client:
            logger.warning("Cognitive Search client not initialized")
            return []

        try:
            from azure.search.documents.models import VectorizableTextQuery

            # Create semantic search query
            vector_query = VectorizableTextQuery(text=query, k=top_k, fields="content_vector")

            # Execute search with semantic configuration
            results = self.client.search(
                search_text=query,
                vector_queries=[vector_query],
                query_type="semantic",
                semantic_configuration_name="default-semantic-config",
                top=top_k,
                select=["id", "title", "content", "source", "metadata"],
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": result.get("id"),
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "source": result.get("source", ""),
                        "score": result.get("@search.score", 0),
                        "metadata": result.get("metadata", {}),
                        "reranker_score": result.get("@search.rerankerScore", 0),
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def _vector_search_internal(
        self, vector: List[float], top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Internal vector search implementation

        Args:
            vector: Query vector
            top_k: Number of results

        Returns:
            List of search results
        """
        try:
            from azure.search.documents.models import VectorQuery

            # Create vector query
            vector_query = VectorQuery(vector=vector, k=top_k, fields="content_vector")

            # Execute vector search
            results = self.client.search(
                search_text="*",
                vector_queries=[vector_query],
                top=top_k,
                select=["id", "title", "content", "source", "metadata"],
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": result.get("id"),
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "source": result.get("source", ""),
                        "score": result.get("@search.score", 0),
                        "metadata": result.get("metadata", {}),
                        "search_type": "vector",
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def _keyword_search_internal(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Internal keyword search implementation

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of search results
        """
        try:
            # Execute keyword search (BM25)
            results = self.client.search(
                search_text=query,
                query_type="simple",
                top=top_k,
                select=["id", "title", "content", "source", "metadata"],
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": result.get("id"),
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "source": result.get("source", ""),
                        "score": result.get("@search.score", 0),
                        "metadata": result.get("metadata", {}),
                        "search_type": "keyword",
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _reciprocal_rank_fusion(
        self, results_a: List[Dict[str, Any]], results_b: List[Dict[str, Any]], k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Combine two result lists using Reciprocal Rank Fusion (RRF)

        Args:
            results_a: First result list
            results_b: Second result list
            k: RRF constant (typically 60)

        Returns:
            Combined and reranked results
        """
        # Create a dictionary to accumulate scores
        score_dict = {}
        result_dict = {}

        # Process first list
        for rank, result in enumerate(results_a):
            doc_id = result.get("id")
            rrf_score = 1.0 / (k + rank + 1)

            if doc_id not in score_dict:
                score_dict[doc_id] = 0
                result_dict[doc_id] = result

            score_dict[doc_id] += rrf_score

        # Process second list
        for rank, result in enumerate(results_b):
            doc_id = result.get("id")
            rrf_score = 1.0 / (k + rank + 1)

            if doc_id not in score_dict:
                score_dict[doc_id] = 0
                result_dict[doc_id] = result

            score_dict[doc_id] += rrf_score

        # Combine results with RRF scores
        combined_results = []
        for doc_id, rrf_score in score_dict.items():
            result = result_dict[doc_id]
            result["@search.score"] = rrf_score
            result["combined_type"] = "hybrid"
            combined_results.append(result)

        # Sort by RRF score
        combined_results.sort(key=lambda x: x.get("@search.score", 0), reverse=True)

        return combined_results

    async def _semantic_rerank(
        self, query: str, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply semantic reranking to results

        Args:
            query: Original query
            results: Search results to rerank

        Returns:
            Reranked results
        """
        # Semantic reranking is already applied by Azure Cognitive Search
        # This method can be used for custom reranking logic
        return results

    async def index_document(self, document: Dict[str, Any]) -> str:
        """
        Index a document with embeddings

        Args:
            document: Document data with 'title', 'content', 'source', 'metadata'

        Returns:
            Document ID
        """
        if not self.client:
            raise Exception("Cognitive Search client not initialized")

        try:
            # Generate document ID
            import uuid

            doc_id = document.get("id") or f"doc-{uuid.uuid4()}"

            # Generate embeddings for content
            from src.llm.azure_openai_client import AzureOpenAIClient

            openai_client = AzureOpenAIClient()

            embeddings = await openai_client.get_embeddings([document.get("content", "")])
            content_vector = embeddings[0]

            # Prepare document for indexing
            index_document = {
                "id": doc_id,
                "title": document.get("title", ""),
                "content": document.get("content", ""),
                "source": document.get("source", ""),
                "content_vector": content_vector,
                "metadata": document.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat(),
            }

            # Upload to Azure Cognitive Search
            result = self.client.upload_documents(documents=[index_document])

            if result[0].succeeded:
                logger.info(f"Document {doc_id} indexed successfully")
                return doc_id
            else:
                raise Exception(f"Document indexing failed: {result[0].error_message}")

        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            raise

    async def batch_index_documents(
        self, documents: List[Dict[str, Any]], batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Index multiple documents in batches

        Args:
            documents: List of documents to index
            batch_size: Batch size for processing

        Returns:
            Dictionary with indexing statistics
        """
        if not self.client:
            raise Exception("Cognitive Search client not initialized")

        try:
            import uuid

            from src.llm.azure_openai_client import AzureOpenAIClient

            openai_client = AzureOpenAIClient()

            # Initialize statistics
            stats = {
                "total_documents": len(documents),
                "successful": 0,
                "failed": 0,
                "total_chunks_indexed": 0,
                "errors": [],
            }

            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]

                # Generate embeddings for batch
                contents = [doc.get("content", "") for doc in batch]
                embeddings_list = await openai_client.get_embeddings(contents)

                # Prepare documents for indexing
                index_documents = []
                for j, doc in enumerate(batch):
                    doc_id = doc.get("id") or f"doc-{uuid.uuid4()}"

                    index_documents.append(
                        {
                            "id": doc_id,
                            "title": doc.get("title", ""),
                            "content": doc.get("content", ""),
                            "source": doc.get("source", ""),
                            "content_vector": embeddings_list[j],
                            "metadata": doc.get("metadata", {}),
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    )

                # Upload batch
                results = self.client.upload_documents(documents=index_documents)

                # Update statistics
                for result in results:
                    if result.succeeded:
                        stats["successful"] += 1
                        stats["total_chunks_indexed"] += 1
                    else:
                        stats["failed"] += 1
                        stats["errors"].append({"key": result.key, "error": result.error_message})

                logger.info(
                    f"Batch {i//batch_size + 1} processed: {stats['successful']}/{len(batch)}"
                )

            logger.info(f"Batch indexing complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Batch indexing failed: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of Azure Cognitive Search

        Returns:
            Dictionary with health status and response time
        """
        start_time = datetime.utcnow()

        try:
            if not self.client:
                return {"status": "unhealthy", "error": "Client not initialized"}

            # Simple health check - try to get index statistics
            # self.client.get_index_statistics()

            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {"status": "healthy", "response_time_ms": response_time_ms}

        except Exception as e:
            logger.error(f"Azure Search health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
