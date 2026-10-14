import hashlib
from typing import Optional
from codesentinel.api.database import SessionLocal, CacheEntry
from codesentinel.observability.metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL

def compute_chunk_hash(chunk_text: str, model: str = "") -> str:
    """Computes SHA-256 hash of a diff chunk, keyed with model name if provided."""
    key = f"{model}:{chunk_text}" if model else chunk_text
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def get_cached_chunk(chunk_text: str, model: str = "") -> Optional[str]:
    """Looks up a diff chunk response in the SQLite cache_entries table."""
    chunk_hash = compute_chunk_hash(chunk_text, model)
    db = SessionLocal()
    try:
        entry = db.query(CacheEntry).filter(CacheEntry.chunk_hash == chunk_hash).first()
        if entry:
            try:
                CACHE_HITS_TOTAL.labels(cache="diff_chunks").inc()
            except Exception:
                pass
            return entry.response_json
        try:
            CACHE_MISSES_TOTAL.labels(cache="diff_chunks").inc()
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"Warning: Cache lookup error: {e}")
        return None
    finally:
        db.close()

def set_cached_chunk(chunk_text: str, response_json: str, model: str = "") -> None:
    """Stores a diff chunk response in the SQLite cache_entries table."""
    chunk_hash = compute_chunk_hash(chunk_text, model)
    db = SessionLocal()
    try:
        entry = db.query(CacheEntry).filter(CacheEntry.chunk_hash == chunk_hash).first()
        if not entry:
            entry = CacheEntry(chunk_hash=chunk_hash, response_json=response_json, model=model)
            db.add(entry)
        else:
            entry.response_json = response_json
            entry.model = model
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Cache store error: {e}")
    finally:
        db.close()

# Convenient aliases
get_cached_response = get_cached_chunk
set_cached_response = set_cached_chunk
hash_chunk = compute_chunk_hash
