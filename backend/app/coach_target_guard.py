from __future__ import annotations

import re
from typing import Any


# "mal" Türkçede hem hakaret hem de nesnel bir isimdir. Bu nedenle tek başına
# yasaklanmaz; yalnız açık ikinci-kişi karşılaştırmasında ve nesnel "mal sahibi /
# mal varlığı" gibi bağlamlar yoksa saldırı olarak değerlendirilir.
_INSULT = (
    r'(?:'
    r'mal(?!\s+(?:sahibi|varlığ\w*|varligi\w*|miktar\w*|stok\w*|teslim\w*|al[ıi]m\w*|sat[ıi]m\w*|beyan\w*))'
    r'|aptal\w*|salak\w*|gerizek[aâ]l[ıi]\w*|ahmak\w*|beyinsiz\w*|embesil\w*'
    r'|dangalak\w*|cahil\w*|ezik\w*|çaps[ıi]z\w*|caps[ıi]z\w*|vas[ıi]fs[ıi]z\w*'
    r')'
)

# Önceki koruma "sen ... mal" biçimini yakalıyordu fakat "senin gibi bir mal"
# ve "senin kadar aptal" gibi tamlama/karşılaştırma biçimleri kelime sınırı
# nedeniyle kaçabiliyordu. Bu desenler yalnız açık kişi hedefi olduğunda çalışır.
_TARGETED_COMPARISON_PATTERNS = (
    rf'\b(?:senin|sizin)\s+gibi\s+(?:bir\s+)?{_INSULT}\b',
    rf'\b(?:senin|sizin)\s+kadar\s+{_INSULT}\b',
    rf'\b(?:hayat[ıi]mda|ömrümde|omrumde)\s+(?:senin|sizin)\s+(?:gibi|kadar)\s+(?:bir\s+)?{_INSULT}\b',
)

# Kişisel saldırı kabuğunu mümkün olduğunca bütün olarak sök. Böylece
# "senin gibi bir mal görmedim hayatımda, bu öneri pahalı" girdisinden
# "bu öneri pahalı" korunur; "görmedim hayatımda" gibi kırık artık kalmaz.
_TARGETED_SHELL_PATTERNS = (
    rf'\b(?:hayat[ıi]mda|ömrümde|omrumde)\s+(?:senin|sizin)\s+(?:gibi|kadar)\s+(?:bir\s+)?{_INSULT}'
    rf'(?:\s+(?:birini|birisini|birisi|biri))?(?:\s+(?:görmedim|görmedik|görmemiştim|görmediniz))?\b[\s,;:.-]*',
    rf'\b(?:senin|sizin)\s+(?:gibi|kadar)\s+(?:bir\s+)?{_INSULT}'
    rf'(?:\s+(?:birini|birisini|birisi|biri))?(?:\s+(?:görmedim|görmedik|görmemiştim|görmediniz|görüyorum|görüyoruz))?'
    rf'(?:\s+(?:hayat[ıi]mda|ömrümde|omrumde|ilk\s+kez))?\b[\s,;:.-]*',
)

_ATTACK_SIGNALS = {'hakaret/küfür', 'kişiye yönelik saldırı', 'tehdit/şiddet'}


def _matches(text: str) -> bool:
    low = text.lower().replace('â', 'a')
    return any(re.search(pattern, low, flags=re.IGNORECASE | re.DOTALL) for pattern in _TARGETED_COMPARISON_PATTERNS)


def _safe_generic() -> str:
    return (
        'Bu görüşe katılmıyorum. '
        'Eleştirimi kişiye değil, ileri sürülen görüşün gerekçelerine odaklamak istiyorum.'
    )


def install(engine_module: Any) -> None:
    """Açık ikinci-kişi karşılaştırmalı hakaretler için son hedef-koruma katmanı."""
    if getattr(engine_module, '_N_KOPRU_TARGET_GUARD_INSTALLED', False):
        return

    previous_analyze = engine_module.analyze_message
    previous_strip = engine_module._strip_attack_shell
    previous_rewrite = engine_module.rewrite_with_ai

    def targeted_analyze_message(text: str) -> list[str]:
        signals = list(previous_analyze(text))
        if _matches(text):
            if 'kişiye yönelik saldırı' not in signals:
                signals.append('kişiye yönelik saldırı')
            signals = [signal for signal in signals if signal != 'nötr/bağlamsal ifade']
        return signals or ['nötr/bağlamsal ifade']

    def targeted_strip_attack_shell(text: str) -> str:
        cleaned = text
        for pattern in _TARGETED_SHELL_PATTERNS:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = previous_strip(cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,;:.-!?')
        return cleaned

    # Mevcut deterministik yeniden yazım bu iki ismi çalışma anında modülden
    # çözdüğü için, rewrite çağrısından önce yerlerine hedef-korumalı sürümleri koy.
    engine_module.analyze_message = targeted_analyze_message
    engine_module._strip_attack_shell = targeted_strip_attack_shell

    def targeted_rewrite_with_ai(text: str, context: str = '', use_ai: bool = True) -> dict[str, Any]:
        result = dict(previous_rewrite(text, context=context, use_ai=use_ai))
        original = text.strip()
        if not original or not _matches(original):
            return result

        suggestion = str(result.get('suggestion') or '').strip()
        output_signals = list(engine_module.analyze_message(suggestion)) if suggestion else []
        unsafe = (
            not suggestion
            or suggestion.casefold() == original.casefold()
            or _matches(suggestion)
            or bool(_ATTACK_SIGNALS.intersection(output_signals))
        )
        if not unsafe:
            return result

        remainder = targeted_strip_attack_shell(original)
        candidate = ''
        if remainder and not _matches(remainder):
            try:
                candidate = (
                    engine_module._question_sentence(remainder)
                    if '?' in original
                    else engine_module._sentence(remainder)
                )
                candidate_signals = list(engine_module.analyze_message(candidate))
                if _ATTACK_SIGNALS.intersection(candidate_signals):
                    candidate = ''
            except Exception:
                candidate = ''

        result['suggestion'] = candidate or _safe_generic()
        result['engine'] = 'targeted-comparison-guard'
        result['reason'] = (
            'Son hedef-koruma denetimi, ikinci kişiye yöneltilmiş karşılaştırmalı '
            'aşağılamayı tespit etti; kişisel saldırı çıkarıldı ve varsa tartışılabilir içerik korundu.'
        )
        result['signals'] = list(engine_module.analyze_message(original))
        return result

    engine_module.rewrite_with_ai = targeted_rewrite_with_ai
    engine_module._N_KOPRU_TARGET_GUARD_INSTALLED = True
