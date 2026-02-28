"""Cached embeddings wrapper for LangChain."""

import hashlib
from typing import Any

from langchain_core.embeddings import Embeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db.models import EmbeddingCache


class CachedEmbeddings(Embeddings):
    """Wrapper around another Embeddings class that caches results in the database."""

    def __init__(
        self,
        underlying_embeddings: Embeddings,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        """Initialize the cached embeddings.
        
        Args:
            underlying_embeddings: The actual embeddings implementation to use when a cache miss occurs.
            session_factory: Factory for creating async database sessions.
        """
        self.underlying_embeddings = underlying_embeddings
        self.session_factory = session_factory

    def _hash_text(self, text: str) -> str:
        """Create a SHA-256 hash of the text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed search docs (synchronous - not implemented for db cache).
        
        Since our database access is async-only, we require the async version to be used.
        """
        raise NotImplementedError(
            "CachedEmbeddings only supports async execution via aembed_documents"
        )

    def embed_query(self, text: str) -> list[float]:
        """Embed query text (synchronous - not implemented for db cache)."""
        raise NotImplementedError(
            "CachedEmbeddings only supports async execution via aembed_query"
        )

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Asynchronously embed search docs, using the database cache when possible."""
        # 1. Compute hashes for all requested texts to maintain original order
        text_hashes: list[str] = [self._hash_text(t) for t in texts]
        
        # 2. Check the database for existing hashes
        cached_results: dict[str, list[float]] = {}
        async with self.session_factory() as session:
            stmt = select(EmbeddingCache).where(EmbeddingCache.text_hash.in_(text_hashes))
            result = await session.execute(stmt)
            for row in result.scalars():
                # pgvector returns ndarray or list; ensure it's a list
                cached_results[row.text_hash] = list(row.embedding)

        # 3. Identify texts that missed the cache
        missing_indices: list[int] = []
        missing_texts: list[str] = []
        for i, text_hash in enumerate(text_hashes):
            if text_hash not in cached_results:
                missing_indices.append(i)
                missing_texts.append(texts[i])

        # 4. Fetch missing embeddings from the underlying provider
        if missing_texts:
            print(f"EmbeddingCache: missed {len(missing_texts)} chunks, fetching from provider...")
            if hasattr(self.underlying_embeddings, "aembed_documents"):
                new_embeddings = await self.underlying_embeddings.aembed_documents(missing_texts)
            else:
                raise NotImplementedError("Underlying embeddings does not support async")

            # 5. Save the newly fetched embeddings to the database
            async with self.session_factory() as session:
                for i, text in enumerate(missing_texts):
                    text_hash = text_hashes[missing_indices[i]]
                    embedding = new_embeddings[i]
                    
                    # Store in our original order tracking
                    cached_results[text_hash] = embedding
                    
                    # Store in DB
                    db_entry = EmbeddingCache(
                        text_hash=text_hash,
                        embedding=embedding,
                    )
                    session.add(db_entry)
                
                try:
                    await session.commit()
                except Exception as e:
                    print(f"Warning: Failed to save embeddings to cache: {e}")
                    await session.rollback()
        else:
            print(f"EmbeddingCache: served all {len(texts)} chunks from cache.")

        # 6. Reconstruct the requested list in the exact original order
        final_embeddings: list[list[float]] = []
        for text_hash in text_hashes:
            final_embeddings.append(cached_results[text_hash])

        return final_embeddings

    async def aembed_query(self, text: str) -> list[float]:
        """Asynchronously embed query text."""
        # A query is just a single document
        docs = await self.aembed_documents([text])
        return docs[0]
