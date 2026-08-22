"""Donanımdan bağımsız, sınırlı ve yalnızca süreç içinde yaşayan iddia önbelleği.

Önbellek SQLite'a yazılmaz; ham yorum metni yerine SHA-256 anahtarı tutar.
Bir sonuç yalnızca aynı model nesnesi, model adı, cihaz, başlık, yorum ve
karar sözleşmesi için yeniden kullanılır.
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from threading import RLock


CACHE_SCHEMA = 'n-kopru-claim-decision-v1'
CACHE_MAX_ENTRIES = 512
CLAIM_INFERENCE_LOCK = RLock()
_CACHE_LOCK = RLock()
_CACHE: OrderedDict[str, tuple[bool, float]] = OrderedDict()


def claim_cache_key(
    title: str,
    comment_text: str,
    *,
    model_name: str,
    device: str,
    model_identity: int,
    candidate_labels: list[str],
    hypothesis_template: str,
    threshold: float,
) -> str:
    """Modelin gerçekten gördüğü her girdiyi değiştirilmeden anahtara katar."""
    payload = json.dumps(
        {
            'schema': CACHE_SCHEMA,
            'model': model_name,
            'device': device,
            'model_identity': model_identity,
            'title': title,
            'text': comment_text,
            'labels': candidate_labels,
            'hypothesis_template': hypothesis_template,
            'threshold': threshold,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def claim_cache_get(key: str) -> tuple[bool, float] | None:
    with _CACHE_LOCK:
        value = _CACHE.get(key)
        if value is not None:
            _CACHE.move_to_end(key)
        return value


def claim_cache_store(key: str, value: tuple[bool, float]) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = value
        _CACHE.move_to_end(key)
        while len(_CACHE) > CACHE_MAX_ENTRIES:
            _CACHE.popitem(last=False)


def claim_cache_discard(keys: list[str]) -> int:
    with _CACHE_LOCK:
        return sum(_CACHE.pop(key, None) is not None for key in set(keys))


def clear_claim_cache() -> int:
    with _CACHE_LOCK:
        count = len(_CACHE)
        _CACHE.clear()
        return count


def claim_cache_size() -> int:
    with _CACHE_LOCK:
        return len(_CACHE)
