from __future__ import annotations

import re
import unicodedata
from typing import Any


_ATTACK_SIGNALS = {'hakaret/küfür', 'kişiye yönelik saldırı', 'tehdit/şiddet'}
_SUBSTANTIVE_SIGNALS = {
    'soru',
    'sayısal/doğrulanabilir iddia',
    'kaynak/kanıt vurgusu',
    'koşullu/dengeli görüş',
    'görüş ayrılığı/itiraz',
    'destek/olumlu görüş',
    'konuya katkı eleştirisi',
    'bağlamı yeniden değerlendirme talebi',
}

# Sosyal medya / YouTube tarzı gerçek dünya yazımlarında açık küfür kullanmadan
# kişiyi küçümseyen kalıplar. Kalıplar özellikle kişi-hedefli tutulur; konu,
# nesne veya sözcük açıklaması gibi masum kullanımları kapsamaması amaçlanır.
_REALWORLD_PERSONAL_PATTERNS = (
    r'\b(?:sen\s+de\s+)?ne\s+boş\s+adams[ıi]n\b',
    r'\bokumay[ıi]\s+öğren\s+de\s+gel\b',
    r'\bbeynini\s+kullan(?:\s+biraz)?\b',
    r'\banlama\s+kapasiten\s+yok\b',
    r'\b(?:ilkokul\s+çocuğu|çocuk|cocuk)\s+senden\s+(?:daha\s+)?iyi\s+anlar\b',
    r'\bzek[aâ]\s+seviyen\b.{0,30}\b(?:yetmiyor|yetmez)\b',
    r"\biq['’]?n\s+kaç\s+senin\b",
    r'\bsana\s+laf\s+anlat[ıi]lmaz\b',
    r'\bseninle\s+tart[ıi]şmak\s+zaman\s+kayb[ıi]\b',
    r'\bkendini\s+rezil\s+ediyorsun\b',
    r'\bac[ıi]nas[ıi]\s+birisin\b',
    r'\bşaka\s+m[ıi]s[ıi]n\s+sen\b',
    r'\bergen\s+m[ıi]s[ıi]n\s+nesin\b',
    r'\bfanboyluk\s+yapma\b',
    r'\bkudurmuşsun\b',
    r'\bhadi\s+ordan\b',
    r'\byürü\s+git\b',
    r'\badam\s+değilsin\b',
    r'\binsan\s+içine\s+ç[ıi]kma\b',
    r'\bhangi\s+mağaradan\s+ç[ıi]kt[ıi]n\b',
    r'\bbeynin\s+alm[ıi]yor\b',
    r'\bkafan[ıi]\s+çalışt[ıi]r\s+da\s+yaz\b',
    r'\bokuduğunu\s+anlam[ıi]yorsun\b',
    r'\bbu\s+kadar\s+cahillik\s+fazla\b',
    r'\bpalyaço\s+gibi\s+konuşuyorsun\b',
    r'\btam\s+bir\s+eziksin\b',
    r'\bçaps[ıi]z[ıi]n\s+tekisin\b',
    r'\bvas[ıi]fs[ıi]z\s+herif\b',
    r'\bmanyak\s+m[ıi]s[ıi]n\s+sen\b',
    r'\bkudur\s+fanboy\b',
)

# Tehdidi yalnız belirgin eylem/sonuç birlikteliklerinde genişletiyoruz. Böylece
# "adresini bulurum" gibi korkutma bağlamı yakalanırken sıradan "bulurum"
# fiilinin tehdit diye etiketlenmesi önlenir.
_REALWORLD_THREAT_PATTERNS = (
    r'\badresini\s+bulurum(?:\s+görürsün)?\b',
    r'\bnerede\s+olduğunu\s+bulurum\b',
    r'\bgörürsün\s+sen\s+gününü\b',
    r'\bağz[ıi]n[ıi]\s+burnunu\s+k[ıi]rar[ıi]m\b',
    r'\bdayak\s+yersin(?:\s+böyle\s+konuşursan)?\b',
    r'\bkarş[ıi]ma\s+ç[ıi]kma\b.{0,40}\bpişman\s+olursun\b',
    r'\bbir\s+daha\s+yazarsan\b.{0,30}\b(?:mahvederim|pişman\s+edersin|pişman\s+olursun)\b',
)

# Harf aralarına boşluk/nokta/tire/alt çizgi/görünmez karakter koyma ve yaygın
# leet biçimleri. Bunlar yalnız tespit/temizlik için kullanılır; kullanıcıya
# gösterilecek metin bu biçime dönüştürülmez.
_OBFUSCATED_INPUT_PATTERNS = (
    r'(?<!\w)s[\W_]*[iı1!][\W_]*k[\W_]*t[\W_]*[iı1!][\W_]*r(?!\w)',
    r'(?<!\w)s[\W_]*[iı1!][\W_]*k[\W_]*[iı1!][\W_]*m(?!\w)',
    r'(?<!\w)a[\W_]*m[\W_]*k(?!\w)',
    r'(?<!\w)y[\W_]*[a4][\W_]*r[\W_]*r[\W_]*[a4][\W_]*k(?!\w)',
    r'(?<!\w)a[\W_]+p[\W_]+t[\W_]+a[\W_]+l(?!\w)',
    r'(?<!\w)s[\W_]+a[\W_]+l[\W_]+a[\W_]+k(?!\w)',
    r'(?<!\w)ş[\W_]+e[\W_]+r[\W_]+e[\W_]+f[\W_]+s[\W_]+i[\W_]+z(?!\w)',
    r'(?<!\w)s[\W_]+e[\W_]+r[\W_]+e[\W_]+f[\W_]+s[\W_]+i[\W_]+z(?!\w)',
)

# Açık saldırı kısaltmasını yalnız bir insan/hedef grubuna bağlandığında ele al.
_TARGETED_ABBREVIATION_PATTERNS = (
    r'\b(?:ilk\s+)?yazanlar[ıi]\b.{0,20}\bskm\b',
    r'\b(?:seni|sizi|hepinizi|onlar[ıi]|bunlar[ıi])\b.{0,20}\bskm\b',
)

# Saldırı kabuğu temizliğinde bütün cümleyi değil, kişi-hedefli parçayı söken
# ek kalıplar. Karma mesajdaki gerçek görüş bu sayede korunur.
_REALWORLD_SHELL_PATTERNS = (
    r'\bcahil\s+cahil\s+konuşma\b[\s,;:.-]*',
    r'\bkudur\s+fanboy\b[\s,;:.-]*',
    r'\bfanboyluk\s+yapma(?:\s+da)?\b[\s,;:.-]*',
    r'\bkafan\s+basm[ıi]yor(?:\s+galiba)?\b[\s,;:.-]*',
    r'\b(?:sen\s+de\s+)?ne\s+boş\s+adams[ıi]n(?:\s+ya)?\b[\s,;:.-]*',
)

_IDEA_TARGET_WORDS = (
    'fikir', 'öneri', 'yöntem', 'tasarım', 'uygulama', 'karar', 'plan',
    'argüman', 'arguman', 'cümle', 'cumle', 'yorum', 'yaklaşım', 'yaklasim',
)


def _is_attack(signals: list[str]) -> bool:
    return bool(_ATTACK_SIGNALS.intersection(signals))


def _unicode_clean(text: str) -> str:
    # Zero-width ve diğer format karakterlerini yalnız tespit görünümünden çıkar.
    return ''.join(ch for ch in text if unicodedata.category(ch) != 'Cf')


def _matches_any(patterns: tuple[str, ...], text: str) -> bool:
    cleaned = _unicode_clean(text.lower().replace('â', 'a'))
    return any(re.search(p, cleaned, flags=re.IGNORECASE | re.DOTALL) for p in patterns)


def _idea_directed_aptalca(engine_module: Any, text: str) -> bool:
    """"Bu fikir aptalca" gibi nesne eleştirisini kişi hakaretinden ayırır."""
    low = _unicode_clean(text.lower())
    if not re.search(r'\baptalca\w*\b', low):
        return False
    if not any(word in low for word in _IDEA_TARGET_WORDS):
        return False
    # Doğrudan ikinci kişi hedefi varsa istisna uygulama.
    if re.search(r'\b(?:sen|siz|sana|seni|senin|sizin)\b', low):
        return False
    # aptalca sözcüğünü çıkarınca başka gerçek saldırı kalıyorsa yine saldırıdır.
    remainder = re.sub(r'\baptalca\w*\b', ' ', low)
    try:
        if engine_module._has_any(engine_module.OFFENSIVE_PATTERNS, remainder):
            return False
        if engine_module._has_any(engine_module.DIRECT_ATTACK_PATTERNS, remainder):
            return False
        if engine_module._has_any(engine_module.THREAT_PATTERNS, remainder):
            return False
    except Exception:
        return False
    return True


def _explicit_evidence_context(text: str) -> bool:
    """Salt 'veri' sözcüğünü kaynak talebi sayma; bağlam/eylem iste."""
    low = _unicode_clean(text.lower())
    explicit = (
        'kaynak', 'kaynağ', 'kanıt', 'araştırma', 'rapor', 'doi', 'http://',
        'https://', 'referans', 'bilimsel çalışma', 'akademik çalışma',
        'çalışmaya göre', 'çalışmada',
    )
    if any(marker in low for marker in explicit):
        return True
    if re.search(r'\bveri(?:yi|leri|lerin|nin|ye)?\b.{0,30}\b(?:paylaş|göster|sun|açıkla|dayan)\w*\b', low):
        return True
    if re.search(r'\b(?:hangi|neredeki|dayandığı)\s+veri\b', low):
        return True
    if re.search(r'\bveriye\s+dayan\w*\b|\bveri\s+var\s+m[ıi]\b|\bverin\s+ne\b', low):
        return True
    return False


def _extra_personal_attack(text: str) -> bool:
    if _matches_any(_REALWORLD_PERSONAL_PATTERNS, text):
        return True
    if _matches_any(_TARGETED_ABBREVIATION_PATTERNS, text):
        return True
    if _matches_any(_OBFUSCATED_INPUT_PATTERNS, text):
        return True
    return False


def _extra_threat(text: str) -> bool:
    return _matches_any(_REALWORLD_THREAT_PATTERNS, text)


def _is_pure_attack(engine_module: Any, original: str, signals: list[str]) -> bool:
    """Gerçek tartışılabilir içerik sinyali taşımayan saldırıyı ayırır."""
    if not _is_attack(signals):
        return False
    if _SUBSTANTIVE_SIGNALS.intersection(signals):
        return False
    try:
        if engine_module._ban_stance(original) != 'none':
            return False
    except Exception:
        pass
    return True


def _malformed_issue(engine_module: Any, original: str, suggestion: str, signals: list[str]) -> str:
    """Yalnız saldırı girdilerindeki görünür biçimde bozuk son çıktıları yakalar."""
    text = (suggestion or '').strip()
    if not text:
        return 'boş çıktı'
    if not _is_attack(signals):
        return ''

    low = engine_module._normalize(text) if hasattr(engine_module, '_normalize') else text.lower()

    try:
        output_signals = list(engine_module.analyze_message(text))
        if _is_attack(output_signals):
            return 'saldırı kalıntısı'
    except Exception:
        pass

    if re.search(r'^(?:(?:sen|siz)\s+)?(?:birisin|birisiniz|birisi|biri)\b', low):
        return 'kırık başlangıç'
    if re.search(r'^(?:senden|sizden|senin|sizin|sana|seni)\b', low):
        return 'kırık başlangıç'
    if re.search(r'\b(?:birisin|birisiniz)\b', low):
        return 'kişisel hitap kalıntısı'
    if re.search(r'\b(?:senden|sizden)\s+daha\s+(?:iyi|kötü|zeki|akıllı|başarılı|mantıklı|değerli)\b', low):
        return 'kişisel karşılaştırma kalıntısı'

    if _is_pure_attack(engine_module, original, signals):
        if re.search(r'\b(?:senden|sizden|senin|sizin)\b', low):
            return 'ikinci kişi kalıntısı'

    if 'soru' in signals and '?' not in text:
        return 'soru niyeti kayboldu'
    if 'sayısal/doğrulanabilir iddia' in signals:
        try:
            compact = text.replace(' ', '')
            for number in engine_module._numbers(original):
                if number.replace(' ', '') not in compact:
                    return 'sayısal bilgi kayboldu'
        except Exception:
            pass

    words = re.findall(r'\b\w+\b', text, flags=re.UNICODE)
    if len(words) < 4 and not text.endswith('?'):
        return 'çok kısa saldırı artığı'

    return ''


def _safe_generic(original: str) -> str:
    low = original.lower()
    if any(x in low for x in ('fikir', 'düşünce', 'görüş', 'yorum')):
        return (
            'Bu görüşü yeterince ikna edici bulmuyorum. '
            'Eleştirimi kişiye değil, ileri sürülen düşüncenin gerekçelerine odaklamak istiyorum.'
        )
    return (
        'Bu görüşe katılmıyorum. '
        'Eleştirimi kişiye değil, ileri sürülen görüşün gerekçelerine odaklamak istiyorum.'
    )


def _fallback(engine_module: Any, original: str, context: str, signals: list[str]) -> str:
    """Bozuk bir ilk çıktı için güvenli ve niyet-koruyan son yedek."""
    try:
        deterministic, _, _ = engine_module._deterministic_rewrite(original, context, signals)
        if not _malformed_issue(engine_module, original, deterministic, signals):
            return deterministic
    except Exception:
        pass

    if 'bağlamı yeniden değerlendirme talebi' in signals:
        return (
            'Yanıtın konuyu yeterince dikkate almadığını düşünüyorum. '
            'Konuyu baştan değerlendirerek yeniden yanıtlayabilir misin?'
        )

    if 'konuya katkı eleştirisi' in signals:
        return (
            'Yorumunun tartışmanın konusuna yeterince katkı sağlamadığını düşünüyorum. '
            'Konuyla ilgili görüşünü daha somut biçimde açıklayabilir misin?'
        )

    if 'kaynak/kanıt vurgusu' in signals:
        return 'Bu iddianın dayanağını değerlendirebilmek için kullandığın kaynak veya kanıtı paylaşabilir misin?'

    if 'soru' in signals:
        try:
            clean = engine_module._strip_attack_shell(original)
            clean = re.sub(r'^\s*(?:m[ıi]s[ıi]n|misin|musun|müsün)\b[ ,;:-]*', '', clean, flags=re.IGNORECASE)
            if len(clean.split()) >= 3:
                candidate = engine_module._question_sentence(clean)
                if not _malformed_issue(engine_module, original, candidate, signals):
                    return candidate
        except Exception:
            pass

    if 'sayısal/doğrulanabilir iddia' in signals:
        try:
            candidate = engine_module._numeric_claim_rewrite(original)
            if not _malformed_issue(engine_module, original, candidate, signals):
                return candidate
        except Exception:
            pass

    return _safe_generic(original)


def _ai_repair(engine_module: Any, original: str, bad_candidate: str, context: str, signals: list[str]) -> str:
    """Yalnız bozuk çıktıda, bellekte hazır yerel modeli ikinci hakem yapar."""
    try:
        status = engine_module.status(load=False)
        if not status.get('loaded'):
            return ''
        model = getattr(engine_module, '_MODEL', None)
        tokenizer = getattr(engine_module, '_TOKENIZER', None)
        if model is None or tokenizer is None:
            return ''

        import torch

        system_prompt = (
            "Sen N-KÖPRÜ Yanıt Koçu için son kalite hakemisin. Sana özgün mesaj ve hatalı olabilecek bir öneri verilecek. "
            "Hakaret, kişisel aşağılama, tehdit ve kırık cümle bırakma. Özgün mesajdaki gerçek görüşü, soruyu, sayıları, "
            "kaynak talebini ve yönü koru; olmayan yeni fikir ekleme. Salt hakaret varsa yeni iddia uydurma, eleştiriyi görüş ve gerekçe eksenine taşı. "
            "En fazla iki doğal Türkçe cümle yaz. Yalnızca nihai öneriyi döndür."
        )
        user_prompt = (
            f'Konu: {context.strip() or "Belirtilmedi"}\n'
            f'Sinyaller: {", ".join(signals)}\n'
            f'Özgün mesaj: {original}\n'
            f'İlk öneri: {bad_candidate}'
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors='pt',
        ).to(model.device)
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=min(64, int(getattr(engine_module, 'MAX_NEW_TOKENS', 48)) + 16),
                do_sample=False,
                repetition_penalty=1.12,
                no_repeat_ngram_size=3,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = outputs[0][inputs['input_ids'].shape[-1]:]
        candidate = tokenizer.decode(generated, skip_special_tokens=True)
        if hasattr(engine_module, '_clean_generation'):
            candidate = engine_module._clean_generation(candidate)
        candidate = candidate.strip()
        if not candidate or _malformed_issue(engine_module, original, candidate, signals):
            return ''

        valid, _ = engine_module._candidate_valid(original, candidate, signals)
        return candidate if valid else ''
    except Exception:
        return ''


def install(engine_module: Any) -> None:
    """Yanıt Koçu üzerine idempotent gerçek-dünya + son kalite kapılarını kurar."""
    if getattr(engine_module, '_N_KOPRU_FINAL_GUARD_INSTALLED', False):
        return

    original_analyze = engine_module.analyze_message
    original_strip = engine_module._strip_attack_shell
    original_rewrite = engine_module.rewrite_with_ai

    def guarded_analyze_message(text: str) -> list[str]:
        signals = list(original_analyze(text))

        # "Bu fikir aptalca" gibi kişi değil nesne/fikir hedefli kullanımda
        # OFFENSIVE_PATTERNS içindeki geniş aptal\w* eşleşmesini geri al.
        if _idea_directed_aptalca(engine_module, text):
            signals = [s for s in signals if s != 'hakaret/küfür']

        if _extra_personal_attack(text):
            if 'kişiye yönelik saldırı' not in signals:
                signals.append('kişiye yönelik saldırı')

        if _extra_threat(text):
            if 'tehdit/şiddet' not in signals:
                signals.append('tehdit/şiddet')

        # Ana motor 'veri' sözcüğünü genel evidence marker olarak kullanıyor.
        # "veri kaybı/güvenliği/tabanı" gibi içeriklerde kaynak talebi yoksa bu
        # sinyali kaldır; gerçek kaynak/araştırma/veri isteme kalıpları korunur.
        if 'kaynak/kanıt vurgusu' in signals and not _explicit_evidence_context(text):
            signals = [s for s in signals if s != 'kaynak/kanıt vurgusu']

        # original_analyze yalnız nötr sinyal üretmişse ve biz saldırı eklediysek
        # nötr etiketi birlikte taşımak gereksiz/yanıltıcıdır.
        if _is_attack(signals) and 'nötr/bağlamsal ifade' in signals:
            signals = [s for s in signals if s != 'nötr/bağlamsal ifade']
        return signals or ['nötr/bağlamsal ifade']

    def guarded_strip_attack_shell(text: str) -> str:
        cleaned = text
        # Önce yeni karma-saldırı kalıplarını sök; böylece gerçek konu cümlesi
        # ana motorun mevcut temizleyicisine sağlam biçimde ulaşır.
        for pattern in _REALWORLD_SHELL_PATTERNS:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE | re.DOTALL)

        # Yeni kişi-hedefli kısa kalıplar ve tehditler tamamen kabuk sayılır.
        for pattern in (*_REALWORLD_PERSONAL_PATTERNS, *_REALWORLD_THREAT_PATTERNS, *_TARGETED_ABBREVIATION_PATTERNS):
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE | re.DOTALL)

        # Obfuscation regexleri özgün metin üzerinde çalışır; sıralama önemlidir.
        for pattern in _OBFUSCATED_INPUT_PATTERNS:
            cleaned = re.sub(pattern, ' ', _unicode_clean(cleaned), flags=re.IGNORECASE | re.DOTALL)

        cleaned = original_strip(cleaned)
        cleaned = re.sub(r'^\s*(?:ya|yahu|ulan|lan|be|galiba)\b[ ,;:-]*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,;:.-!?')
        return cleaned

    # Global fonksiyonları rewrite çağrısından önce değiştiriyoruz; Python'da
    # mevcut rewrite fonksiyonu bu isimleri çalışma anında modülden çözer.
    engine_module.analyze_message = guarded_analyze_message
    engine_module._strip_attack_shell = guarded_strip_attack_shell

    def guarded_rewrite_with_ai(text: str, context: str = '', use_ai: bool = True) -> dict[str, Any]:
        result = dict(original_rewrite(text, context=context, use_ai=use_ai))
        original = text.strip()
        if not original:
            return result

        signals = list(result.get('signals') or engine_module.analyze_message(original))
        if not _is_attack(signals):
            return result

        suggestion = str(result.get('suggestion') or '').strip()
        issue = _malformed_issue(engine_module, original, suggestion, signals)
        if not issue:
            return result

        repaired = _ai_repair(engine_module, original, suggestion, context, signals) if use_ai else ''
        if repaired:
            result['suggestion'] = repaired
            result['engine'] = 'quality-guard-ai'
            result['reason'] = (
                'Son kalite denetimi ilk öneride anlam/anlatım sorunu buldu; '
                'yerel AI hakemi öneriyi yeniden yazdı ve güvenlik kontrollerinden geçirdi.'
            )
            return result

        safe = _fallback(engine_module, original, context, signals)
        if _malformed_issue(engine_module, original, safe, signals):
            safe = _safe_generic(original)

        result['suggestion'] = safe
        result['engine'] = 'quality-guard-safe'
        result['reason'] = (
            f'Son kalite denetimi ilk öneriyi reddetti ({issue}); '
            'kırık veya kişiselleştirilmiş ifade kullanıcıya gösterilmeden güvenli yeniden yazım kullanıldı.'
        )
        return result

    engine_module.rewrite_with_ai = guarded_rewrite_with_ai
    engine_module._N_KOPRU_FINAL_GUARD_INSTALLED = True
