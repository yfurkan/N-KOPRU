"""N-KÖPRÜ v0.4.4 - Yanıt Koçu (ironi + dengeli görüş).

Amaç:
- kullanıcının ana görüşünü ve somut içeriğini korumak,
- kişisel saldırı/küfrü temizlemek,
- soru, sayı, kaynak talebi ve koşullu görüşleri kaybetmemek,
- zaten yapıcı olan mesajı gereksiz yere değiştirmemek,
- küçük üretken modelin hatalı/konu dışı üretimini kullanıcıya göstermemek,
- yüksek güvenli durumları milisaniyelik güvenli katmanda çözerek CPU gecikmesini azaltmak.

Üretken model yalnızca yüksek güvenli kuralların kapsamadığı belirsiz saldırı/ifade
vakalarında aday üretir. Aday, anlam ve güvenlik denetimlerinden geçmezse reddedilir.

Varsayılan üretken model: Qwen/Qwen2.5-0.5B-Instruct
"""
from __future__ import annotations

import importlib.util
import os
import re
import time
from typing import Any

MODEL_NAME = os.getenv('N_KOPRU_COACH_MODEL', 'Qwen/Qwen2.5-0.5B-Instruct')
MAX_NEW_TOKENS = int(os.getenv('N_KOPRU_COACH_MAX_NEW_TOKENS', '48'))
USE_FAST_PATH = os.getenv('N_KOPRU_COACH_FAST_PATH', '1').strip().lower() not in {'0', 'false', 'off', 'no'}

# Açık ironi/sarkazm kalıpları. Amaç literal cümleyi 'yapıcı' diye aynen bırakmamak.
# Liste özellikle güçlü ve düşük yanlış-pozitifli kalıplarla sınırlıdır.
IRONY_PATTERNS = [
    r'\bgüya\b',
    r'\bsanki\b.{0,100}\b(?:tek\s+çözüm|bütün\s+sorun|tüm\s+sorun|her\s+şey\s+çöz)\w*\b',
]

BALANCE_CONTEXT_MARKERS = (
    'dersin türüne göre', 'derse göre', 'duruma göre', 'bağlama göre', 'belirli koşullarda',
    'belirli şartlarda', 'koşula göre', 'şartıyla', 'farklı kurallar', 'kontrollü kullanım',
)

_MODEL = None
_TOKENIZER = None
_DEVICE = 'cpu'
_LOAD_ERROR: str | None = None

# Kişiye yöneltilen hakaret/küfür çekirdeği. Regexler Türkçe ek almış biçimleri de yakalar.
OFFENSIVE_PATTERNS = [
    r'\bmal\s*beyinli\w*\b', r'\byavşak\w*\b', r'\bgerizek[aâ]l[ıi]\w*\b', r'\bgeri\s*zek[aâ]l[ıi]\w*\b',
    r'\baptal\w*\b', r'\bsalak\w*\b', r'\bbeyinsiz\w*\b', r'\bahmak\w*\b', r'\bembesil\w*\b',
    r'\bdangalak\w*\b', r'\bşerefsiz\w*\b', r'\bmoron\w*\b', r'\bpezevenk\w*\b',
    r'\bsiktir\w*\b', r'\bsikerim\b', r'\bsikeyim\b', r'\bsiktim\b', r'\borospu\w*\b', r'\bpiç\w*\b', r'\bamk\b', r'\baq\b',
    r'\bgötünden\w*\b', r'\bgöt(?:ün|ünü|üne|ünden|ü|e|ten)?\b', r'\bmal\s+m[ıi]s[ıi]n\b', r'\bmal(?:sın|sin)\b', r'\bcahil\w*\b', r'\bzeka\s*özürlü\w*\b', r'\bzek[aâ]\s*özürlü\w*\b',
]

# Hakaret kelimesi içermese de kişiyi hedefleyen kalıplar.
DIRECT_ATTACK_PATTERNS = [
    r'\bsen\b.{0,45}\banlamıyorsun\b', r'\bsen\b.{0,45}\bbilmiyorsun\b', r'\bbilgin(?:\s+(?:bile|de|da))?\s+yok\b',
    r'\bhiçbir\s+şey\s+anlamıyorsun\b', r'\bhiçbir\s+şey\s+bilmiyorsun\b',
    r'\bboş\s+boş\s+konuş\w*\b', r'\bboş\s+konuş\w*\b', r'\bsaçmal\w*\b', r'\buydur\w*\b',
    r'\byoksa\s+sus\b', r'\bsadece\s+konuş\w*\b', r'\bçeneni\s+kapat\w*\b',
    r'\bkafanı\s+kullan\w*\b', r'\bkafan\s+basmıyor\b', r'\bkafanı\s+çalıştır\w*\b', r'\baklın\s+yok\b', r'\bokumayı\s+bilmiyor\w*\b', r'\bokuduğunu\s+anlamıyor\w*\b',
    r'\bkonuyu\s+(?:en\s+)?baştan\s+oku\w*\b', r'\bönce\s+konuyu\s+oku\w*\b',
    r'\bkonuyu\s+okumamış\w*\b', r'\bkonuyu\s+anlamamış\w*\b', r'\bkonuyu\s+anlamadan\b',
    r'\bbey\w*\b.{0,25}\bev\w*\b.{0,25}\bunut\w*\b',
]

DISAGREEMENT_MARKERS = (
    'katılmıyorum', 'karşıyım', 'yanlış', 'yasak', 'yasaklan', 'sorun', 'zarar', 'gereksiz',
    'kısıtlan', 'sınırlandır', 'ama', 'ancak', 'çözüm değil', 'doğru değil', 'olmamalı', 'istemiyorum'
)
SUPPORT_MARKERS = (
    'katılıyorum', 'destekliyorum', 'faydalı', 'yararlı', 'doğru', 'kullanılsın', 'serbest',
    'mantıklı', 'uygun'
)
EVIDENCE_MARKERS = (
    'kaynak', 'kaynağ', 'kanıt', 'veri', 'araştırma', 'rapor', 'doi', 'http://', 'https://', 'referans', 'bilimsel çalışma', 'akademik çalışma', 'çalışmaya göre', 'çalışmada'
)
SOURCE_ACCUSATION_MARKERS = (
    'uydur', 'götünden bilgi', 'götünden bilgiler', 'kaynaklarınla gel', 'kaynakla gel',
    'kaynağın ne', 'kaynağı ne', 'kaynağı nedir', 'kanıtın ne', 'verin ne', 'bilgi üretip durma',
    'kaynak göstermeden', 'kaynak göster', 'kanıt göster'
)
CONTRIBUTION_CRITICISM_MARKERS = (
    'gereksiz yorum', 'konuyla alakalı', 'konuyla ilgili', 'yorumun yok', 'katkı sağlam',
    'sadece konuş', 'nereye varmayı', 'boş konuş', 'konuya katkı', 'konudan sap', 'alakasız yorum'
)
CONTEXT_REVIEW_ATTACK_MARKERS = (
    'konuyu en baştan oku', 'konuyu baştan oku', 'önce konuyu oku', 'konuyu oku da', 'konuyu okumamış',
    'konuyu anlamamış', 'konuyu anlamadan', 'beynini evde unut', 'beynini de evde unut',
    'cevabın konuyla alakasız', 'yanıtın konuyla alakasız', 'soruyu oku da', 'mesajı oku da'
)
EXPERTISE_ATTACK_MARKERS = (
    'hiçbir şey anlamıyorsun', 'hiçbir şey bilmiyorsun', 'bilgin yok', 'bilgin bile yok', 'bilgin de yok', 'bu konudan anlamıyorsun',
    'bu konuda bir bilgin yok', 'konuyu bilmiyorsun', 'anlamıyorsun', 'bilmiyorsun', 'kafan basmıyor',
    'aklın yok', 'okumayı bilmiyor', 'okuduğunu anlamıyor'
)
PROMPT_LEAK_MARKERS = (
    'tartışma konusu:', 'iletişim sinyalleri:', 'özgün mesaj:', 'yeniden yazılmış yanıt:',
    'sen n-köprü', 'göre bir mesaj yazmak için', 'system prompt', 'user prompt',
    'bir yazar olmanızı öneririm', 'yanıtını kontrol etmenizi öneririm', 'assistant:', 'system:'
)

TR_FOLD = str.maketrans({'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u'})
STOPWORDS = {
    'acaba', 'ama', 'ancak', 'artık', 'bana', 'bence', 'ben', 'bile', 'bir', 'biraz', 'biz',
    'bu', 'bunu', 'bunun', 'burada', 'da', 'daha', 'de', 'diye', 'en', 'gibi', 'hem', 'her',
    'hiç', 'icin', 'ile', 'ise', 'ki', 'mı', 'mi', 'mu', 'mü', 'ne', 'neden', 'nasıl', 'o',
    'olan', 'olarak', 'olduğunu', 'sadece', 'sen', 'siz', 'şey', 'şu', 've', 'veya', 'ya',
    'yani', 'yerine', 'yok', 'çok', 'kadar', 'gerçekten', 'konuda', 'konuyu', 'konuyla',
}

# Saldırı kabuğunu çıkarırken tüm ana içeriği silmemek için yalnız yüksek güvenli kalıplar.
ATTACK_SHELL_PATTERNS = [
    r'\b(?:aptal|salak|mal|gerizek[aâ]l[ıi]|ahmak)\s+m[ıi]s[ıi]n\b',
    *OFFENSIVE_PATTERNS,
    r'\bsen\s+bu\s+konudan\s+hiçbir\s+şey\s+anlamıyorsun\b',
    r'\bsen\b.{0,45}\banlamıyorsun\b', r'\bsen\b.{0,45}\bbilmiyorsun\b',
    r'\bhiçbir\s+şey\s+anlamıyorsun\b', r'\bhiçbir\s+şey\s+bilmiyorsun\b', r'\bbilgin\s+yok\b',
    r'\bboş\s+boş\s+konuş\w*\b', r'\bboş\s+konuş\w*\b', r'\buydur\w*(?:\s+durma|\s+dur)?\b', r'\bsaçmal\w*\b', r'\byoksa\s+sus\b',
    r'\bsiktir\s+git\w*\b', r'\bçeneni\s+kapat\w*\b', r'\bkafanı\s+kullan\w*\b',
    r'\bkafan\s+basmıyor\b', r'\bkafanı\s+çalıştır\w*\b', r'\baklın\s+yok\b',
    r'\bokumayı\s+bilmiyor\w*\b', r'\bokuduğunu\s+anlamıyor\w*\b',
    r'\bbeynini\s+(?:de\s+)?evde\s+unut\w*\b',
]


def dependencies_installed() -> bool:
    return importlib.util.find_spec('transformers') is not None and importlib.util.find_spec('torch') is not None


def load_model():
    global _MODEL, _TOKENIZER, _DEVICE, _LOAD_ERROR
    if _MODEL is not None and _TOKENIZER is not None:
        return _MODEL, _TOKENIZER
    if not dependencies_installed():
        _LOAD_ERROR = 'torch/transformers kurulu değil; Yanıt Koçu güvenli hibrit yedekle çalışacak.'
        return None, None

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        use_cuda = bool(torch.cuda.is_available())
        _DEVICE = 'cuda' if use_cuda else 'cpu'
        if not use_cuda:
            try:
                torch.set_num_threads(min(8, max(1, os.cpu_count() or 4)))
            except Exception:
                pass

        _TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
        _MODEL = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype='auto')
        _MODEL.to(_DEVICE)
        _MODEL.eval()
        _LOAD_ERROR = None
        return _MODEL, _TOKENIZER
    except Exception as exc:
        _LOAD_ERROR = f'{type(exc).__name__}: {exc}'
        _MODEL = None
        _TOKENIZER = None
        return None, None


def status(load: bool = False) -> dict[str, Any]:
    if load:
        load_model()
    installed = dependencies_installed()
    loaded = _MODEL is not None and _TOKENIZER is not None
    if loaded:
        mode = 'generative-coach'
        message = 'Yanıt Koçu hazır: hızlı anlam-koruma katmanı + denetimli üretken AI.'
    elif installed:
        mode = 'coach-ready'
        message = 'AI paketleri kurulu; hızlı güvenli Yanıt Koçu hazır, üretken model henüz belleğe yüklenmedi.'
    else:
        mode = 'coach-fallback'
        message = 'Bağlama duyarlı güvenli Yanıt Koçu hazır; üretken AI paketleri bulunamadı.'
    return {
        'installed': installed,
        'loaded': loaded,
        'model': MODEL_NAME,
        'device': _DEVICE,
        'mode': mode,
        'message': message,
        'error': _LOAD_ERROR,
    }


def _has_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE | re.DOTALL) for p in patterns)


def _normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text.lower().replace('â', 'a')).strip()


def _fold(text: str) -> str:
    return _normalize(text).translate(TR_FOLD)


def _sentence(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip(' ,;:-')
    if not text:
        return ''
    text = text[0].upper() + text[1:]
    if text[-1] not in '.!?':
        text += '.'
    return text


def _question_sentence(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip(' ,;:-.?!')
    if not text:
        return ''
    text = text[0].upper() + text[1:]
    return text + '?'


def _numbers(text: str) -> list[str]:
    return re.findall(r'%\s?\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\b', text)


def _protected_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    patterns = [r'https?://\S+', r'@[\w.]+', r'#[\wçğıöşüÇĞİÖŞÜ]+', r'\b[A-ZÇĞİÖŞÜ]{2,8}\b']
    for p in patterns:
        for item in re.findall(p, text):
            if item not in tokens:
                tokens.append(item)
    return tokens




def _is_numeric_claim(text: str) -> bool:
    """Her sayı kaynak gerektiren iddia değildir; saat/tarih/komut gibi sayıları ayırır."""
    t = _normalize(text)
    if re.search(r'%\s?\d+(?:[.,]\d+)?', t):
        return True
    if not re.search(r'\b\d+(?:[.,]\d+)?\b', t):
        return False

    # Salt saat, tarih, sıra, sürüm veya kişisel plan ifadelerini istatistik iddiası sayma.
    if re.search(r'\b(?:saat|saatte|saatinde)\s*\d+', t) or re.search(r'\b\d{1,2}[:.]\d{2}\b', t):
        return False
    if re.search(r'\bv?\d+\.\d+(?:\.\d+)?\b', t):
        return False

    statistic_nouns = (
        'öğrenci', 'katılımcı', 'kişi', 'kullanıcı', 'oran', 'yüzde', 'puan', 'oy', 'anket',
        'araştırma', 'veri', 'sonuç', 'başarı', 'başarısız', 'vaka', 'yorum', 'kez', 'defa'
    )
    claim_verbs = (
        'kullandı', 'kullanmış', 'katıldı', 'tercih etti', 'arttı', 'azaldı', 'düştü', 'yükseldi',
        'başardı', 'oldu', 'vardı', 'bulunuyor', 'tespit edildi', 'gösterdi', 'bildirdi', 'oy verdi'
    )
    return any(x in t for x in statistic_nouns) or any(x in t for x in claim_verbs)

def _marker_present(text: str, marker: str) -> bool:
    """Kısa bağlaçların başka kelimelerin içinde yanlış eşleşmesini engeller."""
    token_only = {
        'ama', 'ancak', 'yanlış', 'sorun', 'zarar', 'gereksiz', 'faydalı', 'yararlı',
        'doğru', 'serbest', 'mantıklı', 'uygun', 'veri', 'rapor', 'doi', 'referans'
    }
    if marker in token_only:
        return re.search(r'(?<!\w)' + re.escape(marker) + r'(?!\w)', text, flags=re.IGNORECASE) is not None
    return marker in text


def _any_marker(text: str, markers: tuple[str, ...]) -> bool:
    return any(_marker_present(text, m) for m in markers)


def _is_sarcastic(text: str) -> bool:
    """Yalnız güçlü/örtüşen ironi işaretlerini işaretler; sıradan övgü veya 'tabii ki'yi yakalamaz."""
    t = _normalize(text)
    if _has_any(IRONY_PATTERNS, t):
        return True

    cue = any(re.search(r'(?<!\w)' + re.escape(x) + r'(?!\w)', t) for x in ('aynen', 'zaten', 'bravo'))
    cue = cue or any(x in t for x in ('tabii canım', 'tabi canım', 'çok mantıklı gerçekten', 'ne kadar mantıklı', 'ne kadar zekice'))
    absurd = any(x in t for x in ('sihirli', 'mucizevi'))
    absolute = any(x in t for x in ('bütün sorun', 'tüm sorun', 'her şey çöz', 'tek çözüm', 'kesin çöz'))

    # "Kaynak vermeden konuşmak çok güvenilir" gibi içsel çelişkili alaylar.
    source_without = any(x in t for x in ('kaynak vermeden', 'kaynak göstermeden', 'kaynaksız'))
    source_praise = any(x in t for x in ('güvenilir', 'bilimsel', 'sağlam veri', 'çok doğru'))
    if source_without and source_praise and (cue or 'gerçekten' in t):
        return True

    # "Herkesi susturunca tartışma çok kaliteli olacak" gibi tartışma amacına ters övgüler.
    silence = any(x in t for x in ('sustur', 'konuşmasın', 'çeneyi kapat'))
    quality_praise = any(x in t for x in ('kaliteli', 'nitelikli', 'harika', 'mükemmel'))
    if silence and quality_praise and (cue or 'zaten' in t):
        return True

    # Yasak/tek çözüm gibi mutlak sonuçlarda en az iki örtüşen ipucu isteriz.
    weak_count = int(cue) + int(absurd) + int('zaten' in t) + int('tabii canım' in t or 'tabi canım' in t)
    return absolute and weak_count >= 2


def _is_balanced_view(text: str) -> bool:
    """Koşullu/ara pozisyonu salt 'destek' veya salt 'itiraz' diye etiketlememek için."""
    t = _normalize(text)
    if _ban_stance(text) == 'conditional':
        return True
    if any(m in t for m in BALANCE_CONTEXT_MARKERS):
        return True

    contrast = any(re.search(r'(?<!\w)' + re.escape(x) + r'(?!\w)', t) for x in ('ama', 'ancak', 'fakat'))
    positive = _any_marker(t, SUPPORT_MARKERS) or any(x in t for x in ('izin veril', 'serbest bırak'))
    limiting = _any_marker(t, DISAGREEMENT_MARKERS) or any(x in t for x in (
        'kural olmalı', 'kurallar olmalı', 'kabul edilmesin', 'kaynak göstermeden',
        'yalnızca', 'sadece belirli', 'sınavlarda kullanılmamalı',
    ))
    return contrast and positive and limiting


def _sarcasm_rewrite(text: str, context: str, signals: list[str]) -> tuple[str, str, bool]:
    """Güçlü ironi kalıplarını literal okumak yerine güvenli, doğrudan niyete çevirir."""
    t = _normalize(text)
    obj, usage_subject = _ban_subject(text, context)

    # Yasaklama ile her şeyin çözüleceğini alaycı biçimde söyleyen kalıp -> yasak tek başına çözüm değil.
    if any(k in t for k in ('yasak', 'yasakla')) and any(k in t for k in ('çöz', 'hallol', 'bitecek', 'sorun')):
        return (
            f'{obj} yasaklamanın tek başına bütün sorunları çözeceğini düşünmüyorum.',
            'sarcasm-anti-ban', True,
        )

    # Kaynaksızlığın 'çok güvenilir' olduğuna dair alay -> doğrudan kaynak eleştirisi.
    if _any_marker(t, EVIDENCE_MARKERS) or any(x in t for x in ('kaynaksız', 'kaynak vermeden', 'kaynak göstermeden')):
        return (
            'Kaynak gösterilmeden paylaşılan bilgilerin yeterince güvenilir olduğunu düşünmüyorum. '
            'İddiaların dayandığı kaynakları paylaşabilir misin?',
            'sarcasm-source', True,
        )

    # Susturmanın kaliteyi artıracağına dair alaycı kalıp.
    if any(x in t for x in ('sustur', 'çeneyi kapat', 'konuşmasın')):
        return (
            'Katılımcıları susturmanın tartışmayı daha nitelikli hâle getireceğini düşünmüyorum.',
            'sarcasm-silencing', True,
        )

    # Güçlü ironi saptandı ama semantik aile kesin değilse üretken aday denenebilir.
    # Güvenli yedek, literal övgüyü tekrar etmek yerine değerlendirme talebine döner.
    return (
        'Bu yaklaşımın gerçekten etkili olduğundan emin değilim. Gerekçelerini daha açık tartışmayı tercih ederim.',
        'sarcasm-generic', False,
    )


def analyze_message(text: str) -> list[str]:
    t = _normalize(text)
    signals: list[str] = []
    if _has_any(OFFENSIVE_PATTERNS, t):
        signals.append('hakaret/küfür')
    if _has_any(DIRECT_ATTACK_PATTERNS, t):
        signals.append('kişiye yönelik saldırı')
    if _is_sarcastic(text):
        signals.append('ironi/sarkazm')
    if '?' in text:
        signals.append('soru')
    if _is_numeric_claim(text):
        signals.append('sayısal/doğrulanabilir iddia')

    balanced = _is_balanced_view(text)
    if balanced:
        signals.append('koşullu/dengeli görüş')
    else:
        if _any_marker(t, DISAGREEMENT_MARKERS):
            signals.append('görüş ayrılığı/itiraz')
        if _any_marker(t, SUPPORT_MARKERS):
            signals.append('destek/olumlu görüş')

    if _any_marker(t, EVIDENCE_MARKERS) or any(m in t for m in SOURCE_ACCUSATION_MARKERS):
        signals.append('kaynak/kanıt vurgusu')
    if any(m in t for m in CONTRIBUTION_CRITICISM_MARKERS):
        signals.append('konuya katkı eleştirisi')
    if any(m in t for m in CONTEXT_REVIEW_ATTACK_MARKERS):
        signals.append('bağlamı yeniden değerlendirme talebi')
    if len(text.split()) <= 5:
        signals.append('çok kısa ifade')
    return signals or ['nötr/bağlamsal ifade']


def _strip_attack_shell(text: str) -> str:
    cleaned = text
    for pattern in ATTACK_SHELL_PATTERNS:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE | re.DOTALL)
    # Tek başına kalan saldırı emirlerini ve hitap kırıntılarını temizle.
    cleaned = re.sub(r'\b(?:sus|saçmalama|kes sesini)\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+([,.;!?])', r'\1', cleaned)
    cleaned = re.sub(r'([,;])\s*([,;])+', r'\1', cleaned)
    cleaned = re.sub(r'^\s*(?:ya|yahu|ulan|lan|be)\b[ ,;:-]*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,;:-')
    return cleaned


def _ban_stance(text: str) -> str:
    """Yasaklama/kısıtlama eksenindeki ana niyeti mümkün olduğunca yönlü çıkarır."""
    t = _normalize(text)
    if not any(k in t for k in ('yasak', 'kısıt', 'sınır', 'serbest', 'kullan')):
        return 'none'

    permission = any(k in t for k in ('serbest', 'kullanılsın', 'kullanılabilir', 'izin veril', 'yasaklanmamalı', 'yasaklamak yanlış'))
    restriction = any(k in t for k in ('kısıt', 'sınır', 'kural', 'yasak', 'kabul edilmesin', 'kaynak göstermeden', 'kaynak vermeden'))
    contrast = any(re.search(r'(?<!\w)' + re.escape(k) + r'(?!\w)', t) for k in ('ama', 'ancak', 'fakat'))

    conditional = (
        ('tamamen' in t and ('yanlış' in t or 'doğru değil' in t or 'çözüm değil' in t)
         and any(k in t for k in ('ama', 'ancak', 'fakat', 'sınav', 'kısıt', 'sınır')))
        or ('kontrollü' in t)
        or ('koşul' in t)
        or ('şart' in t and any(k in t for k in ('kullan', 'izin', 'serbest', 'kural')))
        or ('sınav' in t and any(k in t for k in ('kısıt', 'sınır', 'yasak', 'kullanılmamalı')))
        or ('belirli' in t and any(k in t for k in ('sınır', 'kural', 'kısıt', 'koşul')))
        or ('dersin türüne göre' in t)
        or ('derse göre' in t and 'kural' in t)
        or ('farklı kurallar' in t)
        or (contrast and permission and restriction)
    )
    if conditional:
        return 'conditional'

    anti = any(p in t for p in (
        'yasaklamak yanlış', 'yasaklanması yanlış', 'yasaklanmamalı', 'yasaklamayın',
        'tamamen yasaklamak yanlış', 'yasak çözüm değil', 'yasaklamak çözüm değil',
        'kullanın işte', 'kullanılsın', 'serbest olmalı', 'yasaklayıp ne yapacaksınız',
        'yasaklamanın çözüm olduğunu düşünmüyorum', 'yasaklamaya karşıyım'
    ))
    pro = any(p in t for p in (
        'yasaklanmalı', 'yasak olmalı', 'kesinlikle yasak', 'tamamen yasaklan',
        'kullanımı yasak', 'yasaklamak gerekir', 'yasaklanması gerekir'
    ))
    if anti and not pro:
        return 'anti-ban'
    if pro and not anti:
        return 'pro-ban'
    return 'mixed'


def _ban_subject(text: str, context: str) -> tuple[str, str]:
    """(nesne, kullanım-öznesi) döndürür; konu bilinmiyorsa nötr 'bunu/bu kullanım' kullanır."""
    t = _normalize(f'{context} {text}')
    if 'yapay zek' in t:
        return 'Yapay zekâyı', 'Yapay zekâ kullanımının'
    if 'telefon' in t:
        return 'Telefon kullanımını', 'Telefon kullanımının'
    if 'sosyal medya' in t:
        return 'Sosyal medya kullanımını', 'Sosyal medya kullanımının'
    if 'chatgpt' in t:
        return "ChatGPT'yi", "ChatGPT kullanımının"
    return 'Bunu', 'Bunun'


def _source_attack(text: str, signals: list[str]) -> bool:
    t = _normalize(text)
    return 'kaynak/kanıt vurgusu' in signals and (
        'hakaret/küfür' in signals or 'kişiye yönelik saldırı' in signals or any(m in t for m in SOURCE_ACCUSATION_MARKERS)
    )


def _contribution_attack(text: str, signals: list[str]) -> bool:
    t = _normalize(text)
    return 'konuya katkı eleştirisi' in signals and (
        'hakaret/küfür' in signals or 'kişiye yönelik saldırı' in signals or any(m in t for m in CONTRIBUTION_CRITICISM_MARKERS)
    )


def _context_review_attack(text: str, signals: list[str]) -> bool:
    t = _normalize(text)
    return 'bağlamı yeniden değerlendirme talebi' in signals or any(m in t for m in CONTEXT_REVIEW_ATTACK_MARKERS)


def _expertise_attack(text: str, signals: list[str]) -> bool:
    t = _normalize(text)
    return ('kişiye yönelik saldırı' in signals or 'hakaret/küfür' in signals) and any(m in t for m in EXPERTISE_ATTACK_MARKERS)


def _clean_is_already_constructive(text: str, signals: list[str]) -> bool:
    return ('hakaret/küfür' not in signals and 'kişiye yönelik saldırı' not in signals and 'bağlamı yeniden değerlendirme talebi' not in signals and 'ironi/sarkazm' not in signals)


def _numeric_claim_rewrite(text: str) -> str:
    claim = _sentence(_strip_attack_shell(text))
    if not claim:
        claim = _sentence(text)
    if _any_marker(_normalize(claim), EVIDENCE_MARKERS):
        return claim
    return f'{claim} Bu bilginin dayandığı kaynak veya araştırmayı paylaşabilir misin?'


def _deterministic_rewrite(text: str, context: str, signals: list[str]) -> tuple[str, str, bool]:
    """Yüksek güvenli yeniden yazım.

    Returns: (suggestion, decision_tag, high_confidence)
    high_confidence=False ise üretken model aday üretmeye çalışabilir.
    """
    t = text.strip()
    lower = _normalize(t)
    clean = _strip_attack_shell(t)
    stance = _ban_stance(t)
    obj, usage_subject = _ban_subject(t, context)
    has_attack = 'hakaret/küfür' in signals or 'kişiye yönelik saldırı' in signals

    # 0) Zaten yapıcı/temizse: soru ve görüşü aynen koru. Sadece kaynak işareti olmayan
    # açık sayısal iddiaya doğrulama isteği eklenir.
    if _clean_is_already_constructive(t, signals):
        if 'sayısal/doğrulanabilir iddia' in signals and 'soru' not in signals and 'kaynak/kanıt vurgusu' not in signals:
            return _numeric_claim_rewrite(t), 'numeric-evidence', True
        return t, 'preserve-clean', True

    # 1) Açık ironi/sarkazm: literal olumlu ifadeyi gerçek niyet sanma.
    if 'ironi/sarkazm' in signals:
        return _sarcasm_rewrite(t, context, signals)

    # 2) Yasaklama/kısıtlama ekseni: saldırı kabuğunu at, yönü asla tersine çevirme.
    if stance == 'conditional':
        if 'sınav' in lower:
            return (
                f'{obj} tamamen yasaklamanın doğru olmadığını düşünüyorum; ancak sınavlarda kullanımının '
                'sınırlandırılması gerektiği görüşündeyim.',
                'stance-conditional-exam', True,
            )
        return (
            f'{obj} tamamen yasaklamanın doğru olmadığını düşünüyorum; ancak belirli koşullarda kullanımının '
            'sınırlandırılması gerektiği görüşündeyim.',
            'stance-conditional', True,
        )

    if stance == 'anti-ban':
        return (
            f'{obj} yasaklamanın çözüm olduğunu düşünmüyorum; kullanımına izin verilmesi gerektiği görüşündeyim.',
            'stance-anti-ban', True,
        )

    if stance == 'pro-ban':
        return (
            f'{usage_subject} sınırlandırılması veya yasaklanması gerektiğini düşünüyorum. '
            'Bu görüşü gerekçeler üzerinden tartışmak daha yararlı olur.',
            'stance-pro-ban', True,
        )

    # 2) Bağlamı okumama/anlamama hakareti: eleştirinin hedefini koru, kişiselleştirmeyi at.
    if _context_review_attack(t, signals):
        return (
            'Yanıtın konuyu yeterince dikkate almadığını düşünüyorum. Konuyu baştan değerlendirerek yeniden yanıtlayabilir misin?',
            'context-review', True,
        )

    # 3) Sayısal iddia saldırı içerse bile sayı kaybolamaz; saldırıyı temizle ve doğrulama iste.
    if 'sayısal/doğrulanabilir iddia' in signals and 'soru' not in signals:
        return _numeric_claim_rewrite(t), 'numeric-evidence', True

    # 4) Kaynak/kanıt eleştirisi.
    if _source_attack(t, signals):
        # Soru zaten açık bir kaynak sorusu taşıyorsa özünü doğrudan koru.
        if '?' in t and clean and _any_marker(_normalize(clean), EVIDENCE_MARKERS):
            q = clean
            # Hakaret kalıntıları çıkınca baştaki anlamsız bağlaçları temizle.
            q = re.sub(r'^\s*(?:peki|ama|ve)\s+', '', q, flags=re.IGNORECASE)
            return _question_sentence(q), 'source-question', True
        return (
            'Paylaşılan bilgilerin yeterince kaynakla desteklenmediğini düşünüyorum. '
            'İddiaları dayandıkları kaynaklarla birlikte paylaşabilir misin?',
            'source-criticism', True,
        )

    # 5) Hem konuya katkı hem bilgi/gerekçe eksikliği eleştirisi varsa iki niyeti birlikte koru.
    if _contribution_attack(t, signals) and _expertise_attack(t, signals):
        return (
            'Bu konuda paylaştığın görüşün yeterince bilgi veya gerekçeyle desteklenmediğini düşünüyorum. '
            'Görüşünü daha somut bilgi ya da gerekçelerle açıklayabilir misin?',
            'contribution-expertise', True,
        )

    # 6) Konuya katkı sağlamama eleştirisi.
    if _contribution_attack(t, signals):
        return (
            'Yorumunun tartışmanın konusuna yeterince katkı sağlamadığını düşünüyorum. '
            'Konuyla ilgili görüşünü daha somut biçimde açıklayabilir misin?',
            'contribution-criticism', True,
        )

    # 5) Bilgi/anlayışa yönelik kişisel saldırı.
    if _expertise_attack(t, signals):
        return (
            'Bu görüşün gerekçesini yeterince ikna edici bulmuyorum. '
            'Dayandığın bilgi, örnek veya gerekçeleri daha açık paylaşabilir misin?',
            'expertise-attack', True,
        )

    # 7) Saldırı içeren ama içinde gerçek bir soru kalan mesaj.
    if 'soru' in signals and clean:
        q = clean
        # "mısın" gibi hakaret sorusundan kalan anlamsız parçalara karşı kısa temizlik.
        q = re.sub(r'^\s*(?:m[ıi]s[ıi]n|misin|musun|müsün)\b[ ,;:-]*', '', q, flags=re.IGNORECASE)
        if len(q.split()) >= 3:
            return _question_sentence(q), 'question-sanitized', True

    # 8) Geriye anlamlı bir içerik kaldıysa içerik omurgasını koru. Bu dalda model ancak
    # temizlenmiş cümle çok kırık/çok kısa ise devreye girebilir.
    if has_attack and clean:
        clean = re.sub(r'^\s*(?:ama|ancak|ve|ya)\s+', '', clean, flags=re.IGNORECASE)
        if len(clean.split()) >= 5:
            return _sentence(clean), 'attack-shell-removed', True
        if len(clean.split()) >= 2:
            return _sentence(clean), 'ambiguous-short', False

    # 9) Saf saldırı: yeni görüş uydurma; yalnızca tartışmayı görüş/gerekçe eksenine çek.
    if has_attack:
        return (
            'Bu görüşe katılmıyorum. Eleştirimi kişiye değil, ileri sürülen görüşün gerekçelerine odaklamak istiyorum.',
            'pure-attack', True,
        )

    return t, 'preserve-clean', True


def _clean_generation(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^(öneri|yeniden yazılmış yanıt|yanıt)\s*:\s*', '', text, flags=re.IGNORECASE)
    text = text.strip('"“” ')
    for marker in ('\nAçıklama:', '\nNeden:', '\nGerekçe:', '\nNot:'):
        if marker in text:
            text = text.split(marker, 1)[0].strip()
    text = re.split(r'\n\s*(?:Kullanıcı|Asistan|Assistant|System|User)\s*:', text, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    return text


def _has_bad_repetition(text: str) -> bool:
    words = re.findall(r'\w+', _fold(text))
    if len(words) < 12:
        return False
    trigrams = [' '.join(words[i:i + 3]) for i in range(len(words) - 2)]
    return len(set(trigrams)) / max(1, len(trigrams)) < 0.72


def _content_roots(text: str) -> list[str]:
    folded = _fold(_strip_attack_shell(text))
    words = re.findall(r'[a-z0-9%]+', folded)
    roots: list[str] = []
    for w in words:
        if w in STOPWORDS or len(w) < 4 or w.isdigit():
            continue
        root = w[:6] if len(w) >= 6 else w
        if root not in roots:
            roots.append(root)
    return roots


def _anchor_summary(text: str, signals: list[str]) -> list[str]:
    anchors: list[str] = []
    stance = _ban_stance(text)
    if stance != 'none':
        anchors.append(f'yasaklama yönelimi={stance}')
    if 'soru' in signals:
        anchors.append('soru niyeti')
    if 'sayısal/doğrulanabilir iddia' in signals:
        anchors.extend(f'sayı={x}' for x in _numbers(text))
    if 'kaynak/kanıt vurgusu' in signals:
        anchors.append('kaynak/kanıt talebi')
    if 'konuya katkı eleştirisi' in signals:
        anchors.append('konuya katkı eleştirisi')
    if 'bağlamı yeniden değerlendirme talebi' in signals:
        anchors.append('konuyu yeniden değerlendirme talebi')
    if 'koşullu/dengeli görüş' in signals:
        anchors.append('koşullu/dengeli görüş')
    if 'ironi/sarkazm' in signals:
        anchors.append('ironi: literal değil gerçek niyeti koru')
    protected = _protected_tokens(text)
    if protected:
        anchors.append('korunacak=' + ','.join(protected[:5]))
    roots = _content_roots(text)[:5]
    if roots:
        anchors.append('anahtar=' + ','.join(roots))
    return anchors


def _semantic_overlap_ok(original: str, candidate: str, signals: list[str]) -> bool:
    original_roots = _content_roots(original)
    candidate_roots = set(_content_roots(candidate))
    if len(original_roots) < 2:
        return True
    overlap = sum(1 for r in original_roots if r in candidate_roots)
    required = 1 if len(original_roots) <= 3 else 2
    if 'sayısal/doğrulanabilir iddia' in signals or 'kaynak/kanıt vurgusu' in signals:
        required = max(required, 1)
    return overlap >= required


def _negation_profile(text: str) -> set[str]:
    t = _normalize(text)
    keys = {
        'yanlış': ('yanlış', 'doğru değil'),
        'değil': ('değil',),
        'karşı': ('karşıyım', 'karşı çık'),
        'istememe': ('istemiyorum', 'istemem', 'olmamalı', 'yapılmamalı'),
    }
    return {name for name, markers in keys.items() if any(m in t for m in markers)}


def _candidate_valid(original: str, candidate: str, signals: list[str]) -> tuple[bool, str]:
    c = candidate.strip()
    o = original.strip()
    cl = _normalize(c)
    ol = _normalize(o)

    if not c or len(c.split()) < 3:
        return False, 'çıktı çok kısa/boş'
    if len(c.split()) > 46:
        return False, 'çıktı gereksiz uzun'
    if any(m in cl for m in PROMPT_LEAK_MARKERS):
        return False, 'prompt/ara metin sızıntısı veya doğal olmayan kalıp'
    if _has_any(OFFENSIVE_PATTERNS, cl) or _has_any(DIRECT_ATTACK_PATTERNS, cl):
        return False, 'kişiselleştirme temizlenmedi'
    if _has_bad_repetition(c):
        return False, 'tekrarlı/anlamsız üretim'

    original_numbers = _numbers(o)
    if original_numbers:
        compact_c = c.replace(' ', '')
        for n in original_numbers:
            if n.replace(' ', '') not in compact_c:
                return False, 'sayısal bilgi korunmadı'

    for token in _protected_tokens(o):
        if token not in c:
            return False, f'korunması gereken öğe kayboldu: {token}'

    if 'soru' in signals and '?' not in c:
        return False, 'soru niyeti korunmadı'

    if 'kaynak/kanıt vurgusu' in signals and not _any_marker(cl, EVIDENCE_MARKERS):
        return False, 'kaynak/kanıt talebi korunmadı'

    if 'ironi/sarkazm' in signals and _is_sarcastic(c):
        return False, 'ironi doğrudan niyete çevrilmedi'

    if 'koşullu/dengeli görüş' in signals and not _is_balanced_view(c):
        # Dengeli görüşün tek tarafa düşmesine izin verme. Açık iki-kutuplu anlatım da kabul edilir.
        c_stance = _ban_stance(c)
        if c_stance not in ('conditional', 'mixed'):
            return False, 'koşullu/dengeli görüş tek tarafa dönüştü'

    original_stance = _ban_stance(o)
    candidate_stance = _ban_stance(c)
    if original_stance in ('anti-ban', 'pro-ban') and candidate_stance not in (original_stance, 'mixed'):
        return False, 'ana görüş tersine döndü'
    if original_stance == 'conditional' and candidate_stance not in ('conditional', 'mixed'):
        return False, 'koşullu görüş tek tarafa dönüştü'
    if original_stance == 'conditional' and 'sınav' in ol and 'sınav' not in cl:
        return False, 'koşullu görüşte sınav bağlamı kayboldu'

    # Girişte güçlü yasaklama sonucu yoksa model yeni bir yasak sonucu icat edemez.
    if 'yasak' not in ol and any(p in cl for p in ('yasaklanmalıdır', 'yasaklanmalı', 'yasak olmalıdır', 'yasak olmalı')):
        return False, 'girişte olmayan yeni sonuç eklendi'

    # Negatif/itiraz omurgası açıkça varsa model bunu tamamen olumlu sonuca çeviremez.
    original_neg = _negation_profile(o)
    candidate_neg = _negation_profile(c)
    if original_neg and not candidate_neg and 'görüş ayrılığı/itiraz' in signals:
        # Yasak yönü özel denetimde korunmuşsa bu genel kontrolü atla.
        if original_stance == 'none':
            return False, 'itiraz/olumsuzluk omurgası kayboldu'

    if not _semantic_overlap_ok(o, c, signals):
        return False, 'mesajın ana içerik ankrajları korunmadı'

    return True, 'ok'


def _reason(signals: list[str], engine: str, decision_tag: str = '', validation_reason: str = '') -> str:
    if engine == 'preserve-safe':
        return 'Mesaj zaten yapıcı ve anlaşılır bulundu; ana içerik gereksiz yere değiştirilmedi.'

    parts: list[str] = []
    if 'hakaret/küfür' in signals or 'kişiye yönelik saldırı' in signals:
        parts.append('kişisel saldırıyı çıkardı')
    if 'bağlamı yeniden değerlendirme talebi' in signals:
        parts.append('konuyu yeniden değerlendirme talebini korudu')
    if 'konuya katkı eleştirisi' in signals and 'kaynak/kanıt vurgusu' not in signals:
        parts.append('konuya katkı eleştirisini korudu')
    if 'görüş ayrılığı/itiraz' in signals:
        parts.append('itirazın ana fikrini korudu')
    if 'koşullu/dengeli görüş' in signals:
        parts.append('koşullu/dengeli görüşü korudu')
    if 'ironi/sarkazm' in signals:
        parts.append('ironiyi literal okumadan gerçek niyete çevirdi')
    if 'soru' in signals:
        parts.append('soru niyetini korudu')
    if 'sayısal/doğrulanabilir iddia' in signals:
        parts.append('sayısal bilgiyi korudu')
    if 'kaynak/kanıt vurgusu' in signals or decision_tag == 'numeric-evidence':
        parts.append('kaynak/kanıt eksenini korudu')
    if not parts:
        parts.append('mesajın ana niyetini korudu')

    if engine == 'qwen-generative':
        prefix = 'Denetimli üretken AI'
    elif engine == 'hybrid-safe':
        prefix = 'Hibrit anlam-koruma katmanı'
    else:
        prefix = 'Bağlamsal güvenli motor'

    tail = ''
    if validation_reason and engine == 'hybrid-safe':
        tail = f' Üretken aday ({validation_reason}) nedeniyle reddedildi; güvenli yeniden yazım kullanıldı.'
    return f'{prefix}, ' + '; '.join(dict.fromkeys(parts)) + '.' + tail


def _generate_candidate(text: str, context: str, signals: list[str]) -> tuple[str, str]:
    """Üretken modelden kısa bir aday alır. Hata olursa ('', neden) döndürür."""
    model, tokenizer = load_model()
    if model is None or tokenizer is None:
        return '', 'üretken model hazır değil'

    try:
        import torch

        anchors = _anchor_summary(text, signals)
        system_prompt = (
            "Sen N-KÖPRÜ Yanıt Koçu'sun. Türkçe tartışma mesajını daha yapıcı ve anlaşılır yeniden yaz. "
            "Ana görüşü, yönü, soruyu, sayıları ve somut içeriği değiştirme. Girişte olmayan fikir, gerekçe, "
            "istatistik veya sonuç ekleme. Hakaret ve kişiselleştirmeyi çıkar. Kaynak isteyen mesaj kaynak istemeye "
            "devam etsin. Koşullu görüşte iki tarafı da koru. Açık ironi/sarkazm varsa literal övgüyü tekrar etme; "
            "gerçek niyeti doğrudan ve nötr biçimde yaz. En fazla 2 kısa doğal Türkçe cümle yaz. Yalnızca nihai mesajı döndür."
        )
        # Az örnek = CPU'da daha kısa prompt ve daha düşük gecikme.
        examples = [
            {'role': 'user', 'content': 'Mesaj: Sen bu konudan hiçbir şey anlamıyorsun.'},
            {'role': 'assistant', 'content': 'Bu görüşün gerekçesini yeterince ikna edici bulmuyorum. Dayandığın bilgi veya gerekçeleri daha açık paylaşabilir misin?'},
            {'role': 'user', 'content': 'Mesaj: Geçen dönem öğrencilerin %70’i yapay zekâ kullandı.'},
            {'role': 'assistant', 'content': 'Geçen dönem öğrencilerin %70’i yapay zekâ kullandı. Bu bilginin dayandığı kaynak veya araştırmayı paylaşabilir misin?'},
            {'role': 'user', 'content': 'Mesaj: Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.'},
            {'role': 'assistant', 'content': 'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.'},
        ]
        user_prompt = (
            f'Konu: {context.strip() or "Belirtilmedi"}\n'
            f'Sinyaller: {", ".join(signals)}\n'
            f'Korunacaklar: {"; ".join(anchors) if anchors else "ana fikir"}\n'
            f'Mesaj: {text}'
        )
        messages = [{'role': 'system', 'content': system_prompt}, *examples, {'role': 'user', 'content': user_prompt}]
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
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                repetition_penalty=1.12,
                no_repeat_ngram_size=3,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = outputs[0][inputs['input_ids'].shape[-1]:]
        return _clean_generation(tokenizer.decode(generated, skip_special_tokens=True)), 'ok'
    except Exception as exc:
        return '', f'üretim hatası: {type(exc).__name__}'


def rewrite_with_ai(text: str, context: str = '', use_ai: bool = True) -> dict[str, Any]:
    started = time.perf_counter()
    clean = text.strip()
    signals = analyze_message(clean)

    if not clean:
        return {
            'suggestion': '',
            'reason': 'Yeniden yazılacak metin boş.',
            'engine': 'none',
            'elapsed_ms': 0,
            'signals': signals,
        }

    deterministic, decision_tag, high_confidence = _deterministic_rewrite(clean, context, signals)

    # v0.4.4 hızlı yol: zaten temiz mesajlar ve yüksek güvenli saldırı/iddia türleri için
    # küçük üretken modeli çalıştırmak hem kaliteyi düşürebiliyor hem CPU'da 15-25 sn gecikme ekliyordu.
    if USE_FAST_PATH and high_confidence:
        engine = 'preserve-safe' if deterministic == clean else 'hybrid-safe'
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            'suggestion': deterministic,
            'reason': _reason(signals, engine, decision_tag),
            'engine': engine,
            'elapsed_ms': elapsed_ms,
            'signals': signals,
        }

    suggestion = deterministic
    engine = 'hybrid-safe' if deterministic != clean else 'preserve-safe'
    validation_reason = ''

    if use_ai and not high_confidence:
        candidate, generation_reason = _generate_candidate(clean, context, signals)
        if candidate:
            valid, validation_reason = _candidate_valid(clean, candidate, signals)
            if valid:
                suggestion = candidate
                engine = 'qwen-generative'
            else:
                suggestion = deterministic
                engine = 'hybrid-safe'
        else:
            validation_reason = generation_reason

    # Son güvenlik kapısı: hangi motor üretirse üretsin kullanıcıya hakaret/prompt sızıntısı dönmez.
    final_valid, final_reason = _candidate_valid(clean, suggestion, signals)
    if not final_valid:
        safe, safe_tag, _ = _deterministic_rewrite(clean, context, signals)
        safe_lower = _normalize(safe)
        safe_ok = not _has_any(OFFENSIVE_PATTERNS, safe_lower) and not _has_any(DIRECT_ATTACK_PATTERNS, safe_lower)
        nums_ok = all(n.replace(' ', '') in safe.replace(' ', '') for n in _numbers(clean))
        protected_ok = all(tok in safe for tok in _protected_tokens(clean))
        if safe_ok and nums_ok and protected_ok:
            suggestion = safe
            decision_tag = safe_tag
            engine = 'preserve-safe' if suggestion == clean else 'hybrid-safe'
            validation_reason = validation_reason or final_reason
        else:
            stripped = _strip_attack_shell(clean)
            suggestion = _sentence(stripped) if stripped else 'Bu görüşe katılmıyorum. Gerekçelerini daha açık paylaşabilir misin?'
            engine = 'contextual-fallback'
            validation_reason = validation_reason or final_reason

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    return {
        'suggestion': suggestion,
        'reason': _reason(signals, engine, decision_tag, validation_reason),
        'engine': engine,
        'elapsed_ms': elapsed_ms,
        'signals': signals,
    }
