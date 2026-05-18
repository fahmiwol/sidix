# MULTILINGUAL TYPO-RESILIENT FRAMEWORK
## SIDIX yang Mengerti Typo dalam 6+ Bahasa

**Versi:** 1.0 | **Status:** IMPLEMENTATION-READY
**Scope:** Indonesia, English, Arabizi, Malay, Tagalog, Hinglish + Script Detection

---

## FILOSOFI

User SIDIX bukan hanya dari Indonesia. SIDIX harus mengerti typo dalam bahasa apapun:
- **Indonesia**: "gmn", "bgmn", "tdk", "krn"
- **English**: "hw", "pls", "idk", "btw", "rn"
- **Arabizi**: "kifah", "shlon", "sho", "ya3ni", "inshallah"
- **Malay**: "cmna", "nk", "xde", "btul", "tq"
- **Tagalog**: "pno", "mg", "po", "kau", "ako"
- **Hinglish**: "kaise", "kya", "nahi", "haan", "theek hai"

> *"Typo adalah tanda kemanusiaan. SIDIX harus mengerti, bukan mengoreksi."*

---

## 5-LAYER UNIVERSAL ARCHITECTURE

```
Input User (any language, any typo level)
    |
    v
+--------------------------------------------------+
|  LAYER 1: SCRIPT DETECTOR                        |
|  - Detect script: Latin / Arabic / Cyrillic / CJK |
|  - Auto-route ke language detector yang tepat      |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
|  LAYER 2: LANGUAGE DETECTOR                      |
|  - 6 language classifiers with confidence         |
|  - Mixed-language detection                       |
|  - Auto-switch typo dictionary                     |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
|  LAYER 3: UNIVERSAL TYPO CORRECTOR               |
|  - Language-specific typo dictionaries            |
|  - QWERTY proximity mapping                       |
|  - Phonetic matching (sound-alike)                |
|  - Slang/abbreviation expansion                   |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
|  LAYER 4: CROSS-LINGUAL SEMANTIC MATCHER         |
|  - Embedding-based intent detection               |
|  - Cross-lingual similarity                       |
|  - Context preservation                           |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
|  LAYER 5: CULTURAL CONTEXT RESPONDER             |
|  - Respond in user's detected language            |
|  - Respect cultural communication style           |
|  - Maintain dignity — never shame for typos       |
+--------------------------------------------------+
    |
    v
SIDIX Process (Jiwa Orchestrator) + Response in user's language
```

---

## LAYER 1: SCRIPT DETECTOR

```python
# brain/multilingual/script_detector.py

import re
from enum import Enum
from typing import Dict, Tuple

class ScriptType(Enum):
    LATIN = "latin"           # English, Indonesian, Malay, etc.
    ARABIC = "arabic"         # Arabic script
    CYRILLIC = "cyrillic"     # Russian, Ukrainian, etc.
    CJK = "cjk"               # Chinese, Japanese, Korean
    DEVANAGARI = "devanagari" # Hindi, Sanskrit
    THAI = "thai"             # Thai script
    HEBREW = "hebrew"         # Hebrew script
    MIXED = "mixed"           # Multiple scripts
    UNKNOWN = "unknown"

class ScriptDetector:
    """Detect script system dari input text."""
    
    # Unicode ranges
    PATTERNS = {
        ScriptType.ARABIC: r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
        ScriptType.CYRILLIC: r'[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F]',
        ScriptType.CJK: r'[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF\U00020000-\U0002A6DF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]',
        ScriptType.DEVANAGARI: r'[\u0900-\u097F]',
        ScriptType.THAI: r'[\u0E00-\u0E7F]',
        ScriptType.HEBREW: r'[\u0590-\u05FF\uFB1D-\uFB4F]',
    }
    
    # Minimum characters to consider a script present
    MIN_CHARS = 2
    
    def detect(self, text: str) -> Dict:
        """
        Detect script type dari text.
        
        Returns:
            {
                "primary_script": ScriptType,
                "detected_scripts": [ScriptType, ...],
                "confidence": float,
                "is_mixed": bool
            }
        """
        text = text.strip()
        if not text:
            return {
                "primary_script": ScriptType.UNKNOWN,
                "detected_scripts": [],
                "confidence": 0.0,
                "is_mixed": False
            }
        
        detected = []
        script_counts = {}
        
        for script, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            count = len(matches)
            if count >= self.MIN_CHARS:
                detected.append(script)
                script_counts[script] = count
        
        # Determine primary script
        if len(detected) == 0:
            # Default to Latin if no special scripts found
            primary = ScriptType.LATIN
            is_mixed = False
        elif len(detected) == 1:
            primary = detected[0]
            is_mixed = False
        else:
            # Multiple scripts — pick the one with most characters
            primary = max(script_counts, key=script_counts.get)
            is_mixed = True
        
        # Calculate confidence
        total_special = sum(script_counts.values())
        total_chars = len([c for c in text if c.isalpha()])
        confidence = min(1.0, total_special / max(total_chars, 1)) if detected else 0.5
        
        return {
            "primary_script": primary,
            "detected_scripts": detected,
            "confidence": confidence,
            "is_mixed": is_mixed,
            "script_counts": script_counts
        }
    
    def is_arabizi(self, text: str) -> bool:
        """
        Detect Arabizi — Arabic words written in Latin script.
        Common patterns: numbers for Arabic letters (3, 7, 9), characteristic words.
        """
        arabizi_markers = [
            r'\b[aks]if\b', r'\bshlon\b', r'\bsho\b', r'\bkifah\b',
            r'\bya3ni\b', r'\binshallah\b', r'\balhamdulillah\b',
            r'\bmashallah\b', r'\bsubhanallah\b', r'\bwallah\b',
            r'\bhabibi\b', r'\byalla\b', r'\bshukran\b',
            r'\b[37]\w*[79]',  # Numbers as Arabic letters: 3=a, 7=h, 9=q
        ]
        
        text_lower = text.lower()
        matches = sum(1 for pattern in arabizi_markers if re.search(pattern, text_lower))
        return matches >= 2 or any(c.isdigit() for c in text if c in '379')
    
    def is_romanized_hindi(self, text: str) -> bool:
        """Detect Hinglish — Hindi written in Latin script."""
        hinglish_markers = [
            r'\bkaise\b', r'\bkya\b', r'\bnahi\b', r'\bhaan\b',
            r'\btheek\b', r'\bacha\b', r'\bbhai\b', r'\bhai\b',
            r'\bmera\b', r'\btera\b', r'\bkahaa\b', r'\bkaro\b',
            r'\bho\b', r'\bji\b', r'\bna\b', r'\bji\b',
        ]
        text_lower = text.lower()
        matches = sum(1 for pattern in hinglish_markers if re.search(pattern, text_lower))
        return matches >= 2


# Singleton
script_detector = ScriptDetector()
```

---

## LAYER 2: LANGUAGE DETECTOR

```python
# brain/multilingual/language_detector.py

from enum import Enum
from typing import Dict, List, Tuple
import re

class LanguageCode(Enum):
    """Supported languages for SIDIX Multilingual Framework."""
    ID = "id"        # Indonesian
    EN = "en"        # English
    AR_LATIN = "ar-latin"  # Arabizi (Arabic in Latin script)
    MS = "ms"        # Malay
    TL = "tl"        # Tagalog
    HI_LATIN = "hi-latin"  # Hinglish (Hindi in Latin script)
    UNKNOWN = "unknown"

class UniversalLanguageDetector:
    """
    Detect language dari text — termasuk Arabizi dan Hinglish.
    Supports mixed-language detection.
    """
    
    # Language markers — characteristic words/phrases untuk tiap bahasa
    LANGUAGE_MARKERS = {
        LanguageCode.ID: {
            "words": [
                "yang", "dan", "di", "dari", "untuk", "dengan", "pada", "dalam",
                "ini", "itu", "adalah", "bisa", "sudah", "akan", "saya", "kamu",
                "dia", "kita", "mereka", "tidak", "juga", "sudah", "belum",
                "banyak", "sedikit", "bagus", "baik", "buruk", "baru", "lama",
                "gimana", "bagaimana", "kenapa", "mengapa", "dimana", "kapan",
                "apa", "siapa", "berapa", "bagaimana", "mohon", "tolong", "terima kasih",
                "iya", "bukan", "benar", "salah", "mungkin", "pastinya",
                "gmn", "bgmn", "knp", "tdk", "dg", "dgn", "utk", "dlm",
                "sdh", "udh", "blm", "bs", "jg", "jga", "krn", "tp", "tpi",
                "bgt", "bgtt", "skrg", "nnti", "kmrn", "gw", "gue", "lu", "elo",
            ],
            "patterns": [
                r'\b(aku|saya|gue|gw)\b.*\b(kamu|lu|elo|anda)\b',  # Personal pronouns
                r'\b(di|ke|dari)\s+\w+',  # Prepositions
                r'(nya|an|kan|lah|pun)$',  # Suffixes
            ],
            "weight": 1.0
        },
        
        LanguageCode.EN: {
            "words": [
                "the", "and", "is", "are", "was", "were", "be", "been",
                "have", "has", "had", "do", "does", "did", "will", "would",
                "could", "should", "may", "might", "can", "shall",
                "what", "which", "who", "when", "where", "why", "how",
                "this", "that", "these", "those", "here", "there",
                "hello", "hi", "please", "thanks", "thank you", "sorry",
                "yes", "no", "maybe", "sure", "okay", "ok",
                "good", "bad", "new", "old", "big", "small",
                "pls", "thx", "ty", "idk", "btw", "rn", "imo", "tbh",
                "fyi", "asap", "brb", "lol", "omg", "wtf", "nvm",
                "hw", "wat", "dis", "dat", "gonna", "wanna", "gotta",
            ],
            "patterns": [
                r'\b(th|sh|ch|ph|gh)\w+',  # English digraphs
                r'\b\w+(ing|ed|er|est|tion|sion|ness|ment|able|ible)\b',  # English suffixes
                r'\b(i|you|he|she|it|we|they)\b.*\b(am|is|are|was|were)\b',  # Subject-verb
            ],
            "weight": 1.0
        },
        
        LanguageCode.AR_LATIN: {
            "words": [
                "kifah", "kifach", "shlon", "shlonik", "sho", "shoo", "shnu",
                "ya3ni", "yani", "inshallah", "inshaallah", "alhamdulillah",
                "mashallah", "subhanallah", "allah", "wallah", "wallahi",
                "habibi", "habibti", "yalla", "yallah", "shukran", "afwan",
                "marhaba", "salam", "assalam", "alaikum", "waalaikum",
                "ramadan", "eid", "mubarak", "barakallah", "jazakallah",
                "insaan", "kalam", "kitab", "qalb", "ruh", "ilm", "hikma",
                "khalas", "mashi", "tamam", "zain", "mabsout", "mabrook",
                "akhi", "ukhti", "umm", "abu", "ibn", "bint",
                "salat", "dua", "wudu", "ghusl", "zakat", "hajj", "umrah",
                "halal", "haram", "mashbooh", "fardh", "sunnah", "wajib",
                "astaghfirullah", "bismillah", "masyaallah", "lailahaillallah",
                "assalamualaikum", "waalaikumsalam", "jazakallahu khairan",
            ],
            "patterns": [
                r'\b\w*[379]\w*\b',  # Arabic numerals: 3=ع, 7=ح, 9=ق
                r'\b(al|el|il)-?\w+',  # Arabic article
                r'\b(abd|abu|ibn|bint|umm)\s+\w+',  # Arabic naming
            ],
            "weight": 1.2  # Higher weight — very distinctive
        },
        
        LanguageCode.MS: {
            "words": [
                "yang", "dan", "di", "dari", "untuk", "dengan", "pada",
                "ini", "itu", "adalah", "boleh", "sudah", "akan", "saya", "awak",
                "dia", "kita", "mereka", "tidak", "juga",
                "cmna", "cmne", "macam mana", "bgmana", "kenapa", "mengapa",
                "mana", "bila", "apa", "siapa", "berapa",
                "terima kasih", "minta maaf", "ya", "tidak", "ok",
                "bagus", "baik", "buruk", "baru", "lama",
                "nk", "nakk", "xde", "tade", "btul", "btol", "tak betul",
                "tq", "thx", "ty", "xpa", "xpela", "sory", "sori",
                "lah", "leh", "meh", "kan", "kot", "eh", "ah",
                "sy", "awk", "dia", "org", "orang", "kite", "kito",
                "skrg", "nnti", "hrini", "hritu", "esok", "smalam",
                "bnyk", "skit", "sgt", "sngt", "sangat",
                "jgn", "jg", "pun", "je", "ja", "dgn", "utk",
            ],
            "patterns": [
                r'\b(saya|awak|aku|kau|dia)\b.*\b(boleh|sudah|akan|tidak)\b',
                r'\b(di|ke|dari)\s+\w+',
                r'(lah|kan|pun|je|ja|meh|kot)$',  # Malaysian particles
            ],
            "weight": 1.0
        },
        
        LanguageCode.TL: {
            "words": [
                "ang", "ng", "sa", "na", "ay", "at", "para", "may", "mayroon",
                "wala", "hindi", "opo", "oo", "hindi po", "salamat", "maraming salamat",
                "paano", "ano", "sino", "bakit", "saan", "kailan", "gaano",
                "ako", "ikaw", "siya", "tayo", "kami", "kayo", "sila",
                "po", "ho", "opo", "oho",
                "maganda", "masaya", "malungkot", "mabuti", "masama",
                "ngayon", "bukas", "kahapon", "mamaya",
                "marami", "kaunti", "masyado", "lagi",
                "pno", "mg", "bkt", "sn", "kln", "gno",
                "tlga", "tlg", "dapat", "dpt", "lng", "lang",
                "kase", "kc", "kasi", "dahil", "pag", "kapag",
                "pero", "peru", "kaso", "tsaka", "at saka",
                "oo", "ndi", "hnd", "wrn", "wala",
                "pls", "plz", "ty", "thx", "salamat po",
                "ate", "kuya", "lola", "lolo", "nanay", "tatay",
            ],
            "patterns": [
                r'\b(ako|ikaw|siya|tayo|sila)\b.*\b(ay|ng|sa)\b',
                r'\b\w+(ng|ang|sa|na)\b',  # Common Tagalog particles
                r'(po|ho|opo|oho)$',  # Honorifics
            ],
            "weight": 1.0
        },
        
        LanguageCode.HI_LATIN: {
            "words": [
                "kaise", "kaisa", "kaisi", "kya", "kyun", "kyon", "kahan", "kab",
                "nahi", "na", "nai", "nhn", "nhin",
                "haan", "han", "hna", "hji", "hnji",
                "theek", "thik", "tik", "badhiya", "achha", "acha", "accha",
                "bhai", "bhen", "dost", "yaar",
                "hai", "hain", "tha", "thi", "the", "hoga", "hogi",
                "mera", "meri", "mere", "tera", "teri", "tere", "uska", "uski",
                "main", "tum", "aap", "woh", "wo", "yeh", "ye",
                "mein", "maine", "tune", "usne", "unhone",
                "kar", "karo", "kare", "karna", "kiya", "kia",
                "chalo", "ruk", "jao", "aao", "jaao",
                "bahut", "bohot", "bht", "jyada", "zyaada", "kam",
                "dhanyavad", "shukriya", "namaste", "salaam", "adaab",
                "haan ji", "nahi ji", "theek hai", "koi baat nahi",
                "sab", "sabhi", "kuch", "koi", "har", "aur",
                "lekin", "par", "magar", "toh", "to", "ki", "ka", "ke",
                "dill", "dil", "dimag", "mann", "aatma",
            ],
            "patterns": [
                r'\b(main|tum|aap|woh|yeh)\b.*\b(hai|hain|tha|thi)\b',
                r'\b\w+(na|ne|ni)\b',  # Verb endings
                r'(hai|hain|tha|thi|hoga|thi)$',  # Common endings
            ],
            "weight": 1.1  # Slightly higher — distinctive markers
        }
    }
    
    def detect(self, text: str) -> Dict:
        """
        Detect language(s) dari text.
        
        Returns:
            {
                "primary_language": LanguageCode,
                "detected_languages": [
                    {"language": LanguageCode, "confidence": float, "evidence": [str]},
                    ...
                ],
                "is_mixed": bool,
                "script": ScriptType
            }
        """
        text_lower = text.lower().strip()
        if not text:
            return self._empty_result()
        
        # First: detect script
        from brain.multilingual.script_detector import script_detector
        script_result = script_detector.detect(text)
        
        # Arabizi check
        if script_detector.is_arabizi(text):
            return {
                "primary_language": LanguageCode.AR_LATIN,
                "detected_languages": [{
                    "language": LanguageCode.AR_LATIN,
                    "confidence": 0.9,
                    "evidence": ["arabizi_patterns"]
                }],
                "is_mixed": False,
                "script": ScriptType.LATIN
            }
        
        # Hinglish check
        if script_detector.is_romanized_hindi(text):
            return {
                "primary_language": LanguageCode.HI_LATIN,
                "detected_languages": [{
                    "language": LanguageCode.HI_LATIN,
                    "confidence": 0.85,
                    "evidence": ["hinglish_markers"]
                }],
                "is_mixed": False,
                "script": ScriptType.LATIN
            }
        
        # Score each language
        scores = {}
        for lang, data in self.LANGUAGE_MARKERS.items():
            score = self._score_language(text_lower, lang, data)
            scores[lang] = score
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_scores[0][0]
        primary_score = sorted_scores[0][1]
        
        # Build detected languages list
        detected = []
        for lang, score in sorted_scores:
            if score > 0:  # Only include detected languages
                detected.append({
                    "language": lang,
                    "confidence": min(1.0, score),
                    "evidence": self._get_evidence(text_lower, lang)
                })
        
        # Check if mixed (secondary language score > 50% of primary)
        is_mixed = len(sorted_scores) > 1 and sorted_scores[1][1] > primary_score * 0.5
        
        return {
            "primary_language": primary,
            "detected_languages": detected,
            "is_mixed": is_mixed,
            "script": script_result["primary_script"]
        }
    
    def _score_language(self, text: str, lang: LanguageCode, data: Dict) -> float:
        """Score seberapa likely text adalah bahasa tertentu."""
        score = 0.0
        weight = data.get("weight", 1.0)
        
        # Word matching
        words_found = 0
        for word in data["words"]:
            if word in text:
                words_found += 1
        
        # Normalize by word list size (use log to prevent bias toward languages with more markers)
        word_score = min(1.0, words_found / max(len(data["words"]) * 0.1, 5))
        score += word_score * weight
        
        # Pattern matching
        pattern_hits = 0
        for pattern in data.get("patterns", []):
            if re.search(pattern, text):
                pattern_hits += 1
        
        pattern_score = min(1.0, pattern_hits / max(len(data.get("patterns", [])), 1))
        score += pattern_score * weight * 0.5
        
        return score
    
    def _get_evidence(self, text: str, lang: LanguageCode) -> List[str]:
        """Get evidence words yang matched."""
        text_lower = text.lower()
        evidence = []
        
        data = self.LANGUAGE_MARKERS.get(lang, {})
        for word in data.get("words", []):
            if word in text_lower and word not in evidence:
                evidence.append(word)
                if len(evidence) >= 5:
                    break
        
        return evidence
    
    def _empty_result(self) -> Dict:
        return {
            "primary_language": LanguageCode.UNKNOWN,
            "detected_languages": [],
            "is_mixed": False,
            "script": ScriptType.UNKNOWN
        }


# Singleton
detector = UniversalLanguageDetector()
```

---

## LAYER 3: UNIVERSAL TYPO CORRECTOR

### 3.1 Typo Dictionaries per Language

```python
# brain/multilingual/typo_dictionaries.py

# ============================================
# 1. INDONESIAN TYPO DICTIONARY (200+ entries)
# ============================================
# (Sudah lengkap di TYPO_RESILIENT_FRAMEWORK.md)
# Import dari brain/typo/dictionaries.py

# ============================================
# 2. ENGLISH TYPO DICTIONARY (300+ entries)
# ============================================

EN_TYPO_DICTIONARY = {
    # Common misspellings
    "teh": "the", "hte": "the", "eth": "the",
    "adn": "and", "nad": "and", "annd": "and",
    "taht": "that", "thta": "that", "tath": "that",
    "wiht": "with", "wit": "with", "whit": "with",
    "fo": "for", "fro": "for", "fot": "for",
    "form": "from", "frm": "from", "fomr": "from",
    "ti": "it", "ti's": "it's",
    "si": "is", "sia": "is a",
    "onw": "own", "won": "own",
    "hw": "how", "howw": "how", "hwo": "how",
    "whn": "when", "wne": "when", "wen": "when",
    "wer": "where", "wher": "where", "wehre": "where",
    "waht": "what", "wat": "what", "whta": "what",
    "wo": "who", "whois": "who is",
    "wy": "why", "whi": "why",
    "wa": "was", "wass": "was",
    "hv": "have", "hve": "have", "haev": "have",
    "hasa": "has a", "haz": "has",
    "hadn": "hadn't",
    "didnt": "didn't", "did'nt": "didn't", "dint": "didn't",
    "doesnt": "doesn't", "doeant": "doesn't",
    "dont": "don't", "donot": "do not",
    "wont": "won't", "wld": "would", "wouldnt": "wouldn't",
    "shld": "should", "shud": "should", "shouldnt": "shouldn't",
    "cud": "could", "cld": "could", "couldnt": "couldn't",
    "cant": "can't", "cnt": "can't", "cannnot": "cannot",
    "isnt": "isn't", "aint": "isn't",
    "arent": "aren't", "werent": "weren't",
    "hasnt": "hasn't", "havent": "haven't",
    "wasnt": "wasn't", "wernt": "weren't",
    "im": "i'm", "ive": "i've", "ill": "i'll",
    "youre": "you're", "youve": "you've", "youll": "you'll",
    "hes": "he's", "shes": "she's", "its": "it's",
    "thats": "that's", "whats": "what's", "heres": "here's",
    "theres": "there's", "wheres": "where's",
    "lets": "let's",
    
    # QWERTY proximity typos
    "abd": "and", "ans": "and", "amd": "and",
    "tehr": "their", "thier": "their", "t heir": "their",
    "tey": "they", "thye": "they", "tehy": "they",
    "thme": "them", "t hem": "them",
    "yu": "you", "yuo": "you", "oyu": "you", "yoy": "you",
    "me": "my", "ym": "my",
    "her": "her", "hre": "her",
    "hsi": "his",
    "or": "our", "uor": "our",
    "ut": "out", "otu": "out",
    "abot": "about", "abuot": "about", "baout": "about",
    "bck": "back", "bakc": "back",
    "beter": "better", "bettr": "better",
    "cll": "call", "cal": "call",
    "cme": "come", "com": "come", "ocme": "come",
    "dae": "day", "dy": "day",
    "evn": "even", "evne": "even",
    "frist": "first", "fisrt": "first", "firs": "first",
    "gett": "get", "gte": "get", "ge t": "get",
    "giv": "give", "gve": "give", "giev": "give",
    "god": "good", "ogod": "good", "goood": "good",
    "kno": "know", "knwo": "know", "konw": "know",
    "liek": "like", "lik": "like", "ilke": "like",
    "lk": "look", "lok": "look",
    "mkae": "make", "maek": "make", "mak": "make",
    "ma": "man", "mna": "man",
    "migh": "might", "migth": "might",
    "msut": "must", "mstu": "must",
    "nme": "name", "nmae": "name", "naem": "name",
    "nwe": "new", "enw": "new",
    "noe": "now", "nwo": "now", "onw": "now",
    "oly": "only", "onyl": "only", "onl": "only",
    "otehr": "other", "otehr": "other", "othr": "other",
    "poeple": "people", "peple": "people", "ppl": "people",
    "pleas": "please", "plz": "please", "pls": "please",
    "rigt": "right", "rihgt": "right", "rgiht": "right",
    "sad": "said", "siad": "said", "sia d": "said",
    "se": "see", "es": "see",
    "smoe": "some", "soem": "some",
    "tiem": "time", "tme": "time", "itme": "time",
    "tow": "two", "twp": "two",
    "ues": "use", "sue": "use", "uesd": "used",
    "vrey": "very", "veyr": "very",
    "wya": "way",
    "wrok": "work", "wok": "work", "wokr": "work",
    "yaer": "year", "yera": "year", "yr": "year",
    
    # Internet/chat shortforms
    "u": "you", "ur": "your", "urs": "yours",
    "r": "are", "b": "be",
    "y": "why",
    "n": "and",
    "c": "see",
    "b4": "before", "b4n": "bye for now",
    "gr8": "great", "gr8t": "great",
    "l8r": "later", "l8er": "later",
    "m8": "mate",
    "w8": "wait", "w8ing": "waiting",
    "2day": "today", "2morrow": "tomorrow", "2morow": "tomorrow",
    "4ever": "forever", "4eva": "forever",
    "luv": "love", "lub": "love",
    "tho": "though", "thru": "through",
    "nite": "night", "tonite": "tonight",
    "thanx": "thanks", "thnx": "thanks",
    "x": "express", "xlnt": "excellent",
    "msg": "message", "msgs": "messages",
    "plz": "please", "plzz": "please",
    "sry": "sorry", "srry": "sorry",
    "ttyl": "talk to you later",
    "gtg": "got to go", "g2g": "got to go",
    "idk": "i don't know", "idek": "i don't even know",
    "idc": "i don't care",
    "imo": "in my opinion", "imho": "in my humble opinion",
    "tbh": "to be honest",
    "fyi": "for your information",
    "asap": "as soon as possible",
    "afaik": "as far as i know",
    "brb": "be right back",
    "btw": "by the way",
    "bbl": "be back later",
    "cu": "see you", "cya": "see you",
    "dm": "direct message", "pm": "private message",
    "ftw": "for the win", "fml": "for my luck",
    "gg": "good game", "wp": "well played",
    "hbd": "happy birthday",
    "ic": "i see",
    "ikr": "i know right",
    "jk": "just kidding", "jkjk": "just kidding",
    "k": "okay", "kk": "okay", "kkk": "okay",
    "lmk": "let me know",
    "nvm": "never mind", "nvmd": "never mind",
    "ofc": "of course",
    "omw": "on my way",
    "rn": "right now",
    "smh": "shaking my head",
    "sus": "suspicious",
    "tbd": "to be decided",
    "tfw": "that feeling when",
    "thx": "thanks", "tx": "thanks",
    "ty": "thank you", "tysm": "thank you so much", "tyvm": "thank you very much",
    "w/": "with", "w/o": "without",
    "wat": "what", "wut": "what",
    "dis": "this", "dat": "that",
    "dere": "there", "der": "there",
    "dunno": "don't know",
    "gonna": "going to", "wanna": "want to", "gotta": "got to",
    "kinda": "kind of", "sorta": "sort of",
    "lemme": "let me", "gimme": "give me",
    "dun": "don't", "donno": "don't know",
    "tryna": "trying to",
    "outta": "out of",
    "lotta": "lot of",
    "cuppa": "cup of",
}

# ============================================
# 3. ARABIZI TYPO DICTIONARY (200+ entries)
# ============================================

AR_LATIN_TYPO_DICTIONARY = {
    # Greetings
    "salam": "salam", "slm": "salam", "assalam": "assalamualaikum",
    "aslm": "assalamualaikum", "asalam": "assalamualaikum",
    "alaikum": "waalaikumsalam", "ws": "waalaikumsalam",
    "walaikum": "waalaikumsalam", "wslm": "waalaikumsalam",
    "marhaba": "marhaba", "mrhba": "marhaba",
    "sabah": "sabah al khair", "sabaho": "sabah al khair",
    "masa": "masa al khair", "maso": "masa al khair",
    
    # Common expressions
    "kifah": "kifah", "kif": "kifah", "kifach": "kifah",
    "kifak": "kifak", "kifik": "kifik",
    "shlon": "shlon", "shlonak": "shlonak", "shlonik": "shlonik",
    "shlonic": "shlonik", "shlnak": "shlonak",
    "sho": "sho", "shoo": "sho", "esh": "esh", "sh": "sh",
    "shnu": "shnu", "shno": "shnu", "ish": "ish",
    "waen": "waen", "wayn": "waen", "ween": "waen",
    "yalla": "yalla", "yallah": "yalla", "yala": "yalla",
    "ya3ni": "ya3ni", "yani": "yani", "y3ni": "ya3ni",
    "inshallah": "inshallah", "insh": "inshallah", "inshaallah": "inshallah",
    "inshalah": "inshallah", "ins": "inshallah",
    "alhamdulillah": "alhamdulillah", "alhmd": "alhamdulillah",
    "alhamd": "alhamdulillah", "7md": "alhamdulillah",
    "mashallah": "mashallah", "mash": "mashallah", "msa": "mashallah",
    "subhanallah": "subhanallah", "sbhan": "subhanallah", "sb7an": "subhanallah",
    "astaghfirullah": "astaghfirullah", "astgfr": "astaghfirullah",
    "bismillah": "bismillah", "bsm": "bismillah",
    "jazakallah": "jazakallah", "jazak": "jazakallah",
    "jazakallahu khairan": "jazakallahu khairan", "jzk": "jazakallahu khairan",
    "barakallah": "barakallah", "brak": "barakallah",
    "mabrook": "mabrook", "mabruk": "mabrook", "mbrook": "mabrook",
    
    # Pronouns
    "ana": "ana", "ani": "ana", "ene": "ana",
    "enta": "enta", "inti": "inti", "ent": "enta",
    "entu": "entu", "intu": "entu",
    "huwe": "huwe", "hiya": "hiya",
    "ehna": "ehna", "ihna": "ehna",
    "akhi": "akhi", "akho": "akhi", "5o": "akhi",
    "ukhti": "ukhti", "ukht": "ukhti",
    "habibi": "habibi", "habibti": "habibti", "7bibi": "habibi",
    
    # Common words
    "wallah": "wallah", "wallahi": "wallahi", "wlh": "wallah",
    "khalas": "khalas", "5las": "khalas", "kls": "khalas",
    "tamam": "tamam", "tmam": "tamam",
    "zain": "zain", "zn": "zain", "mnee7": "mnee7",
    "mabsout": "mabsout", "mabsoot": "mabsout",
    "mashi": "mashi", "mchy": "mashi", "mshi": "mashi",
    "sahih": "sahih", "sh": "sahih",
    "mumkin": "mumkin", "mken": "mumkin", "mumken": "mumkin",
    "mish": "mish", "msh": "mish", "mo": "mish", "mu": "mish",
    "la": "la", "laa": "la",
    "naam": "naam", "nm": "naam",
    "aiwa": "aiwa", "ewa": "aiwa",
    "shukran": "shukran", "shkran": "shukran", "thx": "shukran",
    "afwan": "afwan",
    "min fadlak": "min fadlak", "mf": "min fadlak",
    "law samaht": "law samaht", "ls": "law samaht",
    "ma3leh": "ma3leh", "malesh": "malesh", "m3lesh": "malesh",
    "ma3lesh": "malesh", "m3leh": "ma3leh",
    "bas": "bas", "bs": "bas",
    "kteer": "kteer", "ktir": "kteer", "kther": "kteer",
    "shway": "shway", "shwai": "shway", "shoya": "shway",
    "ktshan": "ktshan", "kteer kteer": "kteer kteer",
    "dah": "dah", "dih": "dih", "da": "dah",
    "illi": "illi", "ely": "illi", "li": "illi",
    "3nd": "3nd", "and": "3nd",
    "fi": "fi", "fih": "fi",
    "mn": "mn", "min": "min",
    "la": "la", "ila": "ila",
    "3la": "3la", "ala": "ala",
    "bl": "bl", "bala": "bala",
    "w": "w", "wa": "wa",
    " Aw": " Aw", "aw": "aw",
    "li": "li", "lil": "lil",
    "hatha": "hatha", "hathi": "hathi", "hada": "hatha", "hadi": "hathi",
    "kol": "kol", "killo": "kol", "kul": "kol",
    "wahed": "wahed", "wahid": "wahed", "w7d": "wahed",
    "etnen": "etnen", "ethnen": "etnen",
    "tlet": "tlet", "tlata": "tlata",
    "arba3": "arba3", "arb3": "arba3",
    "khamsa": "khamsa", "5msa": "khamsa",
    "sitta": "sitta",
    
    # Religious terms
    "salat": "salat", "salah": "salat", "slah": "salat",
    "dua": "dua", "do3a": "dua", "doaa": "dua",
    "wudu": "wudu", "wdu": "wudu",
    "ghusl": "ghusl",
    "zakat": "zakat", "zkt": "zakat",
    "hajj": "hajj", "7j": "hajj",
    "umrah": "umrah",
    "halal": "halal", "7lal": "halal",
    "haram": "haram", "7ram": "haram",
    "mashbooh": "mashbooh",
    "fardh": "fardh", "ford": "fardh",
    "sunnah": "sunnah", "sna": "sunnah",
    "wajib": "wajib",
    "quran": "quran", "quraan": "quran", "qur'an": "quran",
    "hadith": "hadith", "7dith": "hadith",
    "sahabah": "sahabah", "shb": "sahabah",
    "imam": "imam",
    "sheikh": "sheikh", "shk": "sheikh", "5": "sheikh",
    "masjid": "masjid", "msgd": "masjid",
    "qibla": "qibla",
    "adhan": "adhan", "athan": "adhan",
    "iftar": "iftar", "ftor": "iftar",
    "suhoor": "suhoor", "shor": "suhoor",
    "taraweeh": "taraweeh",
    "tahajjud": "tahajjud",
    "jummah": "jummah", "juma": "jummah",
    "eid": "eid", "3id": "eid",
    "ramadan": "ramadan", "rmzan": "ramadan",
    "hijri": "hijri",
    "shahada": "shahada",
    "takbir": "takbir",
    "tasbih": "tasbih",
    "tahmid": "tahmid",
    "tahlil": "tahlil",
    "istikharah": "istikharah",
    
    # SIDIX-related Arabizi
    "ilm": "ilm", "3lm": "ilm",
    "hikmah": "hikmah", "7kma": "hikmah",
    "qalb": "qalb",
    "ruh": "ruh",
    "nafs": "nafs",
    "aql": "aql",
    "hayat": "hayat",
    "sidix": "sidix",
    "deen": "deen", "din": "deen",
    "dunya": "dunya",
    "akhira": "akhira",
    "siraat": "siraat",
    "haqq": "haqq",
    "batil": "batil",
    "noor": "noor", "nur": "noor",
    "zulm": "zulm",
    "adl": "adl",
}

# ============================================
# 4. MALAY TYPO DICTIONARY (150+ entries)
# ============================================

MS_TYPO_DICTIONARY = {
    # Common words & contractions
    "sy": "saya", "saye": "saya", "syg": "sayang",
    "awk": "awak", "awek": "awak", "ko": "kau", "kau": "kau",
    "aku": "aku", "akuu": "aku",
    "dia": "dia", "die": "dia", "dy": "dia",
    "kite": "kita", "kito": "kita", "kitorang": "kitorang",
    "org": "orang", "orang": "orang",
    "cmna": "macam mana", "cmne": "macam mana", "cmn": "macam mana",
    "macam": "macam", "mcm": "macam",
    "mana": "mana", "mna": "mana",
    "bila": "bila", "bile": "bila", "bla": "bila",
    "kenapa": "kenapa", "knpa": "kenapa", "napa": "kenapa",
    "apa": "apa", "pe": "apa", "pape": "apa apa",
    "mengapa": "mengapa",
    "berapa": "berapa", "brp": "berapa",
    "siapa": "siapa", "spe": "siapa",
    "yg": "yang", "yng": "yang",
    "utk": "untuk", "untk": "untuk",
    "dgn": "dengan", "dg": "dengan",
    "dlm": "dalam",
    "pd": "pada",
    "dr": "dari", "dri": "dari",
    "ke": "ke", "kek": "ke",
    "di": "di",
    "pun": "pun", "pn": "pun",
    "je": "saja", "ja": "saja", "jerr": "saja",
    "lah": "lah", "la": "lah", "leh": "leh", "meh": "meh",
    "kan": "kan", "kn": "kan",
    "kot": "kot",
    "nak": "nak", "nk": "nak", "nakk": "nak",
    "xde": "tak ada", "tade": "tak ada", "xdak": "tak ada",
    "xd": "tak ada", "takdak": "tak ada",
    "ada": "ada", "ade": "ada", "daa": "ada",
    "btul": "betul", "btol": "betul", "betoi": "betul",
    "salah": "salah", "slh": "salah",
    "baru": "baru", "bru": "baru",
    "lama": "lama",
    "banyak": "banyak", "bnyk": "banyak", "byk": "banyak",
    "sikit": "sikit", "skit": "sikit", "sket": "sikit",
    "sangat": "sangat", "sgt": "sangat", "sngt": "sangat",
    "terlalu": "terlalu",
    "bagus": "bagus",
    "cantik": "cantik", "cntk": "cantik",
    "comel": "comel", "cml": "comel",
    "lawak": "lawak",
    "sedih": "sedih",
    "marah": "marah",
    "takut": "takut",
    "gembira": "gembira",
    "letih": "letih", "ltih": "letih",
    "lapar": "lapar",
    "haus": "haus",
    "tidur": "tidur", "tdo": "tidur", "tdur": "tidur",
    "bangun": "bangun",
    "makan": "makan", "mkn": "makan",
    "minum": "minum",
    "pergi": "pergi", "pg": "pergi",
    "balik": "balik", "blk": "balik",
    "datang": "datang", "dtg": "datang",
    "tengok": "tengok", "tgk": "tengok", "tengo": "tengok",
    "dengar": "dengar", "dgr": "dengar",
    "cakap": "cakap", "ckp": "cakap",
    "faham": "faham", "fhm": "faham",
    "tahu": "tahu", "thu": "tahu",
    "lupa": "lupa",
    "ingat": "ingat",
    "suka": "suka", "suke": "suka",
    "benci": "benci",
    "cinta": "cinta", "cnta": "cinta",
    "kawan": "kawan", "kwn": "kawan",
    "keluarga": "keluarga",
    "rumah": "rumah", "rmh": "rumah",
    "kerja": "kerja", "krja": "kerja",
    "sekolah": "sekolah", "skolah": "sekolah",
    "duit": "duit",
    "masa": "masa",
    "hari": "hari", "hr": "hari",
    "minggu": "minggu",
    "bulan": "bulan", "bln": "bulan",
    "tahun": "tahun", "thn": "tahun",
    "pagi": "pagi", "pgi": "pagi",
    "petang": "petang",
    "malam": "malam", "mlm": "malam",
    "sekarang": "sekarang", "skrg": "sekarang", "skrang": "sekarang",
    "nanti": "nanti", "nnti": "nanti",
    "tadi": "tadi",
    "sebentar": "sebentar",
    "cepat": "cepat", "cpt": "cepat",
    "lambat": "lambat",
    "jauh": "jauh",
    "dekat": "dekat", "dkt": "dekat",
    "besar": "besar", "bsar": "besar",
    "kecil": "kecil", "kcl": "kecil",
    "panas": "panas",
    "sejuk": "sejuk",
    "tinggi": "tinggi",
    "rendah": "rendah",
    
    # Shortforms & internet slang
    "tq": "terima kasih", "thx": "terima kasih", "ty": "terima kasih",
    "xpa": "tak apa", "xpela": "tak apa lah", "xp": "tak apa",
    "sory": "maaf", "sori": "maaf", "sorry": "maaf",
    "ok": "ok", "oke": "ok", "okee": "ok",
    "btul": "betul", "btol": "betul",
    "tau": "tahu", "taw": "tahu",
    "tau": "tahu",
    "jg": "juga", "jga": "juga",
    "tdk": "tidak", "tk": "tidak", "tak": "tidak", "x": "tidak",
    "blm": "belum",
    "sdh": "sudah", "dah": "sudah",
    "bs": "bisa", "bole": "boleh", "blh": "boleh",
    "hrs": "harus", "msti": "mesti",
    "lg": "lagi", "lgi": "lagi",
    "krn": "kerana", "sbb": "sebab",
    "sbb": "sebab",
    "tp": "tapi", "tpi": "tapi",
    "jgk": "jugak", "juge": "jugak",
    "hrini": "hari ini",
    "hritu": "hari itu",
    "smalam": "semalam",
    "esok": "esok",
    "depa": "dia orang",
    "kito": "kita orang",
    "dorang": "dia orang",
    "korang": "kau orang",
    
    # SIDIX Malay
    "maqashid": "maqashid",
    "naskh": "naskh",
    "raudah": "raudah",
    "sanad": "sanad",
    "jariyah": "jariyah",
    "ihos": "ihos",
    "sociometer": "sociometer",
    "sidix": "sidix",
}

# ============================================
# 5. TAGALOG TYPO DICTIONARY (150+ entries)
# ============================================

TL_TYPO_DICTIONARY = {
    # Common greetings & expressions
    "kamusta": "kamusta", "musta": "kamusta", "kumusta": "kamusta",
    "mabuhay": "mabuhay",
    "salamat": "salamat", "slmt": "salamat",
    "maraming salamat": "maraming salamat", "maraming slmt": "maraming salamat",
    "opo": "opo", "op": "opo",
    "oo": "oo", "ooo": "oo",
    "hindi po": "hindi po", "hndi": "hindi", "hnd": "hindi",
    "wala po": "wala po", "wla": "wala",
    "paalam": "paalam",
    "ingat": "ingat",
    "ingat ka": "ingat ka",
    "god bless": "god bless",
    "selamat": "selamat",  # Borrowed from Malay
    
    # Pronouns
    "ako": "ako", "ku": "ako",
    "ikaw": "ikaw", "ka": "ikaw", "kaw": "ikaw",
    "siya": "siya", "nya": "siya", "niya": "siya",
    "tayo": "tayo",
    "kami": "kami",
    "kayo": "kayo", "kyo": "kayo",
    "sila": "sila", "sla": "sila",
    "akin": "akin", "sakin": "sa akin", "skn": "sa akin",
    "iyo": "iyo", "sayo": "sa iyo", "sy": "sa iyo",
    "atin": "atin", "satin": "sa atin",
    "kanila": "kanila", "sknla": "sa kanila",
    
    # Question words
    "pno": "paano", "panu": "paano", "pno": "paano",
    "ano": "ano", "nu": "ano",
    "sino": "sino", "snu": "sino",
    "saan": "saan", "sn": "saan",
    "bakit": "bakit", "bkt": "bakit", "bkit": "bakit",
    "kailan": "kailan", "kln": "kailan", "klan": "kailan",
    "gaano": "gaano", "gno": "gaano",
    "ilan": "ilan", "ilang": "ilang",
    "alin": "alin",
    
    # Common words
    "ang": "ang", "ung": "ang", "ng": "ng",
    "sa": "sa", "s": "sa",
    "na": "na", "n": "na",
    "at": "at",
    "ay": "ay",
    "para": "para", "pra": "para",
    "ngayon": "ngayon", "nyon": "ngayon",
    "bukas": "bukas", "bkas": "bukas",
    "kahapon": "kahapon", "khapon": "kahapon", "hapon": "kahapon",
    "mamaya": "mamaya", "mmya": "mamaya",
    "araw": "araw",
    "gabi": "gabi", "gbi": "gabi",
    "umaga": "umaga", "umg": "umaga",
    "tanghali": "tanghali",
    "madaling araw": "madaling araw",
    "taon": "taon", "taon": "taon",
    "buwan": "buwan",
    "linggo": "linggo",
    "marami": "marami", "marami": "marami", "mrmi": "marami",
    "kaunti": "kaunti", "konti": "kaunti",
    "lahat": "lahat",
    "iba": "iba",
    "sariwa": "sariwa",
    "luma": "luma",
    "bago": "bago", "bgo": "bago",
    "mabuti": "mabuti", "mbuti": "mabuti", "gud": "mabuti",
    "masama": "masama",
    "maganda": "maganda", "ganda": "maganda", "gnda": "maganda",
    "pangit": "pangit",
    "masaya": "masaya", "msya": "masaya",
    "malungkot": "malungkot", "lungkot": "malungkot",
    "malaki": "malaki", "laki": "malaki",
    "maliit": "maliit", "liit": "maliit",
    "haba": "haba",
    "iksi": "iksi",
    "mainit": "mainit", "init": "mainit",
    "malamig": "malamig", "lamig": "malamig",
    "bilis": "bilis",
    "mabagal": "mabagal", "mbagal": "mabagal",
    "taas": "taas",
    "baba": "baba",
    "malapit": "malapit", "lapit": "malapit",
    "malayo": "malayo",
    
    # Verbs & actions
    "kumain": "kumain", "kain": "kain", "kumakain": "kumakain",
    "uminom": "uminom", "inom": "inom",
    "tulog": "tulog", "tlog": "tulog", "matulog": "matulog",
    "gising": "gising", "mgising": "magising",
    "punta": "punta", "pnta": "punta", "pumunta": "pumunta",
    "kuha": "kuha", "kumuha": "kumuha",
    "bigay": "bigay", "magbigay": "magbigay",
    "sulat": "sulat", "magsulat": "magsulat",
    "basa": "basa", "bumasa": "bumasa", "magbasa": "magbasa",
    "tawa": "tawa", "tumawa": "tumawa",
    "iyak": "iyak", "umiyak": "umiyak", "cry": "iyak",
    "takbo": "takbo", "tumakbo": "tumakbo",
    "lakad": "lakad", "lumakad": "lumakad",
    "upo": "upo", "umupo": "umupo",
    "tayo": "tayo", "tumayo": "tumayo",
    "tignan": "tignan", "tngnan": "tignan", "tingnan": "tignan",
    "tingin": "tingin", "tgni": "tingin",
    "dinig": "dinig", "marinig": "marinig",
    "isip": "isip", "magisip": "magisip",
    "sabi": "sabi", "sbn": "sabihin", "sabihin": "sabihin",
    "gawa": "gawa", "gumawa": "gumawa",
    "hanap": "hanap", "humnap": "hanap", "maghanap": "maghanap",
    "turo": "turo", "tumuro": "tumuro",
    "tulong": "tulong", "tumulong": "tumulong",
    
    # Connectors & particles
    "pero": "pero", "pru": "pero", "peru": "pero",
    "kasi": "kasi", "kase": "kasi", "kc": "kasi",
    "dahil": "dahil",
    "pag": "pag", "kapag": "kapag",
    "nang": "nang",
    "daw": "daw", "raw": "raw",
    "din": "din", "rin": "rin",
    "po": "po", "ho": "ho",
    "ba": "ba",
    "yata": "yata",
    "ata": "ata",
    "kaya": "kaya",
    "sana": "sana",
    "talaga": "talaga", "tlga": "talaga", "tlg": "talaga",
    "lang": "lang", "lng": "lang",
    "muna": "muna",
    "pa": "pa",
    "naman": "naman",
    "siguro": "siguro", "cguro": "siguro", "bka": "baka",
    "baka": "baka",
    "kahit": "kahit",
    "habang": "habang",
    "dahil": "dahil", "dhil": "dahil",
    "para sa": "para sa",
    "tungkol": "tungkol",
    
    # Family & relationships
    "ate": "ate", "ateng": "ate",
    "kuya": "kuya",
    "lola": "lola",
    "lolo": "lolo",
    "nanay": "nanay", "nay": "nanay", "mama": "nanay",
    "tatay": "tatay", "tay": "tatay", "papa": "tatay",
    "pinsan": "pinsan",
    "kaibigan": "kaibigan", "kaibgan": "kaibigan", "friend": "kaibigan",
    "pare": "pare", "pares": "pare",
    "mars": "mars",
    "bes": "bes",
    
    # Shortforms
    "pls": "paki", "plz": "paki", "plss": "paki",
    "paki": "paki",
    "pwede": "pwede", "pde": "pwede", "pd": "pwede",
    "pwde": "pwede",
    "oo": "oo",
    "opo": "opo",
    "ayos": "ayos", "ays": "ayos",
    "ge": "sige", "sge": "sige",
    "nga": "nga",
    "wala": "wala", "wla": "wala",
    "meron": "meron", "myron": "meron", "mayron": "meron",
    "ayan": "ayan", "ayun": "ayun",
    "eto": "ito", "to": "ito", "2": "ito",
    "ganun": "ganun", "ganyan": "ganyan", "gnun": "ganun",
    "ganyn": "ganyan", "ganyan": "ganyan",
    "ganito": "ganito", "gnito": "ganito",
    "ganto": "ganto",
    "ganyan": "ganyan",
    "pano": "paano", "pnu": "paano",
    
    # SIDIX Tagalog
    "sidix": "sidix",
    "sociometer": "sociometer",
    "maqashid": "maqashid",
    "naskh": "naskh",
    "sanad": "sanad",
    "raudah": "raudah",
    "jariyah": "jariyah",
    "ihos": "ihos",
}

# ============================================
# 6. HINGLISH TYPO DICTIONARY (150+ entries)
# ============================================

HI_LATIN_TYPO_DICTIONARY = {
    # Greetings
    "namaste": "namaste", "namskar": "namaste", "namastey": "namaste",
    "salaam": "salaam", "salam": "salaam",
    "adaab": "adaab",
    "suprabhat": "suprabhat", "subh": "subh",
    "shubh ratri": "shubh ratri",
    "kaise ho": "kaise ho", "kaise": "kaise",
    "kya haal": "kya haal", "kya": "kya",
    "sab badhiya": "sab badhiya", "sab": "sab",
    "kya chal raha": "kya chal raha",
    
    # Common expressions
    "haan": "haan", "han": "haan", "hna": "haan", "hnji": "haan ji",
    "haan ji": "haan ji",
    "nahi": "nahi", "nai": "nahi", "nhn": "nahi", "nhin": "nahi",
    "na": "na",
    "theek hai": "theek hai", "theek": "theek", "thik": "theek", "tik": "theek",
    "badhiya": "badhiya", "bhadiya": "badhiya", "bdhiya": "badhiya",
    "acha": "acha", "accha": "acha", "acha hai": "acha hai",
    "bohot badhiya": "bohot badhiya",
    "koi baat nahi": "koi baat nahi", "koi": "koi",
    "dhanyavad": "dhanyavad", "dhanywaad": "dhanyavad",
    "shukriya": "shukriya", "shukria": "shukriya",
    "alvida": "alvida",
    "phir milenge": "phir milenge",
    "swagat": "swagat",
    "maaf karna": "maaf karna",
    
    # Pronouns
    "main": "main", "mai": "main", "me": "main",
    "tum": "tum", "tu": "tu", "tujhe": "tujhe", "tujh": "tujhe",
    "aap": "aap", "aapko": "aapko",
    "woh": "woh", "wo": "woh", "usne": "usne", "use": "use", "usko": "usko",
    "yeh": "yeh", "ye": "yeh", "isne": "isne", "ise": "ise", "isko": "isko",
    "ham": "ham", "hum": "hum", "hamne": "hamne", "hame": "hame", "hamko": "hamko",
    "unhone": "unhone", "unhe": "unhe", "unko": "unko",
    "inhone": "inhone", "inhe": "inhe", "inko": "inko",
    "mera": "mera", "meri": "meri", "mere": "mere", "merko": "mujhe",
    "tera": "tera", "teri": "teri", "tere": "tere", "terko": "tujhe",
    "uska": "uska", "uski": "uski", "uske": "uske",
    "iska": "iska", "iski": "iski", "iske": "iske",
    "hamara": "hamara", "hamari": "hamari", "hamare": "hamare",
    "sabka": "sabka", "sabki": "sabki", "sabke": "sabke",
    
    # Question words
    "kaise": "kaise", "kaisa": "kaisa", "kaisi": "kaisi",
    "kya": "kya", "kyun": "kyun", "kyon": "kyun", "kyu": "kyun",
    "kahan": "kahan", "kaha": "kahan", "kahaan": "kahan",
    "kab": "kab",
    "kitna": "kitna", "kitne": "kitne", "kitni": "kitni",
    "kaun": "kaun", "kon": "kaun",
    "kiske": "kiske", "kiska": "kiska",
    
    # Common words
    "hai": "hai", "hain": "hain", "hn": "hain",
    "tha": "tha", "thi": "thi", "the": "the",
    "hoga": "hoga", "hogi": "hogi", "honge": "honge",
    "raha": "raha", "rahi": "rahi", "rahe": "rahe",
    "kiya": "kiya", "kia": "kiya", "kiye": "kiya",
    "gaya": "gaya", "gya": "gaya", "gayi": "gayi", "gaye": "gaye",
    "aaya": "aaya", "ayi": "ayi", "aaye": "aaye",
    "chala": "chala", "chali": "chali",
    "bana": "bana", "bani": "bani", "bane": "bane",
    "dekha": "dekha", "dekhi": "dekhi", "dekhe": "dekhe",
    "suna": "suna", "suni": "suni",
    "bola": "bola", "boli": "boli", "bole": "bole",
    "liya": "liya", "liye": "liye", "li": "li",
    "diya": "diya", "diye": "diye", "di": "di",
    "mila": "mila", "mili": "mili",
    "hua": "hua", "hui": "hui", "hue": "hue",
    
    # Verbs
    "karna": "karna", "krna": "karna", "kro": "karo", "karo": "karo", "kare": "kare",
    "karti": "karti", "karta": "karta", "karte": "karte",
    "hona": "hona", "honi": "honi", "hone": "hone",
    "jana": "jana", "jani": "jani", "jane": "jane", "jao": "jao", "ja": "ja",
    "ana": "ana", "aana": "aana", "aao": "aao", "aa": "aa",
    "lena": "lena", "lo": "lo", "le": "le",
    "dena": "dena", "do": "do", "de": "de",
    "pina": "pina", "peena": "pina", "pi": "pi",
    "khana": "khana", "khana khana": "khana khana", "khao": "khao", "kha": "kha",
    "sona": "sona", "sone": "sone", "so": "so",
    "uthna": "uthna", "utho": "utho",
    "baithna": "baithna", "baith": "baith", "baitho": "baitho",
    "padhna": "padhna", "padho": "padho", "padh": "padh",
    "likhna": "likhna", "likho": "likho", "likh": "likh",
    "bolna": "bolna", "bolo": "bolo", "bol": "bol",
    "sunna": "sunna", "suno": "suno", "sun": "sun",
    "dekhna": "dekhna", "dekho": "dekho", "dekh": "dekh",
    "chahiye": "chahiye", "chahie": "chahiye",
    "sakna": "sakna", "sakti": "sakti", "sakta": "sakta",
    "chalega": "chalega", "chalegi": "chalegi",
    
    # Adjectives & adverbs
    "bahut": "bahut", "bht": "bahut", "bohot": "bahut",
    "jyada": "jyada", "zyada": "zyada", "zyada": "zyada", "jada": "jyada",
    "kam": "kam",
    "accha": "accha", "achha": "accha",
    "bura": "bura",
    "naya": "naya", "nayi": "naya", "naye": "naya",
    "purana": "purana", "purani": "purana",
    "sach": "sach", "sacha": "sacha",
    "jhooth": "jhooth",
    "saaf": "saaf",
    "ganda": "ganda",
    "asli": "asli",
    "nakli": "nakli",
    "sasta": "sasta",
    "mehnga": "mehnga", "mahnga": "mehnga",
    "thanda": "thanda",
    "garam": "garam",
    "jaldi": "jaldi",
    "dheere": "dheere",
    "seedha": "seedha",
    "ultha": "ultha",
    
    # Connectors
    "aur": "aur", "or": "aur", "n": "aur",
    "lekin": "lekin", "lekin": "lekin", "par": "par", "magar": "magar",
    "kyunki": "kyunki", "kynki": "kyunki",
    "agar": "agar",
    "toh": "toh", "to": "to",
    "jab": "jab",
    "tak": "tak",
    "se": "se",
    "mein": "mein", "mai": "mein",
    "par": "par", "pe": "par",
    "ke liye": "ke liye",
    "ke baad": "ke baad",
    "ke pehle": "ke pehle",
    "ke sath": "ke sath",
    "ke bina": "ke bina",
    "ke bare mein": "ke bare mein",
    "ki": "ki", "ka": "ka", "ke": "ke",
    
    # Quantifiers
    "ek": "ek", "do": "do", "teen": "teen", "char": "char", "paanch": "paanch",
    "cheh": "cheh", "saat": "saat", "aath": "aath", "nau": "nau", "das": "das",
    "sab": "sab", "sabhi": "sabhi",
    "kuch": "kuch",
    "koi": "koi",
    "har": "har",
    "aur": "aur", "koi aur": "koi aur",
    
    # SIDIX Hinglish
    "sidix": "sidix",
    "sociometer": "sociometer",
    "maqashid": "maqashid",
    "naskh": "naskh",
    "sanad": "sanad",
    "raudah": "raudah",
    "jariyah": "jariyah",
    "ihos": "ihos",
    "dil": "dil",
    "dimag": "dimag",
    "mann": "mann",
    "aatma": "aatma",
    
    # Common slang
    "yaar": "yaar",
    "bhai": "bhai", "bhaiya": "bhaiya", "bhayya": "bhaiya",
    "behen": "behen", "didi": "didi",
    "chalo": "chalo",
    "ruk": "ruk", "ruko": "ruko",
    "bas": "bas",
    "arre": "arre", "arey": "arre", "are": "arre",
    "accha ji": "accha ji",
    "hmm": "hmm", "hmmm": "hmm",
    " ji ": " ji ",
    "re": "re",
    "na": "na",
    "matlab": "matlab",
    "samajh": "samajh", "samjho": "samjho",
    "pata": "pata",
    "malum": "malum",
}


# ============================================
# QWERTY PROXIMITY MAP (for all Latin-script languages)
# ============================================

QWERTY_PROXIMITY = {
    'a': 'qwsz',
    'b': 'vghn',
    'c': 'xdfv',
    'd': 'serfcx',
    'e': 'wsdr',
    'f': 'drtgvc',
    'g': 'ftyhbv',
    'h': 'gyujnb',
    'i': 'ujko',
    'j': 'huiknm',
    'k': 'jiolm',
    'l': 'kop',
    'm': 'njk',
    'n': 'bhjm',
    'o': 'iklp',
    'p': 'ol',
    'q': 'wa',
    'r': 'edft',
    's': 'wedxza',
    't': 'rfgy',
    'u': 'yhji',
    'v': 'cfgb',
    'w': 'qase',
    'x': 'zsdc',
    'y': 'tghu',
    'z': 'asx',
}
```

### 3.2 Universal Typo Corrector Implementation

```python
# brain/multilingual/universal_corrector.py

import re
from typing import Dict, Tuple, List, Optional
from enum import Enum

from brain.multilingual.language_detector import LanguageCode, detector
from brain.multilingual.typo_dictionaries import (
    EN_TYPO_DICTIONARY,
    AR_LATIN_TYPO_DICTIONARY,
    MS_TYPO_DICTIONARY,
    TL_TYPO_DICTIONARY,
    HI_LATIN_TYPO_DICTIONARY,
    QWERTY_PROXIMITY,
)
from brain.typo.dictionaries import TYPO_DICTIONARY as ID_TYPO_DICTIONARY


class UniversalTypoCorrector:
    """
    Universal typo corrector untuk 6+ bahasa.
    Auto-detect language lalu apply dictionary yang sesuai.
    """
    
    def __init__(self):
        # Map language code ke dictionary
        self.dictionaries = {
            LanguageCode.ID: ID_TYPO_DICTIONARY,
            LanguageCode.EN: EN_TYPO_DICTIONARY,
            LanguageCode.AR_LATIN: AR_LATIN_TYPO_DICTIONARY,
            LanguageCode.MS: MS_TYPO_DICTIONARY,
            LanguageCode.TL: TL_TYPO_DICTIONARY,
            LanguageCode.HI_LATIN: HI_LATIN_TYPO_DICTIONARY,
        }
        
        self.qwerty = QWERTY_PROXIMITY
        
        # Minimum word length untuk fuzzy matching
        self.MIN_WORD_LENGTH = 3
        self.MAX_LEVENSHTEIN = 2
    
    def correct(self, text: str, forced_language: Optional[LanguageCode] = None) -> Dict:
        """
        Correct typos dalam text — auto-detect atau forced language.
        
        Returns:
            {
                "original": str,
                "corrected": str,
                "language": LanguageCode,
                "corrections": [{
                    "original_word": str,
                    "corrected_word": str,
                    "type": str,  # "dictionary" | "fuzzy" | "qwerty"
                    "language": LanguageCode
                }],
                "confidence": float
            }
        """
        original = text
        
        # Step 1: Detect language (kalau tidak forced)
        if forced_language:
            primary_lang = forced_language
            lang_confidence = 1.0
        else:
            lang_result = detector.detect(text)
            primary_lang = lang_result["primary_language"]
            lang_confidence = lang_result["detected_languages"][0]["confidence"] if lang_result["detected_languages"] else 0.5
        
        # Step 2: Get dictionary untuk detected language
        dictionary = self.dictionaries.get(primary_lang, {})
        
        # Step 3: Tokenize
        tokens = self._tokenize(text)
        
        # Step 4: Correct each token
        corrected_tokens = []
        corrections_log = []
        
        for token in tokens:
            corrected, correction_type = self._correct_token(
                token, primary_lang, dictionary
            )
            corrected_tokens.append(corrected)
            
            if correction_type and token.lower() != corrected.lower():
                corrections_log.append({
                    "original_word": token,
                    "corrected_word": corrected,
                    "type": correction_type,
                    "language": primary_lang.value
                })
        
        corrected_text = self._detokenize(corrected_tokens)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(
            len(corrections_log), len(tokens), lang_confidence
        )
        
        return {
            "original": original,
            "corrected": corrected_text,
            "language": primary_lang,
            "corrections": corrections_log,
            "confidence": confidence,
            "tokens_total": len(tokens),
            "tokens_corrected": len(corrections_log)
        }
    
    def _correct_token(self, token: str, lang: LanguageCode, dictionary: Dict) -> Tuple[str, Optional[str]]:
        """
        Correct single token.
        
        Strategy:
        1. Exact match in dictionary
        2. Case-insensitive match
        3. Fuzzy match (Levenshtein)
        4. QWERTY proximity match
        5. Keep original (cannot correct)
        """
        if not token or len(token) < 2:
            return token, None
        
        # Preserve case info
        original_case = token
        token_lower = token.lower()
        
        # 1. Exact match
        if token_lower in dictionary:
            return self._restore_case(original_case, dictionary[token_lower]), "dictionary"
        
        # 2. Try all dictionaries (cross-language matching)
        # This helps with mixed-language input
        for dict_lang, dict_data in self.dictionaries.items():
            if token_lower in dict_data:
                return self._restore_case(original_case, dict_data[token_lower]), "dictionary"
        
        # 3. Fuzzy match dalam primary dictionary
        if len(token_lower) >= self.MIN_WORD_LENGTH:
            fuzzy_match = self._fuzzy_match(token_lower, dictionary)
            if fuzzy_match:
                return self._restore_case(original_case, fuzzy_match), "fuzzy"
        
        # 4. QWERTY proximity match (untuk typo keyboard)
        if len(token_lower) >= self.MIN_WORD_LENGTH:
            qwerty_match = self._qwerty_match(token_lower, dictionary)
            if qwerty_match:
                return self._restore_case(original_case, qwerty_match), "qwerty"
        
        # 5. Keep original
        return token, None
    
    def _fuzzy_match(self, token: str, dictionary: Dict, max_distance: int = 2) -> Optional[str]:
        """Find closest match menggunakan Levenshtein distance."""
        best_match = None
        best_distance = max_distance + 1
        
        for key, value in dictionary.items():
            # Only compare words of similar length
            if abs(len(key) - len(token)) > max_distance:
                continue
            
            distance = self._levenshtein(token, key)
            if distance <= max_distance and distance < best_distance:
                best_distance = distance
                best_match = value
        
        return best_match
    
    def _qwerty_match(self, token: str, dictionary: Dict) -> Optional[str]:
        """
        Find match berdasarkan QWERTY proximity.
        Kalau user ngetik 'gpn' mungkin maksudnya 'gimana' (i→p typo).
        """
        best_match = None
        best_score = 0
        
        for key, value in dictionary.items():
            if len(key) != len(token):
                continue
            
            score = 0
            for i, (tc, kc) in enumerate(zip(token, key)):
                if tc == kc:
                    score += 2  # Exact match
                elif tc in self.qwerty.get(kc, ''):
                    score += 1  # QWERTY neighbor
            
            # Threshold: at least 60% match
            if score / (len(token) * 2) > 0.4 and score > best_score:
                best_score = score
                best_match = value
        
        return best_match
    
    def _levenshtein(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance."""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text — preserve structure."""
        # Split by whitespace tapi preserve punctuation sebagai separate tokens
        tokens = []
        current = ""
        
        for char in text:
            if char.isalnum() or char in "'_-":
                current += char
            else:
                if current:
                    tokens.append(current)
                    current = ""
                tokens.append(char)  # Punctuation as separate token
        
        if current:
            tokens.append(current)
        
        return tokens
    
    def _detokenize(self, tokens: List[str]) -> str:
        """Reconstruct text dari tokens."""
        result = ""
        for i, token in enumerate(tokens):
            if i > 0 and token not in ".,;:!?" and tokens[i-1] not in "(":
                result += " "
            result += token
        return result
    
    def _restore_case(self, original: str, corrected: str) -> str:
        """Restore case pattern dari original ke corrected."""
        if original.isupper():
            return corrected.upper()
        elif original[0].isupper() if original else False:
            return corrected.capitalize()
        return corrected.lower()
    
    def _calculate_confidence(self, corrections: int, total: int, lang_conf: float) -> float:
        """Calculate confidence score."""
        if total == 0:
            return 1.0
        
        # Base: language detection confidence
        confidence = lang_conf * 0.6
        
        # Add: correction ratio
        correction_ratio = 1.0 - (corrections / total) * 0.3
        confidence += correction_ratio * 0.4
        
        return max(0.0, min(1.0, confidence))


# Singleton
corrector = UniversalTypoCorrector()
```

---

## LAYER 4: CROSS-LINGUAL SEMANTIC MATCHER

```python
# brain/multilingual/semantic_matcher.py

import numpy as np
from typing import Dict, List, Optional

class CrossLingualSemanticMatcher:
    """
    Semantic matcher yang bekerja across languages.
    Menggunakan embeddings untuk menangkap intent regardless of language.
    """
    
    def __init__(self, embedding_model):
        """
        embedding_model: Model embeddings lokal (e.g., sentence-transformers)
        """
        self.embeddings = embedding_model
        
        # Intent patterns dalam multiple languages
        self.intent_patterns = {
            # Each intent has patterns in multiple languages
            "greeting": {
                LanguageCode.ID: ["halo", "hai", "selamat pagi", "apa kabar"],
                LanguageCode.EN: ["hello", "hi", "hey", "good morning", "how are you"],
                LanguageCode.AR_LATIN: ["marhaba", "salam", "assalamualaikum", "kifah"],
                LanguageCode.MS: ["hai", "helo", "selamat pagi", "apa khabar"],
                LanguageCode.TL: ["kamusta", "hello", "musta", "mabuhay"],
                LanguageCode.HI_LATIN: ["namaste", "kaise ho", "salaam", "hello"],
            },
            "farewell": {
                LanguageCode.ID: ["dadah", "selamat tinggal", "sampai jumpa"],
                LanguageCode.EN: ["bye", "goodbye", "see you", "take care"],
                LanguageCode.AR_LATIN: ["ma3leh", "khalas", "salam"],
                LanguageCode.MS: ["bye", "jumpa lagi", "jaga diri"],
                LanguageCode.TL: ["paalam", "ingat ka", "bye"],
                LanguageCode.HI_LATIN: ["alvida", "phir milenge", "bye"],
            },
            "thanks": {
                LanguageCode.ID: ["terima kasih", "makasih", "thanks"],
                LanguageCode.EN: ["thank you", "thanks", "appreciate it"],
                LanguageCode.AR_LATIN: ["shukran", "jazakallah", "barakallah"],
                LanguageCode.MS: ["terima kasih", "tq", "thanks"],
                LanguageCode.TL: ["salamat", "salamat po", "thank you"],
                LanguageCode.HI_LATIN: ["dhanyavad", "shukriya", "thank you"],
            },
            "help_request": {
                LanguageCode.ID: ["tolong", "bantu", "bantuan", "butuh bantuan"],
                LanguageCode.EN: ["help", "help me", "i need help", "assist"],
                LanguageCode.AR_LATIN: ["mumkin", "min fadlak", "law samaht"],
                LanguageCode.MS: ["tolong", "bantu", "help"],
                LanguageCode.TL: ["tulong", "help", "paki"],
                LanguageCode.HI_LATIN: ["madad", "help", "batao"],
            },
            "setup_gpu": {
                LanguageCode.ID: ["setup gpu", "install gpu", "gpu server", "konfigurasi gpu"],
                LanguageCode.EN: ["setup gpu", "install gpu", "gpu configuration", "nvidia"],
                LanguageCode.AR_LATIN: ["gpu", "server"],
                LanguageCode.MS: ["setup gpu", "gpu server"],
                LanguageCode.TL: ["gpu setup", "install gpu"],
                LanguageCode.HI_LATIN: ["gpu setup", "gpu install"],
            },
            "install_plugin": {
                LanguageCode.ID: ["install plugin", "pasang plugin", "setup mcp"],
                LanguageCode.EN: ["install plugin", "setup mcp", "chrome extension"],
                LanguageCode.AR_LATIN: ["plugin", "mcp"],
                LanguageCode.MS: ["install plugin", "plugin setup"],
                LanguageCode.TL: ["install plugin", "plugin"],
                LanguageCode.HI_LATIN: ["plugin install", "plugin setup"],
            },
            "maqashid_explain": {
                LanguageCode.ID: ["maqashid", "filter maqashid", "creative mode"],
                LanguageCode.EN: ["maqashid", "maqashid filter", "maqashid mode"],
                LanguageCode.AR_LATIN: ["maqashid"],
                LanguageCode.MS: ["maqashid"],
                LanguageCode.TL: ["maqashid"],
                LanguageCode.HI_LATIN: ["maqashid"],
            },
            "sociometer_status": {
                LanguageCode.ID: ["sociometer status", "progress", "sprint"],
                LanguageCode.EN: ["sociometer", "status", "progress", "sprint"],
                LanguageCode.AR_LATIN: ["sociometer"],
                LanguageCode.MS: ["sociometer"],
                LanguageCode.TL: ["sociometer"],
                LanguageCode.HI_LATIN: ["sociometer"],
            },
            "persona_select": {
                LanguageCode.ID: ["pilih persona", "ganti persona", "mode"],
                LanguageCode.EN: ["select persona", "change persona", "persona mode"],
                LanguageCode.AR_LATIN: ["persona"],
                LanguageCode.MS: ["persona"],
                LanguageCode.TL: ["persona"],
                LanguageCode.HI_LATIN: ["persona"],
            },
        }
    
    async def match_intent(self, text: str, detected_language: LanguageCode) -> Dict:
        """
        Match text ke intent — works across languages.
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "matched_pattern": str,
                "language": str
            }
        """
        # Generate embedding untuk input
        input_embedding = await self.embeddings.embed(text)
        
        best_intent = None
        best_confidence = 0.0
        best_pattern = None
        best_lang = None
        
        # Check all intents across all languages
        for intent, lang_patterns in self.intent_patterns.items():
            for lang, patterns in lang_patterns.items():
                for pattern in patterns:
                    pattern_embedding = await self.embeddings.embed(pattern)
                    similarity = self._cosine_similarity(input_embedding, pattern_embedding)
                    
                    # Boost confidence kalau language match
                    if lang == detected_language:
                        similarity *= 1.1
                    
                    if similarity > best_confidence:
                        best_confidence = similarity
                        best_intent = intent
                        best_pattern = pattern
                        best_lang = lang
        
        return {
            "intent": best_intent or "unknown",
            "confidence": min(1.0, best_confidence),
            "matched_pattern": best_pattern or "",
            "language": best_lang.value if best_lang else "unknown"
        }
    
    def _cosine_similarity(self, v1, v2) -> float:
        """Calculate cosine similarity."""
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


from brain.multilingual.language_detector import LanguageCode
```

---

## LAYER 5: CULTURAL CONTEXT RESPONDER

```python
# brain/multilingual/cultural_responder.py

from enum import Enum
from typing import Dict, Optional

from brain.multilingual.language_detector import LanguageCode

class CulturalResponder:
    """
    Response generator yang respect cultural communication style.
    Responds in the user's detected language with appropriate politeness.
    """
    
    # Greeting patterns per language
    GREETINGS = {
        LanguageCode.ID: ["Halo!", "Hai!", "Selamat datang!"],
        LanguageCode.EN: ["Hello!", "Hi there!", "Welcome!"],
        LanguageCode.AR_LATIN: ["Marhaba!", "Assalamualaikum!", "Ahlan!"],
        LanguageCode.MS: ["Hai!", "Selamat datang!", "Apa khabar!"],
        LanguageCode.TL: ["Kamusta!", "Mabuhay!", "Hello!"],
        LanguageCode.HI_LATIN: ["Namaste!", "Aap kaise hain!", "Shubh din!"],
    }
    
    # Clarification prompts per language
    CLARIFICATION_PROMPTS = {
        LanguageCode.ID: """Maaf, saya belum sepenuhnya mengerti maksud Anda.

Anda menulis: "{original}"

Bisakah Anda menjelaskan dengan kata lain? Atau pilih topik:
- Setup GPU / Server
- Install Plugin / MCP
- Maqashid / Naskh / Raudah
- Persona (AYMAN, ABOO, OOMAR, ALEY, UTZ)
- SIDIX System""",
        
        LanguageCode.EN: """Sorry, I didn't fully understand your message.

You wrote: "{original}"

Could you rephrase? Or pick a topic:
- GPU / Server Setup
- Plugin / MCP Installation
- Maqashid / Naskh / Raudah
- Persona (AYMAN, ABOO, OOMAR, ALEY, UTZ)
- SIDIX System""",
        
        LanguageCode.AR_LATIN: """Ma3leh, I didn't fully understand.

You wrote: "{original}"

Can you explain more? Or choose a topic:
- GPU / Server Setup
- Plugin / MCP
- Maqashid / Naskh / Raudah
- Persona
- SIDIX System""",
        
        LanguageCode.MS: """Maaf, saya tidak fully faham.

You wrote: "{original}"

Boleh explain lagi? Atau pilih topik:
- Setup GPU / Server
- Install Plugin / MCP
- Maqashid / Naskh / Raudah
- Persona
- SIDIX System""",
        
        LanguageCode.TL: """Pasensya, hindi ko fully na-gets.

You wrote: "{original}"

Paki-explain ulit? Or pumili ng topic:
- GPU / Server Setup
- Plugin / MCP Install
- Maqashid / Naskh / Raudah
- Persona
- SIDIX System""",
        
        LanguageCode.HI_LATIN: """Maaf, mujhe poora samajh nahi aaya.

You wrote: "{original}"

Aap dobara explain kar sakte hain? Ya topic chune:
- GPU / Server Setup
- Plugin / MCP Install
- Maqashid / Naskh / Raudah
- Persona
- SIDIX System""",
    }
    
    # Low-confidence note (appended to response)
    LOW_CONFIDENCE_NOTES = {
        LanguageCode.ID: "\n\n*(Jika ini bukan yang Anda maksud, silakan ketik ulang.)*",
        LanguageCode.EN: "\n\n*(If this isn't what you meant, please rephrase.)*",
        LanguageCode.AR_LATIN: "\n\n*(If this isn't what you meant, please explain again.)*",
        LanguageCode.MS: "\n\n*(Kalau ini bukan yang you maksud, please type again.)*",
        LanguageCode.TL: "\n\n*(Kung hindi ito ang ibig mong sabihin, paki-type ulit.)*",
        LanguageCode.HI_LATIN: "\n\n*(Agar yeh woh nahi jo aapne kaha, toh dobara likhein.)*",
    }
    
    def get_greeting(self, lang: LanguageCode) -> str:
        """Get culturally appropriate greeting."""
        import random
        greetings = self.GREETINGS.get(lang, self.GREETINGS[LanguageCode.EN])
        return random.choice(greetings)
    
    def get_clarification(self, lang: LanguageCode, original_text: str) -> str:
        """Get clarification prompt in user's language."""
        template = self.CLARIFICATION_PROMPTS.get(
            lang, 
            self.CLARIFICATION_PROMPTS[LanguageCode.EN]
        )
        return template.format(original=original_text)
    
    def get_low_confidence_note(self, lang: LanguageCode) -> str:
        """Get low-confidence note in user's language."""
        return self.LOW_CONFIDENCE_NOTES.get(lang, "")
    
    def wrap_response(self, 
                     base_response: str, 
                     lang: LanguageCode,
                     confidence: float,
                     original_text: str) -> str:
        """
        Wrap base response dengan cultural context.
        
        Rules:
        1. Don't shame user for typos
        2. Respond in detected language
        3. Add clarification note only if low confidence
        4. Never correct user's grammar publicly
        """
        if confidence >= 0.85:
            return base_response
        elif confidence >= 0.60:
            return base_response + self.get_low_confidence_note(lang)
        else:
            return self.get_clarification(lang, original_text)


# Singleton
cultural_responder = CulturalResponder()
```

---

## INTEGRASI: Universal Multilingual Pipeline

```python
# brain/multilingual/pipeline.py

from typing import Dict

from brain.multilingual.language_detector import detector, LanguageCode
from brain.multilingual.universal_corrector import corrector
from brain.multilingual.semantic_matcher import CrossLingualSemanticMatcher
from brain.multilingual.cultural_responder import cultural_responder
from brain.jiwa.orchestrator import JiwaOrchestrator


class MultilingualPipeline:
    """
    End-to-end multilingual pipeline.
    
    Flow:
    1. Detect language
    2. Correct typos (language-specific)
    3. Match intent (cross-lingual)
    4. Process via Jiwa Orchestrator
    5. Respond in user's language with cultural context
    """
    
    def __init__(self, embedding_model, jiwa_orchestrator: JiwaOrchestrator):
        self.detector = detector
        self.corrector = corrector
        self.semantic = CrossLingualSemanticMatcher(embedding_model)
        self.cultural = cultural_responder
        self.jiwa = jiwa_orchestrator
    
    async def process(self, request: Dict) -> Dict:
        """
        Process multilingual request.
        
        request = {
            "question": str,  # Raw user input (with typos, any language)
            "persona": str,   # Optional
            "platform": str,  # Optional
        }
        
        Returns:
            {
                "response": str,
                "detected_language": str,
                "corrected_text": str,
                "intent": str,
                "confidence": float,
                "corrections_made": [dict]
            }
        """
        original_question = request["question"]
        
        # ===== LAYER 1-2: Language Detection =====
        lang_result = self.detector.detect(original_question)
        detected_lang = lang_result["primary_language"]
        
        # ===== LAYER 3: Typo Correction =====
        correction_result = self.corrector.correct(original_question, detected_lang)
        corrected_text = correction_result["corrected"]
        
        # ===== LAYER 4: Intent Matching =====
        intent_result = await self.semantic.match_intent(corrected_text, detected_lang)
        
        # ===== PROCESS VIA JIWA ORCHESTRATOR =====
        # Update request dengan corrected text
        processed_request = {
            **request,
            "question": corrected_text,
            "original_question": original_question,
            "detected_language": detected_lang.value,
            "intent": intent_result["intent"]
        }
        
        # Get response dari Jiwa (7 pillars)
        jiwa_result = await self.jiwa.process(processed_request)
        base_response = jiwa_result["response"]
        
        # ===== LAYER 5: Cultural Response =====
        # Calculate overall confidence
        overall_confidence = (
            correction_result["confidence"] * 0.4 + 
            intent_result["confidence"] * 0.6
        )
        
        # Wrap dengan cultural context
        final_response = self.cultural.wrap_response(
            base_response=base_response,
            lang=detected_lang,
            confidence=overall_confidence,
            original_text=original_question
        )
        
        return {
            "response": final_response,
            "detected_language": detected_lang.value,
            "corrected_text": corrected_text,
            "intent": intent_result["intent"],
            "confidence": overall_confidence,
            "corrections_made": correction_result["corrections"],
            "layers_used": jiwa_result.get("layers_used", ["parametric"]),
            "iterations": jiwa_result.get("iterations", 1),
            "health": jiwa_result.get("health", "healthy"),
        }


# Singleton (initialized at startup)
multilingual_pipeline: MultilingualPipeline = None

def init_pipeline(embedding_model, jiwa_orchestrator: JiwaOrchestrator):
    """Initialize multilingual pipeline."""
    global multilingual_pipeline
    multilingual_pipeline = MultilingualPipeline(embedding_model, jiwa_orchestrator)
    return multilingual_pipeline
```

---

## FILE STRUCTURE

```
brain/
├── multilingual/
│   ├── __init__.py
│   ├── script_detector.py        # LAYER 1: Script detection
│   ├── language_detector.py      # LAYER 2: Language detection (6+ languages)
│   ├── typo_dictionaries.py      # LAYER 3: Typo dictionaries (6 languages)
│   ├── universal_corrector.py    # LAYER 3: Universal typo corrector
│   ├── semantic_matcher.py       # LAYER 4: Cross-lingual intent matching
│   ├── cultural_responder.py     # LAYER 5: Cultural response generator
│   └── pipeline.py               # END-TO-END: Multilingual pipeline
```

---

## CONTOH: Typo dalam 6 Bahasa

### Indonesia
```
Input:  "gmana cra stp gpu d srvr?"
Detect: id (confidence: 0.95)
Correct: "gimana cara setup gpu di server"
Intent:  setup_gpu (confidence: 0.92)
Respond: "Berikut cara setup GPU di server..."
```

### English
```
Input:  "hw do i stp gpu on srvr pls?"
Detect: en (confidence: 0.93)
Correct: "how do i setup gpu on server please"
Intent:  setup_gpu (confidence: 0.94)
Respond: "Here's how to setup GPU on your server..."
```

### Arabizi
```
Input:  "kifah nstp gpu f srvr?"
Detect: ar-latin (confidence: 0.88)
Correct: "kifah nstp gpu fi server"
Intent:  setup_gpu (confidence: 0.85)
Respond: "Habibi, here's how to setup GPU..." (English response for Arabizi)
```

### Malay
```
Input:  "cmna nk stp gpu dlm srvr?"
Detect: ms (confidence: 0.91)
Correct: "macam mana nak setup gpu dalam server"
Intent:  setup_gpu (confidence: 0.90)
Respond: "Macam ni lah cara setup GPU dalam server..."
```

### Tagalog
```
Input:  "pno mg stp ng gpu s srvr?"
Detect: tl (confidence: 0.87)
Correct: "paano mag setup ng gpu sa server"
Intent:  setup_gpu (confidence: 0.86)
Respond: "Ganito ang paraan para mag-setup ng GPU sa server..."
```

### Hinglish
```
Input:  "gpu server me kaise setup kare?"
Detect: hi-latin (confidence: 0.90)
Correct: "gpu server mein kaise setup kare"
Intent:  setup_gpu (confidence: 0.91)
Respond: "Bhai, GPU server mein setup karne ka tarika..."
```

---

## STATISTIK: 1,000+ TYPO PATTERNS

| Bahasa | Kode | Dictionary Entries | Slang/Abbrev |
|--------|------|-------------------|--------------|
| Indonesian | `id` | 200+ | gmn, tdk, dg, jg, bgt, dll |
| English | `en` | 300+ | pls, idk, btw, asap, brb, lol |
| Arabizi | `ar-latin` | 200+ | kifah, shlon, ya3ni, inshallah |
| Malay | `ms` | 150+ | cmna, nk, xde, btul, tq |
| Tagalog | `tl` | 150+ | pno, mg, tlg, gnun, sge |
| Hinglish | `hi-latin` | 150+ | kaise, kya, nahi, haan, theek |

**Total: 1,150+ typo patterns across 6 languages**

---

## PROMPT UNTUK CURSOR

```
Tugas: Implementasikan MULTILINGUAL TYPO FRAMEWORK.

1. Buat folder: brain/multilingual/
2. Buat semua file sesuai struktur di atas
3. Isi typo_dictionaries.py dengan 6 bahasa (sudah lengkap di spec)
4. Implementasikan pipeline end-to-end
5. Integrasikan ke brain/jiwa/orchestrator.py (ganti entry point)
6. Test dengan contoh typo dari 6 bahasa

Prioritas:
- Indonesia + English (paling sering dipakai)
- Arabizi + Malay (komunitas Muslim)
- Tagalog + Hinglish (ekspansi)

Aturan:
- Standing alone: pure Python, no external API
- Self-contained: bisa jalan tanpa embedding model (fallback ke keyword matching)
- Auto: language detection otomatis, no manual switch
- Respectful: never shame user for typos
```

---

*Framework ini memastikan SIDIX mengerti user dari manapun — dalam bahasa apapun, dengan typo seberat apapun.*
*SIDIX tidak menuntut kesempurnaan. SIDIX hadir untuk melayani.*
