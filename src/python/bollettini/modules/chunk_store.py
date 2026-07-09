"""
ChunkStore: archivio leggero dei chunk dei bollettini (testo + metadati).

Sostituisce ChromaDB per QUESTO progetto: qui non serve ricerca semantica/vettoriale
(il retrieval e' per match esatto su metadati), quindi un semplice store SQLite e'
piu' onesto, leggero e senza dipendenze (sqlite3 e' stdlib) ne' embedding.

Backend SQLite (un solo file). I metodi di lettura ritornano la STESSA forma di
ChromaDB.get() -> {"documents": [...], "metadatas": [...]} per minimizzare le modifiche
ai consumatori (colture.py).
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

# Campi metadati persistiti (schema piatto, 1:1 coi chunk prodotti dal chunking)
META_FIELDS = [
    "doc_name", "regione", "data", "province", "numero_bollettino",
    "tipo_documento", "section_title", "parent_coltura", "applies_to",
]


class ChunkStore:
    """Store SQLite dei chunk. Thread-safe a livello di connessione (una per operazione)."""

    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        cols = ", ".join(f"{f} TEXT" for f in META_FIELDS)
        with self._conn() as c:
            c.execute(
                f"CREATE TABLE IF NOT EXISTS chunks ("
                f"chunk_id TEXT PRIMARY KEY, {cols}, content TEXT)"
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_doc ON chunks(doc_name)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_reg ON chunks(regione)")

    # ---------- scrittura ----------
    def upsert_chunks(self, chunks: List[Dict]):
        """Inserisce/aggiorna chunk. Ogni chunk = {chunk_id, content, metadata{...}}."""
        placeholders = ", ".join(["?"] * (len(META_FIELDS) + 2))
        cols = ", ".join(["chunk_id"] + META_FIELDS + ["content"])
        rows = []
        for ch in chunks:
            m = ch.get("metadata", {})
            vals = [ch["chunk_id"]]
            for f in META_FIELDS:
                v = m.get(f)
                vals.append("" if v is None else str(v))
            vals.append(ch.get("content", ""))
            rows.append(tuple(vals))
        with self._conn() as c:
            c.executemany(
                f"INSERT OR REPLACE INTO chunks ({cols}) VALUES ({placeholders})", rows
            )

    def delete_doc(self, doc_name: str):
        with self._conn() as c:
            c.execute("DELETE FROM chunks WHERE doc_name = ?", (doc_name,))

    # ---------- lettura (forma compatibile con ChromaDB.get) ----------
    def _select(self, where_sql: str = "", params: tuple = ()) -> Dict[str, List]:
        cols = ", ".join(META_FIELDS)
        sql = f"SELECT content, {cols} FROM chunks {where_sql}"
        with self._conn() as c:
            cur = c.execute(sql, params)
            documents, metadatas = [], []
            for row in cur.fetchall():
                documents.append(row[0])
                metadatas.append({f: row[i + 1] for i, f in enumerate(META_FIELDS)})
            return {"documents": documents, "metadatas": metadatas}

    def get_by_doc(self, doc_name: str) -> Dict[str, List]:
        """Tutti i chunk di un bollettino."""
        return self._select("WHERE doc_name = ?", (doc_name,))

    def get_all(self, regione: Optional[str] = None) -> Dict[str, List]:
        """Tutti i chunk (eventualmente filtrati per regione)."""
        if regione:
            return self._select("WHERE regione = ?", (regione,))
        return self._select()

    # ---------- utilita' ----------
    def count(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    def distinct_docs(self, regione: Optional[str] = None) -> List[str]:
        with self._conn() as c:
            if regione:
                cur = c.execute("SELECT DISTINCT doc_name FROM chunks WHERE regione = ?", (regione,))
            else:
                cur = c.execute("SELECT DISTINCT doc_name FROM chunks")
            return [r[0] for r in cur.fetchall()]
