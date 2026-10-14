import hashlib
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
import numpy as np
from falkordb import FalkorDB, Graph
from app.config import settings


class FalkorDBManager:
    """
    Production FalkorDB Multigraph Manager.
    Enforces:
      - Isolated tenant graphs via db.select_graph()
      - Read-only execution for untrusted discovery agents via graph.ro_query()
      - Zero-leak ephemeral sandboxing via graph.copy() + finally: delete()
      - Deterministic 768-dim vector generation fallback when offline
    """

    def __init__(self) -> None:
        self.db = FalkorDB(host=settings.falkordb_host, port=settings.falkordb_port)

    def get_graph(self, tenant_graph: str) -> Graph:
        return self.db.select_graph(tenant_graph)

    def list_tenant_graphs(self) -> List[str]:
        return self.db.list_graphs()

    def ensure_indexes(self, tenant_graph: str) -> None:
        graph = self.get_graph(tenant_graph)
        dim = settings.embedding_dim

        range_indexes = [
            "CREATE INDEX FOR (f:File) ON (f.path)",
            "CREATE INDEX FOR (fn:Function) ON (fn.qualified_name)",
            "CREATE INDEX FOR (c:Class) ON (c.qualified_name)",
            "CREATE INDEX FOR (p:PullRequest) ON (p.number)",
            "CREATE INDEX FOR (d:Decision) ON (d.id)",
            "CREATE INDEX FOR (s:StateNode) ON (s.id)",
            "CREATE INDEX FOR (inv:Investigation) ON (inv.id)",
        ]
        vector_indexes = [
            f"CREATE VECTOR INDEX FOR (d:Decision) ON (d.embedding) OPTIONS {{dimension: {dim}, similarityFunction: 'cosine'}}",
            f"CREATE VECTOR INDEX FOR (i:Issue) ON (i.embedding) OPTIONS {{dimension: {dim}, similarityFunction: 'cosine'}}",
            f"CREATE VECTOR INDEX FOR (sig:AnomalySignature) ON (sig.embedding) OPTIONS {{dimension: {dim}, similarityFunction: 'cosine'}}",
        ]

        for stmt in range_indexes + vector_indexes:
            try:
                graph.query(stmt)
            except Exception:
                # Index already exists
                pass

    def query(
        self, tenant_graph: str, cypher: str, params: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, float]:
        graph = self.get_graph(tenant_graph)
        t0 = time.perf_counter()
        res = graph.query(cypher, params or {})
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return res, elapsed_ms

    def ro_query(
        self, tenant_graph: str, cypher: str, params: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, float]:
        graph = self.get_graph(tenant_graph)
        t0 = time.perf_counter()
        res = graph.ro_query(cypher, params or {})
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return res, elapsed_ms

    @contextmanager
    def ephemeral_sandbox(self, base_tenant_graph: str, prefix: str = "sandbox_pr") -> Generator[tuple[Graph, str], None, None]:
        """Clones base_tenant_graph using FalkorDB GRAPH.COPY and guarantees cleanup."""
        sandbox_name = f"{prefix}_{uuid.uuid4().hex[:8]}"
        base_graph = self.get_graph(base_tenant_graph)
        sandbox_graph = base_graph.copy(sandbox_name)
        try:
            yield sandbox_graph, sandbox_name
        finally:
            try:
                sandbox_graph.delete()
            except Exception:
                pass

    @staticmethod
    def embed_text(text: str) -> List[float]:
        """
        Generates a normalized float32 vector of length settings.embedding_dim.
        Uses deterministic token-trigram projection so hybrid vector queries work
        100% reliably offline or without paid API keys, and can be upgraded to
        Gemini/OpenAI embeddings seamlessly.
        """
        dim = settings.embedding_dim
        vec = np.zeros(dim, dtype=np.float32)
        cleaned = text.lower().strip()
        tokens = cleaned.split()
        features = tokens + [cleaned[i : i + 3] for i in range(max(1, len(cleaned) - 2))]
        for feat in features:
            h = int(hashlib.sha256(feat.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return [round(float(x), 6) for x in vec]


db_manager = FalkorDBManager()
