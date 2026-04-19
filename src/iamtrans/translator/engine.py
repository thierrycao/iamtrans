"""翻译引擎模块

三引擎 + 双词典，一个类搞定：

翻译引擎（无需 API key）：
- youdao: 有道翻译 —— 默认引擎，中文用户友好
- google: Google Translate —— 稳定可靠
- mymemory: MyMemory —— 每日 5000 字符免费额度

词典查询（智能语言检测）：
- 英文单词 → ec 字段 → UK/US 音标 + 词性 + 释义
- 中文单字 → newhh 字段 → 拼音 + 词性 + 例句

核心方法：
- translate(): 基础翻译，手动指定语言
- smart_translate(): 智能翻译，自动检测并切换目标
- lookup_dictionary(): 词典查询，根据语言自动选择 API

Example:
    >>> engine = TranslatorEngine('youdao')
    >>> engine.translate('Hello', source='en', target='zh-CN')
    '你好'

    >>> # 智能模式：自动检测语言
    >>> engine.smart_translate('你好')  # 中文 → 英文
    'Hello'
    >>> engine.smart_translate('Hello')  # 英文 → 中文
    '你好'

    >>> # 词典查询
    >>> result = TranslatorEngine.lookup_dictionary('hello')
    >>> result.phonetic  # UK[həˈləʊ] US[həˈloʊ]
    >>> result.definitions[0]['definition']  # '喂，你好...'
"""
import json
import urllib.request
import urllib.error
import urllib.parse
import re
from typing import Optional, List, Dict
from deep_translator import GoogleTranslator, MyMemoryTranslator

# 支持的词典源
DICTIONARY_SOURCES = {
    'free': 'Free Dictionary',
    'youdao': '有道词典',
}

# 默认词典源
DEFAULT_DICT_SOURCE = 'youdao'

# 支持的翻译引擎
ENGINES = {
    'youdao': '有道翻译',
    'google': 'Google Translate',
    'mymemory': 'MyMemory',
}

# 默认翻译引擎
DEFAULT_ENGINE = 'youdao'

# 常用语言代码映射（显示用）
LANGUAGES = {
    'auto': '自动检测',
    'zh-CN': '中文(简体)',
    'zh-TW': '中文(繁体)',
    'en': 'English',
    'ja': '日本語',
    'ko': '한국어',
    'fr': 'Français',
    'de': 'Deutsch',
    'es': 'Español',
    'pt': 'Português',
    'ru': 'Русский',
    'it': 'Italiano',
    'ar': 'العربية',
    'th': 'ภาษาไทย',
    'vi': 'Tiếng Việt',
    'nl': 'Nederlands',
    'pl': 'Polski',
    'tr': 'Türkçe',
    'id': 'Bahasa Indonesia',
    'ms': 'Bahasa Melayu',
    'hi': 'हिन्दी',
    'bn': 'বাংলা',
    'uk': 'Українська',
    'cs': 'Čeština',
    'sv': 'Svenska',
    'da': 'Dansk',
    'fi': 'Suomi',
    'no': 'Norsk',
    'hu': 'Magyar',
    'ro': 'Română',
    'el': 'Ελληνικά',
    'he': 'עברית',
}

# MyMemory 语言代码映射（MyMemory 使用完整格式）
MYMEMORY_LANG_MAP = {
    'auto': 'english',  # 自动检测时默认英文
    'zh-CN': 'chinese simplified',
    'zh-TW': 'chinese traditional',
    'en': 'english',
    'ja': 'japanese',
    'ko': 'korean',
    'fr': 'french',
    'de': 'german',
    'es': 'spanish',
    'pt': 'portuguese',
    'ru': 'russian',
    'it': 'italian',
    'ar': 'arabic',
    'th': 'thai',
    'vi': 'vietnamese',
    'nl': 'dutch',
    'pl': 'polish',
    'tr': 'turkish',
    'id': 'indonesian',
    'ms': 'malay',
    'hi': 'hindi',
    'bn': 'bengali',
    'uk': 'ukrainian',
    'cs': 'czech',
    'sv': 'swedish',
    'da': 'danish',
    'fi': 'finnish',
    'no': 'norwegian bokmål',
    'hu': 'hungarian',
    'ro': 'romanian',
    'el': 'greek',
    'he': 'hebrew',
}


class DictionaryResult:
    """词典查询结果"""

    def __init__(self, word: str):
        self.word = word
        self.definitions: List[Dict] = []  # [{partOfSpeech, definition, example}]
        self.phonetic: str = ""
        self.origin: str = ""
        self.success: bool = False
        self.error: str = ""

    def has_content(self) -> bool:
        return self.success and len(self.definitions) > 0


class TranslatorEngine:
    """翻译引擎

    支持多个翻译服务，无需 API key。

    Example:
        >>> engine = TranslatorEngine('google')
        >>> result = engine.translate('Hello', source='auto', target='zh-CN')
        >>> print(result)  # 你好
    """

    def __init__(self, engine: str = DEFAULT_ENGINE):
        """初始化翻译引擎

        Args:
            engine: 翻译引擎名称 ('youdao', 'google' 或 'mymemory')
        """
        if engine not in ENGINES:
            raise ValueError(f"不支持的引擎: {engine}. 支持: {list(ENGINES.keys())}")
        self.engine = engine
        self._last_error: Optional[str] = None

    def translate(
        self,
        text: str,
        source: str = 'auto',
        target: str = 'zh-CN'
    ) -> str:
        """翻译文本

        Args:
            text: 要翻译的文本
            source: 源语言代码 (默认 'auto' 自动检测)
            target: 目标语言代码 (默认 'zh-CN' 中文简体)

        Returns:
            翻译后的文本

        Raises:
            ValueError: 文本为空或参数无效
            Exception: 网络错误或翻译服务异常
        """
        if not text or not text.strip():
            raise ValueError("翻译文本不能为空")

        text = text.strip()
        self._last_error = None

        try:
            if self.engine == 'youdao':
                return self._translate_youdao(text, source, target)
            elif self.engine == 'google':
                translator = GoogleTranslator(source=source, target=target)
                return translator.translate(text)
            elif self.engine == 'mymemory':
                # MyMemory 使用不同的语言代码格式，需要转换
                src_lang = MYMEMORY_LANG_MAP.get(source, source)
                tgt_lang = MYMEMORY_LANG_MAP.get(target, target)
                translator = MyMemoryTranslator(source=src_lang, target=tgt_lang)
                return translator.translate(text)
            else:
                raise ValueError(f"未知引擎: {self.engine}")
        except Exception as e:
            self._last_error = str(e)
            raise

    def _translate_youdao(self, text: str, source: str, target: str) -> str:
        """有道翻译API

        使用有道词典suggest API进行翻译:
        https://dict.youdao.com/suggest?q=text&le=eng&doctype=json
        """
        # 根据源语言选择 le 参数
        # eng = 英语, ch = 中文
        detected = self.detect_language(text)
        if detected == 'zh-CN':
            le = 'ch'  # 中文输入
        else:
            le = 'eng'  # 英文或其他语言输入

        url = "https://dict.youdao.com/suggest"
        params = {
            'q': text,
            'le': le,
            'doctype': 'json',
        }

        try:
            req_url = url + '?' + urllib.parse.urlencode(params)
            req = urllib.request.Request(req_url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
            req.add_header('Accept', '*/*')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            # 解析翻译结果
            if data and 'data' in data:
                entries = data['data'].get('entries', [])
                if entries and len(entries) > 0:
                    # 获取第一个翻译结果
                    explain = entries[0].get('explain', '')
                    if explain:
                        return explain

            # 如果没有翻译结果，返回空
            return ""

        except Exception as e:
            self._last_error = str(e)
            raise

    def translate_batch(
        self,
        texts: List[str],
        source: str = 'auto',
        target: str = 'zh-CN'
    ) -> List[str]:
        """批量翻译

        Args:
            texts: 文本列表
            source: 源语言代码
            target: 目标语言代码

        Returns:
            翻译结果列表
        """
        if self.engine == 'google':
            translator = GoogleTranslator(source=source, target=target)
            return translator.translate_batch(texts)
        elif self.engine == 'mymemory':
            translator = MyMemoryTranslator(source=source, target=target)
            return translator.translate_batch(texts)
        else:
            raise ValueError(f"未知引擎: {self.engine}")

    @property
    def last_error(self) -> Optional[str]:
        """最后一次翻译的错误信息"""
        return self._last_error

    @staticmethod
    def get_supported_languages(engine: str = 'google') -> List[str]:
        """获取引擎支持的语言列表

        Args:
            engine: 翻译引擎名称

        Returns:
            支持的语言代码列表
        """
        if engine == 'google':
            return GoogleTranslator().get_supported_languages(as_dict=True)
        elif engine == 'mymemory':
            # MyMemory 支持大部分常用语言
            return list(LANGUAGES.keys())
        return []

    @staticmethod
    def detect_language(text: str) -> str:
        """检测文本语言（简单规则检测）

        Args:
            text: 要检测的文本

        Returns:
            检测到的语言代码：'zh-CN'（中文）、'en'（英文）、'auto'（其他）
        """
        text = text.strip()
        if not text:
            return 'auto'

        # 检测中文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > 0:
            return 'zh-CN'

        # 检测英文（主要是字母）
        alpha_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        total_chars = len(text.replace(' ', ''))
        if total_chars > 0 and alpha_chars / total_chars > 0.7:
            return 'en'

        return 'auto'

    def smart_translate(self, text: str, preferred_target: str = 'zh-CN') -> str:
        """智能翻译：自动检测语言并切换目标语言

        - 输入中文 → 翻译成英文
        - 输入英文 → 翻译成中文（或用户偏好语言）
        - 其他语言 → 翻译成用户偏好语言

        Args:
            text: 要翻译的文本
            preferred_target: 用户偏好的目标语言（默认中文）

        Returns:
            翻译后的文本
        """
        detected = self.detect_language(text)

        # 智能选择目标语言
        if detected == 'zh-CN':
            # 中文输入，翻译成英文
            target = 'en'
        elif detected == 'en':
            # 英文输入，翻译成用户偏好语言（通常是中文）
            target = preferred_target if preferred_target != 'en' else 'zh-CN'
        else:
            # 其他语言，翻译成用户偏好语言
            target = preferred_target

        return self.translate(text, source='auto', target=target)

    @staticmethod
    def is_single_word(text: str) -> bool:
        """判断是否是单个单词/字"""
        stripped = text.strip()
        # 英文单词：不含空格，全是字母
        if stripped.isalpha() and len(stripped.split()) == 1:
            return True
        # 中文单字：长度为1且是中文
        if len(stripped) == 1 and any('\u4e00' <= c <= '\u9fff' for c in stripped):
            return True
        return False

    @staticmethod
    def lookup_dictionary(word: str, source: str = DEFAULT_DICT_SOURCE) -> DictionaryResult:
        """查词典（支持多个词典源）

        Args:
            word: 要查询的单词
            source: 词典源 ('free' 或 'youdao')

        Returns:
            DictionaryResult 对象
        """
        if source == 'youdao':
            return TranslatorEngine._lookup_youdao(word)
        else:
            return TranslatorEngine._lookup_free_dictionary(word)

    @staticmethod
    def _lookup_free_dictionary(word: str) -> DictionaryResult:
        """查询 Free Dictionary API"""
        result = DictionaryResult(word)

        if not word or not word.strip():
            result.error = "单词为空"
            return result

        word = word.strip().lower()

        # 只支持英文词典查询
        if not word.isalpha():
            result.error = "仅支持英文单词查询"
            return result

        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'iamtrans/1.0')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data and len(data) > 0:
                entry = data[0]
                result.success = True

                # 音标
                if entry.get('phonetics'):
                    for p in entry['phonetics']:
                        if p.get('text'):
                            ph = p['text'].replace('[', '').replace(']', '')
                            result.phonetic = ph
                            break

                # 词源
                if entry.get('origin'):
                    result.origin = entry['origin']

                # 定义
                if entry.get('meanings'):
                    for meaning in entry['meanings']:
                        part = meaning.get('partOfSpeech', '')
                        for defn in meaning.get('definitions', []):
                            result.definitions.append({
                                'partOfSpeech': part,
                                'definition': defn.get('definition', ''),
                                'example': defn.get('example', ''),
                            })

        except urllib.error.HTTPError as e:
            if e.code == 404:
                result.error = "未找到该单词"
            else:
                result.error = f"查询失败: HTTP {e.code}"
        except Exception as e:
            result.error = f"查询出错: {e}"

        return result

    @staticmethod
    def _lookup_youdao(word: str) -> DictionaryResult:
        """查询有道词典（智能检测语言）

        有道词典API:
        - 英文词典: le=eng，返回 ec 数据
        - 中文词典: le=ch，返回 hc 数据
        """
        result = DictionaryResult(word)

        if not word or not word.strip():
            result.error = "单词为空"
            return result

        word = word.strip()

        try:
            # 智能检测语言，选择对应词典
            detected = TranslatorEngine.detect_language(word)
            if detected == 'zh-CN':
                le = 'ch'  # 汉语词典
            else:
                le = 'eng'  # 英文词典（默认）

            # 使用有道词典 jsonapi
            url = f"https://dict.youdao.com/jsonapi?q={urllib.parse.quote(word)}&le={le}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            req.add_header('Accept', 'application/json')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data:
                result.success = True

                # 解析英文词典数据 (ec)
                if 'ec' in data and data['ec'].get('word'):
                    word_data = data['ec']['word']
                    if isinstance(word_data, list) and len(word_data) > 0:
                        first_word = word_data[0]
                        # 音标
                        uk_phone = first_word.get('ukphone', '')
                        us_phone = first_word.get('usphone', '')
                        if uk_phone or us_phone:
                            result.phonetic = f"UK[{uk_phone}] US[{us_phone}]"

                        # 词性翻译 - 有道数据结构: trs[].tr[].l.i[]
                        for tr_group in first_word.get('trs', []):
                            if tr_group.get('tr'):
                                for tr in tr_group['tr']:
                                    if 'l' in tr and 'i' in tr['l']:
                                        texts = tr['l']['i']
                                        if isinstance(texts, list) and len(texts) > 0:
                                            trans_text = texts[0]
                                            if trans_text and isinstance(trans_text, str):
                                                pos_match = re.match(r'^([a-z]+\.)\s*', trans_text)
                                                pos = pos_match.group(1) if pos_match else ''
                                                definition = trans_text[pos_match.end() if pos_match else 0:].strip() if pos_match else trans_text
                                                if definition:
                                                    result.definitions.append({
                                                        'partOfSpeech': pos,
                                                        'definition': definition,
                                                        'example': '',
                                                    })

                # 解析中文词典数据 (newhh - 新汉语词典)
                if 'newhh' in data and data['newhh'].get('dataList'):
                    data_list = data['newhh']['dataList']
                    if isinstance(data_list, list) and len(data_list) > 0:
                        # 拼音（可能有多个读音）
                        pinyins = []
                        for entry in data_list[:2]:  # 最多取两个读音
                            pinyin = entry.get('pinyin', '')
                            if pinyin and pinyin not in pinyins:
                                pinyins.append(pinyin)
                        if pinyins:
                            result.phonetic = f"拼音: {'/'.join(pinyins)}"

                        # 释义 - 新汉语词典数据结构: dataList[].sense[]
                        for entry in data_list[:2]:  # 取两个读音的释义
                            pinyin = entry.get('pinyin', '')
                            for sense in entry.get('sense', [])[:3]:
                                cat = sense.get('cat', '')  # 词性（动词、形容词等）
                                defs = sense.get('def', [])
                                examples = sense.get('examples', [])
                                for i, def_text in enumerate(defs[:1]):
                                    example = examples[i] if i < len(examples) else ''
                                    # 清理例句中的 <self> 标签
                                    example = re.sub(r'<self>|</self>', '', example)
                                    # 添加拼音标记
                                    pos_display = f"{pinyin}·{cat}" if pinyin else cat
                                    result.definitions.append({
                                        'partOfSpeech': pos_display,
                                        'definition': def_text,
                                        'example': example,
                                    })

                # 如果主词典没有数据，尝试从suggest获取
                if not result.definitions and 'suggest' in data:
                    suggest_data = data['suggest']
                    if suggest_data.get('entries'):
                        for entry in suggest_data['entries'][:5]:
                            explain = entry.get('explain', '')
                            if explain:
                                result.definitions.append({
                                    'partOfSpeech': '',
                                    'definition': explain,
                                    'example': '',
                                })

        except urllib.error.HTTPError as e:
            result.error = f"查询失败: HTTP {e.code}"
        except Exception as e:
            result.error = f"查询出错: {e}"

        return result