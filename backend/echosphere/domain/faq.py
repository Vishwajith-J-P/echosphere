"""Small, local, document-backed FAQ catalogue.

The catalogue is deliberately finite. It is not a general web search or an
unverified model knowledge dump; unknown questions are returned as unknown.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class FAQ:
    key: str
    terms: tuple[str, ...]
    answers: dict[str, str]


ENTRIES = (
    FAQ('no_internet', ('no internet', 'my internet', 'internet not working', 'internet is down', 'wifi not working', 'wi-fi not working', 'नेट नहीं', 'इंटरनेट नहीं', 'वाईफाई नहीं', 'இணையம் இல்லை', 'இணைய இணைப்பு வேலை செய்யவில்லை', 'வைஃபை வேலை செய்யவில்லை'), {
        'en-IN': 'For no internet, first check whether the router or modem has power and whether the cable or Wi-Fi indicator is connected. If it looks normal, switch the router off, wait thirty seconds, and switch it on once. Do not factory-reset it. If the connection is still down after it restarts, I will record the time, device, and indicator lights for follow-up.',
        'hi-IN': 'इंटरनेट न चलने पर पहले देखें कि राउटर या मॉडेम में बिजली है और केबल या वाई-फाई संकेतक जुड़ा है। सब सामान्य लगे तो राउटर को बंद करके तीस सेकंड रुकें और एक बार चालू करें। फ़ैक्टरी रीसेट न करें। फिर भी कनेक्शन न आए तो मैं समय, डिवाइस और संकेतक लाइट की जानकारी आगे की कार्रवाई के लिए दर्ज करूँगा।',
        'ta-IN': 'இணையம் இல்லையெனில் முதலில் ரூட்டர் அல்லது மோடமில் மின்சாரம் உள்ளதா, கேபிள் அல்லது வைஃபை விளக்கு இணைந்துள்ளதா என்று பாருங்கள். எல்லாம் இயல்பாக இருந்தால் ரூட்டரை அணைத்து முப்பது விநாடிகள் காத்திருந்து ஒருமுறை இயக்குங்கள். தொழிற்சாலை மீட்டமைப்பு செய்ய வேண்டாம். இணைப்பு திரும்பவில்லை என்றால் நேரம், சாதனம், விளக்குகளின் நிலையை தொடர்ந்து உதவிக்காக பதிவு செய்வேன்.',
    }),
    FAQ('identity', ('what is echosphere', 'who are you', 'what do you do', 'आप कौन', 'நீங்கள் யார்'), {
        'en-IN': "EchoSphere is an AI voice assistant for support intake. I record the important details and can request a human; I do not replace professional advice.",
        'hi-IN': 'EchoSphere सहायता जानकारी लेने वाला AI वॉइस सहायक है। मैं ज़रूरी विवरण दर्ज कर सकता हूँ और इंसान से बात कराने का अनुरोध कर सकता हूँ; मैं पेशेवर सलाह का विकल्प नहीं हूँ।',
        'ta-IN': 'EchoSphere உதவி விவரங்களைப் பதிவு செய்யும் AI குரல் உதவியாளர். முக்கிய தகவல்களை பதிவு செய்து மனித உதவியாளரைக் கோரலாம்; இது தொழில்முறை ஆலோசனைக்கு மாற்றாகாது.',
    }),
    FAQ('languages', ('supported language', 'which language', 'hindi', 'tamil', 'தமிழ்', 'हिंदी'), {
        'en-IN': 'I support Hindi, English, and Tamil, including switching between them during a call.',
        'hi-IN': 'मैं हिंदी, अंग्रेज़ी और तमिल में सहायता कर सकता हूँ और कॉल के दौरान भाषा बदली जा सकती है।',
        'ta-IN': 'நான் இந்தி, ஆங்கிலம், தமிழ் ஆகிய மொழிகளை ஆதரிக்கிறேன்; அழைப்பின்போது மொழியை மாற்றலாம்.',
    }),
    FAQ('recording', ('record', 'recording', 'store audio', 'privacy', 'रिकॉर्ड', 'பதிவு'), {
        'en-IN': 'Audio recording is disabled by default. EchoSphere keeps the finalized support context needed for the case, subject to the configured retention policy.',
        'hi-IN': 'ऑडियो रिकॉर्डिंग डिफ़ॉल्ट रूप से बंद है। केस के लिए ज़रूरी अंतिम सहायता संदर्भ ही निर्धारित नीति के अनुसार रखा जाता है।',
        'ta-IN': 'ஆடியோ பதிவு இயல்பாக முடக்கப்பட்டுள்ளது. கேஸுக்குத் தேவையான இறுதி உதவி சூழல் மட்டும் அமைக்கப்பட்ட தக்கவைப்பு கொள்கைப்படி வைக்கப்படும்.',
    }),
    FAQ('human', ('human', 'person', 'agent', 'representative', 'इंसान', 'மனித'), {
        'en-IN': 'You can ask for a person at any time. EchoSphere saves the context first; a connection is only confirmed after an authorized human joins.',
        'hi-IN': 'आप कभी भी किसी व्यक्ति से बात करने को कह सकते हैं। EchoSphere पहले संदर्भ सुरक्षित करता है; कनेक्शन तभी पक्का बताया जाता है जब अधिकृत व्यक्ति जुड़ जाए।',
        'ta-IN': 'எப்போது வேண்டுமானாலும் மனித உதவியாளரைக் கேட்கலாம். EchoSphere முதலில் சூழலைச் சேமிக்கும்; அங்கீகரிக்கப்பட்ட நபர் இணைந்த பிறகே இணைப்பு உறுதி செய்யப்படும்.',
    }),
)


def lookup(text: str, language: str) -> str | None:
    normalized = re.sub(r'\s+', ' ', text.casefold()).strip()
    for entry in ENTRIES:
        if any(term.casefold() in normalized for term in entry.terms):
            return entry.answers.get(language, entry.answers['en-IN'])
    return None


def is_question(text: str) -> bool:
    normalized = text.casefold().strip()
    return normalized.endswith('?') or bool(re.match(r'^(what|why|how|when|where|which|can|is|do|does|क्या|क्यों|कैसे|कब|कहाँ|என்ன|ஏன்|எப்படி|எப்போது|எங்கே)\b', normalized))


def limitation(language: str) -> str:
    return {
        'en-IN': "I don't have an approved answer for that in my current support guide, so I won't guess. I can record the question and continue collecting the issue.",
        'hi-IN': 'मेरे मौजूदा सहायता गाइड में इसका स्वीकृत उत्तर नहीं है, इसलिए मैं अनुमान नहीं लगाऊँगा। मैं आपका सवाल दर्ज करके समस्या की जानकारी ले सकता हूँ।',
        'ta-IN': 'எனது தற்போதைய உதவி வழிகாட்டியில் இதற்கான அங்கீகரிக்கப்பட்ட பதில் இல்லை; எனவே நான் ஊகிக்க மாட்டேன். கேள்வியை பதிவு செய்து சிக்கல் விவரங்களைத் தொடரலாம்.',
    }.get(language, "I don't have an approved answer for that, so I won't guess. I can record the question and continue collecting the issue.")
