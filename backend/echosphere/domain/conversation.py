"""Bounded intake: proposals are data; only explicit confirmation changes facts."""
from __future__ import annotations

import re
import time
import unicodedata
from uuid import uuid4

LANGUAGES = ('en-IN', 'hi-IN', 'ta-IN')
FIELDS = ('intent', 'location_or_service_area', 'issue_details', 'contact_name', 'callback_number', 'preferred_language')
TERMINAL = {'ended', 'failed'}
HANDOFF = {'escalating', 'transferring', 'human_connected'}
COPY = {
    'en-IN': {
        'greeting': "I'm EchoSphere, an AI assistant. Please use sample details only. I can collect your issue or request a person. How can I help?",
        'intent': 'What do you need help with?', 'issue_details': 'What happened, and when did it start?',
        'location_or_service_area': 'Which service area is affected?', 'callback_number': 'What callback number should the team use?',
        'contact_name': 'What name should the team use? You may skip this.', 'preferred_language': 'Which language would you prefer for the handoff?',
        'confirm': 'You said: {value}. Is that correct?', 'repair': "I couldn't understand that clearly. Please repeat just the {field}.",
        'transfer': 'I have requested a person and saved your context. The connection is pending; a person may not be available.',
        'safety': "I can't provide professional or emergency guidance. I have requested a person. A connection is not yet confirmed.",
        'complete': 'I have recorded the issue and queued a follow-up case. This does not mean the issue is resolved. I can ask one more question, or connect you to a person.',
        'ended': 'This session has ended.', 'waiting': 'Your request for a person is pending. You can correct your details or end the call.',
        'human': 'A human has joined. I will stop speaking now.',
    },
    'hi-IN': {
        'greeting': 'नमस्ते, मैं EchoSphere, एक AI सहायक हूँ। कृपया केवल उदाहरण की जानकारी दें। मैं आपकी समस्या दर्ज कर सकता हूँ या किसी व्यक्ति से बात करने का अनुरोध कर सकता हूँ। आपको किस मदद की ज़रूरत है?',
        'intent': 'आपको किस मदद की ज़रूरत है?', 'issue_details': 'क्या हुआ और यह कब शुरू हुआ?',
        'location_or_service_area': 'किस सेवा क्षेत्र में समस्या है?', 'callback_number': 'वापस कॉल करने के लिए कौन सा नंबर दें?',
        'contact_name': 'आपका नाम क्या है? आप इसे छोड़ सकते हैं।', 'preferred_language': 'आप किस भाषा में व्यक्ति से बात करना चाहेंगे?',
        'confirm': 'आपने कहा: {value}। क्या यह सही है?', 'repair': 'यह स्पष्ट नहीं सुनाई दिया। कृपया केवल {field} दोबारा बताएं।',
        'transfer': 'मैंने किसी व्यक्ति से बात करने का अनुरोध भेज दिया है और आपकी जानकारी सुरक्षित कर ली है। अभी संपर्क नहीं हुआ है; कोई व्यक्ति उपलब्ध न भी हो सकता है।',
        'safety': 'मैं विशेषज्ञ या आपातकालीन सलाह नहीं दे सकता। मैंने किसी व्यक्ति से बात करने का अनुरोध भेज दिया है। अभी संपर्क की पुष्टि नहीं हुई है।',
        'complete': 'मैंने समस्या दर्ज करके आगे की कार्रवाई के लिए केस कतार में डाल दिया है। इसका मतलब समस्या का समाधान नहीं है। मैं एक और सवाल पूछ सकता हूँ या आपको किसी व्यक्ति से जोड़ सकता हूँ।',
        'ended': 'यह सत्र समाप्त हो गया है।', 'waiting': 'किसी व्यक्ति से बात करने का अनुरोध लंबित है। आप जानकारी सुधार सकते हैं या कॉल समाप्त कर सकते हैं।',
        'human': 'एक व्यक्ति जुड़ गया है। अब मैं बोलना बंद करूँगा।',
    },
    'ta-IN': {
        'greeting': 'வணக்கம், நான் EchoSphere, ஓர் AI உதவியாளர். மாதிரித் தகவல்களை மட்டும் பகிரவும். உங்கள் பிரச்சினையைப் பதிவு செய்யலாம் அல்லது மனித உதவியாளரைக் கோரலாம். உங்களுக்கு என்ன உதவி தேவை?',
        'intent': 'உங்களுக்கு என்ன உதவி தேவை?', 'issue_details': 'என்ன நடந்தது? எப்போது தொடங்கியது?',
        'location_or_service_area': 'எந்த சேவைப் பகுதியில் பிரச்சினை உள்ளது?', 'callback_number': 'திரும்ப அழைக்க எந்த எண்ணைப் பயன்படுத்தலாம்?',
        'contact_name': 'உங்கள் பெயர் என்ன? இதைத் தவிர்க்கலாம்.', 'preferred_language': 'மனித உதவியாளருடன் எந்த மொழியில் பேச விரும்புகிறீர்கள்?',
        'confirm': 'நீங்கள் சொன்னது: {value}. இது சரியா?', 'repair': 'தெளிவாகப் புரியவில்லை. {field} மட்டும் மீண்டும் சொல்லுங்கள்.',
        'transfer': 'மனித உதவியாளருக்குக் கோரிக்கை அனுப்பி உங்கள் தகவல்களைச் சேமித்துள்ளேன். இணைப்பு இன்னும் உறுதியாகவில்லை; உதவியாளர் கிடைக்காமல் இருக்கலாம்.',
        'safety': 'நிபுணத்துவ அல்லது அவசர ஆலோசனை என்னால் வழங்க முடியாது. மனித உதவியாளரைக் கோரியுள்ளேன். இணைப்பு இன்னும் உறுதியாகவில்லை.',
        'complete': 'சிக்கலை பதிவு செய்து தொடர்ந்து உதவிக்கான கேஸை வரிசையில் வைத்துள்ளேன். சிக்கல் தீர்ந்துவிட்டது என்று இதன் பொருள் அல்ல. இன்னொரு கேள்வி கேட்கலாம் அல்லது மனித உதவியாளருடன் இணைக்கலாம்.',
        'ended': 'இந்த அமர்வு முடிந்தது.', 'waiting': 'மனித உதவியாளருக்கான கோரிக்கை நிலுவையில் உள்ளது. தகவல்களைத் திருத்தலாம் அல்லது அழைப்பை முடிக்கலாம்.',
        'human': 'மனித உதவியாளர் இணைந்துள்ளார். இனி நான் பேசுவதை நிறுத்துகிறேன்.',
    },
}
HUMAN = re.compile(r'\b(human|person|operator|representative|agent please|insaan|aadmi)\b|इंसान|व्यक्ति|प्रतिनिधि|आदमी|மனித|உதவியாளரிடம்', re.I)
SAFETY = re.compile(r'\b(medic\w*|diagnos\w*|prescri\w*|symptom\w*|suicid\w*|kill\w*|emergency|lawyer|legal advice|financial advice|invest\w*|weapon|overdose|hurt myself|hurt someone|abuse|treatment|chest pain|should i take|what should i take|is this serious|pain relief|dose)\b|दवा|इलाज|आत्महत्या|मार डाल|आपात|कानूनी|निवेश|सीने में दर्द|क्या दवा|மருந்து|மருத்துவ|தற்கொலை|கொலை|அவசர|சட்ட ஆலோசனை|முதலீடு|மார்பு வலி|என்ன மருந்து', re.I)
YES = {'yes', 'correct', 'yes correct', 'that is correct', 'हाँ', 'हां', 'सही', 'जी हाँ', 'haan', 'ஆமாம்', 'ஆம்', 'சரி', 'aam', 'ama'}
NO = {'no', 'wrong', 'नहीं', 'गलत', 'இல்லை', 'தவறு', 'illa', 'nahi'}
REFUSE = {'skip', 'decline', 'prefer not to say', 'नहीं बताना', 'छोड़ें', 'வேண்டாம்', 'சொல்ல விரும்பவில்லை'}


def language_of(text: str, fallback: str) -> str:
    if re.search('[\u0b80-\u0bff]', text):
        return 'ta-IN'
    if re.search('[\u0900-\u097f]', text):
        return 'hi-IN'
    if re.search(r'\b(english|hindi|tamil)\b', text, re.I):
        for name, code in [('tamil', 'ta-IN'), ('hindi', 'hi-IN'), ('english', 'en-IN')]:
            if name in text.lower():
                return code
    return 'en-IN' if re.search(r'[a-zA-Z]', text) and len(text.split()) > 3 else fallback


def digits(value: str) -> str | None:
    """Normalize explicit digits only. Never invent country codes or missing digits."""
    result = []
    for char in value:
        if char.isdecimal():
            result.append(str(unicodedata.decimal(char)))
        elif char not in ' +()-.,':
            return None
    number = ''.join(result)
    return number if 7 <= len(number) <= 15 else None


class Conversation:
    @staticmethod
    def new(language: str, required: tuple = ('intent', 'issue_details')) -> dict:
        return {'status': 'disclosure', 'case_status': 'open', 'language': language,
                'language_history': [language], 'required': list(required), 'fields': {}, 'history': [],
                'challenge': None, 'repairs': {}, 'repair_pending': None, 'escalation': None,
                'confidence': {'overall_band': 'unknown', 'reason_codes': ['SPEECH_SCORE_UNAVAILABLE']},
                'policy_version': 'intake-v1-hi-en-ta', 'revision': 0}

    @staticmethod
    def copy(call: dict, key: str, **values) -> str:
        return COPY[call['language']][key].format(**values)

    @staticmethod
    def next_field(call: dict) -> str | None:
        return next((key for key in call['required'] if call['fields'].get(key, {}).get('state') != 'confirmed'), None)

    @classmethod
    def prompt(cls, call: dict) -> str:
        if call['status'] in TERMINAL:
            return cls.copy(call, 'ended')
        if call['status'] in HANDOFF:
            return cls.copy(call, 'human' if call['status'] == 'human_connected' else 'waiting')
        challenge = call['challenge']
        if challenge:
            value = call['fields'][challenge['field']]['value']
            if challenge['field'] == 'callback_number':
                value = ' '.join(value)
            return cls.copy(call, 'confirm', value=value)
        key = cls.next_field(call)
        if key:
            call['status'] = 'collecting'
            return cls.copy(call, key)
        call['status'] = 'completing'
        return cls.copy(call, 'complete')

    @classmethod
    def correct(cls, call: dict, field: str, value: str) -> str:
        if field not in FIELDS or not isinstance(value, str) or not 1 <= len(value.strip()) <= 600:
            raise ValueError('Invalid field value')
        value = value.strip()
        if field == 'callback_number':
            value = digits(value)
            if not value:
                raise ValueError('Use 7 to 15 explicit phone digits, without guessing a country code')
        old = call['fields'].get(field)
        version = old['version'] + 1 if old else 1
        if old:
            call['history'].append({**old, 'field': field, 'state': 'corrected'})
        call['fields'][field] = {'value': value, 'version': version, 'state': 'tentative', 'confirmed_at': None}
        call['challenge'] = {'id': str(uuid4()), 'field': field, 'version': version, 'expires_at': time.time() + 120}
        call['repair_pending'] = None
        call['revision'] += 1
        if call['status'] not in HANDOFF | TERMINAL:
            call['status'] = 'confirming'
        return cls.prompt(call)

    @classmethod
    def confirm(cls, call: dict, challenge_id: str) -> str:
        challenge = call['challenge']
        if not challenge or challenge['id'] != challenge_id or challenge['expires_at'] < time.time():
            raise ValueError('The confirmation is stale; review the current value')
        value = call['fields'][challenge['field']]
        if value['version'] != challenge['version']:
            raise ValueError('The confirmation is stale')
        value.update(state='confirmed', confirmed_at=time.time())
        call['challenge'] = None
        call['revision'] += 1
        # Confirm previously volunteered fields before asking for missing facts.
        for key in call['required']:
            item = call['fields'].get(key)
            if item and item['state'] == 'tentative':
                call['challenge'] = {'id': str(uuid4()), 'field': key, 'version': item['version'], 'expires_at': time.time() + 120}
                break
        return cls.prompt(call)

    @classmethod
    def escalate(cls, call: dict, trigger: str) -> str:
        if call['status'] in TERMINAL:
            return cls.copy(call, 'ended')
        if not call['escalation']:
            call['escalation'] = {'id': str(uuid4()), 'trigger': trigger, 'status': 'requested',
                                  'requested_at': time.time(), 'version': 1, 'assigned_to': None}
            call['status'] = 'escalating'
            call['case_status'] = 'handoff_pending'
            call['revision'] += 1
        return cls.copy(call, 'safety' if trigger == 'safety' else 'transfer')

    @classmethod
    def repair(cls, call: dict) -> str:
        key = cls.next_field(call) or 'intent'
        if call['repair_pending'] == key:
            call['repairs'][key] = min(2, call['repairs'].get(key, 0) + 1)
        call['repair_pending'] = key
        call['confidence'] = {'overall_band': 'unknown', 'reason_codes': ['UNCLEAR_INPUT', 'SPEECH_SCORE_UNAVAILABLE']}
        if call['repairs'].get(key, 0) >= 2:
            return cls.escalate(call, 'low_confidence')
        return cls.copy(call, 'repair', field=cls.copy(call, key))

    @classmethod
    def turn(cls, call: dict, text: str, *, speech_confirmation: bool = False) -> str:
        if call['status'] in TERMINAL:
            return cls.copy(call, 'ended')
        language = language_of(text, call['language'])
        if language != call['language']:
            call['language_history'].append(language)
            call['language'] = language
        if HUMAN.search(text):
            return cls.escalate(call, 'human_request')
        if SAFETY.search(text):
            return cls.escalate(call, 'safety')
        if call['status'] in HANDOFF:
            return cls.prompt(call)
        clean = text.strip().lower().strip(' .!?।')
        if clean in REFUSE:
            return cls.escalate(call, 'policy')
        if clean in {'repeat', 'दोहराएं', 'மீண்டும்'}:
            return cls.prompt(call)
        if not clean or clean in {'[unclear]', '[silence]', '[overlap]', 'unclear'}:
            return cls.repair(call)
        if call['challenge']:
            if clean in YES:
                if speech_confirmation:
                    return cls.confirm(call, call['challenge']['id'])
                return cls.prompt(call)
            if clean in NO:
                return cls.repair(call)
            field = call['challenge']['field']
            return cls.correct(call, field, text)
        key = cls.next_field(call)
        if key is None:
            return cls.prompt(call)
        # Multiple explicitly labeled facts can be volunteered without a rigid questionnaire.
        supplied = re.findall(r'(intent|issue_details|location_or_service_area|contact_name|callback_number)\s*:\s*([^;\n]+)', text, re.I)
        if supplied:
            for field, value in reversed(supplied):
                cls.correct(call, field.lower(), value)
            return cls.prompt(call)
        return cls.correct(call, key, text)

    @staticmethod
    def snapshot(call: dict) -> dict:
        confirmed = {key: value.copy() for key, value in call['fields'].items() if value['state'] == 'confirmed'}
        tentative = {key: value.copy() for key, value in call['fields'].items() if value['state'] != 'confirmed'}
        reason = call['escalation']['trigger'] if call['escalation'] else 'intake_complete'
        return {'summary': f'Caller requested support. Handoff reason: {reason}. Confirmed fields: {", ".join(confirmed) or "none"}. Unconfirmed information requires review.',
                'confirmed_fields': confirmed, 'tentative_fields': tentative,
                'open_questions': [key for key in call['required'] if key not in confirmed],
                'language': call['language'], 'language_history': call['language_history'][:],
                'reason': reason, 'revision': call['revision'], 'created_at': time.time()}
