from __future__ import annotations

import re
from typing import Any


def _missing_numbers(engine_module: Any, original: str, suggestion: str) -> list[str]:
    compact = (suggestion or '').replace(' ', '')
    return [
        number
        for number in engine_module._numbers(original)
        if number.replace(' ', '') not in compact
    ]


def _numeric_content_candidate(engine_module: Any, original: str) -> str:
    """Saldırı kabuğundan bağımsız sayısal içerik parçalarını güvenle korur.

    Karma saldırılarda önce virgül/noktalı virgül/cümle sınırları üzerinden
    sayıyı taşıyan gerçek içerik parçaları ayrılır. Böylece saldırı temizleyici
    bir kabuk kalıbını kaçırsa bile sayı ve ona bağlı iddia kaybolmaz.
    """
    pieces = re.split(r'(?<=[.!?])\s+|[,;]\s*', original.strip())
    selected: list[str] = []
    seen_numbers: set[str] = set()

    for piece in pieces:
        numbers = engine_module._numbers(piece)
        if not numbers:
            continue
        cleaned = engine_module._strip_attack_shell(piece).strip(' ,;:.-')
        if not cleaned:
            continue
        try:
            if engine_module._has_attack_residue(cleaned):
                continue
        except Exception:
            pass
        selected.append(cleaned)
        seen_numbers.update(n.replace(' ', '') for n in numbers)

    required = {n.replace(' ', '') for n in engine_module._numbers(original)}
    if not selected or not required.issubset(seen_numbers):
        return ''

    candidate = ' '.join(selected).strip()
    if not candidate:
        return ''

    # Özgün mesaj bir soruysa veya sayısal parça zaten soruysa soru niyetini
    # koru; aksi halde doğrulanabilir iddiaya kanıt/kaynak talebi ekle.
    if '?' in original:
        if not candidate.endswith('?'):
            candidate = candidate.rstrip('.!') + '?'
    else:
        if candidate[-1] not in '.!?':
            candidate += '.'
        low = candidate.casefold()
        if not any(marker in low for marker in ('kaynak', 'araştırma', 'kanıt', 'rapor', 'doi', 'referans')):
            candidate += ' Bu bilginin dayandığı kaynak veya araştırmayı paylaşabilir misin?'

    return candidate


def install(engine_module: Any) -> None:
    """Yanıt Koçu çıktısında kritik içerik-koruma değişmezlerini uygular."""
    if getattr(engine_module, '_N_KOPRU_INVARIANT_GUARD_INSTALLED', False):
        return

    previous_rewrite = engine_module.rewrite_with_ai

    def invariant_rewrite_with_ai(text: str, context: str = '', use_ai: bool = True) -> dict[str, Any]:
        result = dict(previous_rewrite(text, context=context, use_ai=use_ai))
        original = text.strip()
        if not original:
            return result

        signals = list(result.get('signals') or engine_module.analyze_message(original))
        if 'sayısal/doğrulanabilir iddia' not in signals:
            return result

        suggestion = str(result.get('suggestion') or '').strip()
        missing = _missing_numbers(engine_module, original, suggestion)
        if not missing:
            return result

        candidate = _numeric_content_candidate(engine_module, original)
        if not candidate or _missing_numbers(engine_module, original, candidate):
            return result

        try:
            if engine_module._has_attack_residue(candidate):
                return result
        except Exception:
            pass

        result['suggestion'] = candidate
        result['engine'] = 'numeric-invariant-safe'
        result['reason'] = (
            'Son içerik-koruma denetimi, ilk öneride sayısal bilginin kaybolduğunu '
            'tespit etti; saldırı kabuğu çıkarılarak özgün sayısal iddia korundu.'
        )
        return result

    engine_module.rewrite_with_ai = invariant_rewrite_with_ai
    engine_module._N_KOPRU_INVARIANT_GUARD_INSTALLED = True
