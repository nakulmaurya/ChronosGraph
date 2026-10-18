import hashlib
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
import numpy as np
from falkordb import FalkorDB, Graph
from redis.exceptions import ResponseError
from app.config import settings


class FalkorDBManager:
    """
    Production FalkorDB Multigraph Manager.
    Enforces:
      - Isolated tenant graphs via db.select_graph()
      - Read-only execution for discovery agents via graph.ro_query()
      - Zero-leak ephemeral sandboxing via graph.copy() + finally: delete()
      - Deterministic 768-dim vector generation fallback when offline
    """

    def __init__(self) -> None:
        self.db = FalkorDB(host=settings.falkordb_host, port=settings.falkordb_port)

    def get_graph(self, tenant_graph: str) -> Graph:
        return self.db.select_graph(tenant_graph)

    def list_tenant_graphs(self) -> List[str]:
        return self.db.list_graphs()

    def copy_graph(self, source: str, destination: str) -> Graph:
        """Bounded retry only for native fork refusal (e.g. AOF/BGSAVE).

        Never retry transport errors, destination collisions, or ambiguous
        responses. The caller owns a unique destination and its cleanup.
        This does not lock or freeze the source while waiting.
        """
        graph = self.get_graph(source)
        deadline = time.monotonic() + 5.0
        delay = 0.05
        while True:
            try:
                return graph.copy(destination)
            except ResponseError as exc:
                if str(exc) != "GRAPH.COPY failed, could not fork":
                    raise
                remaining = deadline - time.monotonic()
                if remaining <= 0 or destination in self.list_tenant_graphs():
                    raise
                time.sleep(min(delay, remaining))
                delay = min(delay * 2, 0.5)

    def ensure_indexes(self, tenant_graph: str) -> None:
        graph = self.get_graph(tenant_graph)
        dim = settings.embedding_dim

        range_indexes = [
            "CREATE INDEX FOR (f:File) ON (f.path)",
            "CREATE INDEX FOR (f:TrackedFile) ON (f.path)",
            "CREATE INDEX FOR (c:CommitFileChange) ON (c.id)",
            "CREATE INDEX FOR (p:PullRequest) ON (p.commit_sha)",
            "CREATE INDEX FOR (fn:Function) ON (fn.qualified_name)",
            "CREATE INDEX FOR (fn:Function) ON (fn.name)",
            "CREATE INDEX FOR (c:Class) ON (c.qualified_name)",
            "CREATE INDEX FOR (c:Class) ON (c.name)",
            "CREATE INDEX FOR (p:PullRequest) ON (p.number)",
            "CREATE INDEX FOR (d:Decision) ON (d.id)",
            "CREATE INDEX FOR (d:Decision) ON (d.status)",
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
    def ephemeral_sandbox(
        self, base_tenant_graph: str, prefix: str = "sandbox_pr"
    ) -> Generator[tuple[Graph, str, float], None, None]:
        """Clones base_tenant_graph using FalkorDB GRAPH.COPY and guarantees cleanup."""
        sandbox_name = f"{prefix}_{uuid.uuid4().hex[:8]}"
        t0 = time.perf_counter()
        sandbox_graph = self.copy_graph(base_tenant_graph, sandbox_name)
        clone_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        try:
            yield sandbox_graph, sandbox_name, clone_ms
        finally:
            try:
                sandbox_graph.delete()
            except Exception:
                pass

    @staticmethod
    def embed_text(text: str) -> List[float]:
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
