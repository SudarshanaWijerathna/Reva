import os
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Cloud Run containers have a read-only filesystem except /tmp.
# Use /tmp for the chat memory DB when running in production.
_SOURCE_DIR = Path(__file__).resolve().parent
_CANDIDATE_PATH = _SOURCE_DIR / "chat_memory.sqlite"
try:
    # Test if the source directory is writable (local dev)
    _CANDIDATE_PATH.touch(exist_ok=True)
    DB_PATH = _CANDIDATE_PATH
except OSError:
    DB_PATH = Path("/tmp/chat_memory.sqlite")


def _init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            session_id TEXT,
            model_type TEXT,
            text_content TEXT,
            metadata_json TEXT,
            embedding_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio_memories (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            property_id TEXT,
            property_type TEXT,
            location TEXT,
            text_content TEXT,
            metadata_json TEXT,
            embedding_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


_init_db()



def _get_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        return [0.0] * 384

    # Ultra-fast, zero-latency 384-dim semantic feature vector with n-grams
    vec = np.zeros(384, dtype=np.float32)
    words = text.lower().replace(",", " ").replace(".", " ").replace(":", " ").split()
    for i, w in enumerate(words):
        h = abs(hash(w)) % 384
        vec[h] += 1.0
        # Add bigram context
        if i > 0:
            h_bi = abs(hash(f"{words[i-1]}_{w}")) % 384
            vec[h_bi] += 0.5

    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec.tolist()



def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def add_prediction_memory(
    user_id: Optional[Any],
    session_id: Optional[str],
    analysis_data: Dict[str, Any],
) -> str:
    user_key = str(user_id) if user_id else "anonymous"
    model_type = analysis_data.get("model_type", "house")
    price = analysis_data.get("price", "")
    loc = analysis_data.get("location", "")
    reasoning = analysis_data.get("reasoning", "")
    rl_rec = analysis_data.get("rl_recommendation", "")
    sequence = analysis_data.get("lstm_sequence", [])
    seq_str = ", ".join([f"{v:,.0f}" for v in sequence]) if sequence else "N/A"

    doc_text = (
        f"Prediction Record: {model_type.upper()} in {loc}. "
        f"Estimated Price: {price}. "
        f"Price Range: {analysis_data.get('range', '')}. "
        f"LSTM 5-Quarter Forecast: [{seq_str}]. "
        f"RL Recommendation: {rl_rec}. "
        f"Reasoning: {reasoning}"
    )

    embedding = _get_embedding(doc_text)
    mem_id = f"{session_id or 's'}_{model_type}_{int(np.random.randint(100000, 999999))}"

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO memories 
        (id, user_id, session_id, model_type, text_content, metadata_json, embedding_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            mem_id,
            user_key,
            session_id or "",
            model_type,
            doc_text,
            json.dumps(analysis_data, default=str),
            json.dumps(embedding) if embedding else None,
        ),
    )
    conn.commit()
    conn.close()
    return mem_id



def search_memory(
    user_id: Optional[Any],
    query_text: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    if not query_text.strip():
        return []

    user_key = str(user_id) if user_id else "anonymous"
    query_vec = _get_embedding(query_text)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, model_type, text_content, metadata_json, embedding_json, created_at
        FROM memories
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (user_key,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    results = []
    for r in rows:
        mem_id, m_type, text_content, meta_str, emb_str, created_at = r
        meta = json.loads(meta_str) if meta_str else {}
        score = 0.0
        if query_vec and emb_str:
            emb = json.loads(emb_str)
            score = _cosine_similarity(query_vec, emb)
        else:
            # Simple keyword match score
            q_words = set(query_text.lower().split())
            t_words = set(text_content.lower().split())
            overlap = len(q_words.intersection(t_words))
            score = overlap / max(len(q_words), 1)

        results.append({
            "id": mem_id,
            "score": score,
            "model_type": m_type,
            "text": text_content,
            "data": meta,
            "created_at": created_at,
        })

    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def get_last_prediction(
    user_id: Optional[Any],
    session_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    user_key = str(user_id) if user_id else "anonymous"
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    if session_id:
        cursor.execute(
            """
            SELECT text_content, metadata_json FROM memories
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_key, session_id),
        )
    else:
        cursor.execute(
            """
            SELECT text_content, metadata_json FROM memories
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_key,),
        )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "text": row[0],
            "data": json.loads(row[1]) if row[1] else {},
        }
    return None


def add_portfolio_memory(
    user_id: Any,
    property_data: Dict[str, Any],
) -> str:
    """Store or update an owned property representation in vector memory."""
    user_key = str(user_id) if user_id else "anonymous"
    prop_id = str(property_data.get("property_id") or property_data.get("id") or "new")
    prop_type = str(property_data.get("type") or property_data.get("property_type") or "housing").lower()
    location = str(property_data.get("location") or "")
    purchase_price = property_data.get("purchase_price", 0)
    current_val = property_data.get("current_value", purchase_price)
    profit = property_data.get("profit", 0)
    sentiment = property_data.get("sentiment", "good")

    # Build rich natural text description
    details = []
    if property_data.get("house_size_sqft"):
        details.append(f"{property_data['house_size_sqft']} sqft")
    if property_data.get("land_size_perches") or property_data.get("land_size"):
        sz = property_data.get("land_size_perches") or property_data.get("land_size")
        details.append(f"{sz} perches")
    if property_data.get("floors"):
        details.append(f"{property_data['floors']} floors")
    if property_data.get("monthly_rent"):
        details.append(f"Rent: LKR {float(property_data['monthly_rent']):,.0f}/mo")
    if property_data.get("occupancy_status"):
        details.append(f"Occupancy: {property_data['occupancy_status']}")
    if property_data.get("zoning_type"):
        details.append(f"Zoning: {property_data['zoning_type']}")

    det_str = f" Details: ({', '.join(details)})" if details else ""

    doc_text = (
        f"Owned Asset: {prop_type.upper()} in {location}. "
        f"Purchase Price: LKR {float(purchase_price or 0):,.0f}. "
        f"Estimated Valuation: LKR {float(current_val or 0):,.0f}. "
        f"Profit / Gain: LKR {float(profit or 0):,.0f}. "
        f"Sentiment: {sentiment}.{det_str}"
    )

    mem_id = f"user_{user_key}_prop_{prop_id}"
    embedding = _get_embedding(doc_text)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO portfolio_memories 
        (id, user_id, property_id, property_type, location, text_content, metadata_json, embedding_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            mem_id,
            user_key,
            prop_id,
            prop_type,
            location,
            doc_text,
            json.dumps(property_data, default=str),
            json.dumps(embedding) if embedding else None,
        ),
    )
    conn.commit()
    conn.close()
    return mem_id



def sync_portfolio_memories(
    user_id: Any,
    properties_list: List[Dict[str, Any]],
) -> int:
    """Sync all current portfolio properties into vector memory."""
    if not user_id:
        return 0
    count = 0
    for p in properties_list:
        add_portfolio_memory(user_id, p)
        count += 1
    return count


def search_portfolio_memory(
    user_id: Any,
    query_text: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Perform semantic search over user's owned portfolio properties."""
    if not user_id:
        return []
    user_key = str(user_id)
    query_vec = _get_embedding(query_text)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT property_id, property_type, location, text_content, metadata_json, embedding_json
        FROM portfolio_memories
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (user_key,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    results = []
    for r in rows:
        p_id, p_type, loc, text_content, meta_str, emb_str = r
        meta = json.loads(meta_str) if meta_str else {}
        score = 0.0
        if query_vec and emb_str:
            emb = json.loads(emb_str)
            score = _cosine_similarity(query_vec, emb)
        else:
            q_words = set(query_text.lower().split())
            t_words = set(text_content.lower().split())
            overlap = len(q_words.intersection(t_words))
            score = overlap / max(len(q_words), 1)

        results.append({
            "property_id": p_id,
            "property_type": p_type,
            "location": loc,
            "score": score,
            "text": text_content,
            "data": meta,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def get_portfolio_summary_context(user_id: Any) -> str:
    """Retrieve a concise natural text summary of all properties owned by the user."""
    if not user_id:
        return ""
    user_key = str(user_id)
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT text_content
        FROM portfolio_memories
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (user_key,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ""

    lines = [f"- {r[0]}" for r in rows]
    return "\n".join(lines)

