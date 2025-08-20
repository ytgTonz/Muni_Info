from typing import Dict, Any, Optional
from enum import Enum

class Language(Enum):
    ENGLISH = "en"
    AFRIKAANS = "af"
    ZULU = "zu"
    XHOSA = "xh"

class LanguageService:
    def __init__(self):
        self.translations = {
            # Main menu and navigation
            'main_menu': {
                'en': "📋 *Main Menu*\n\n1. View District\n2. View Municipality\n3. View Map\n4. Lodge Complaint\n5. Emergency Services\n6. My Complaints\n7. Change Language\n\nPlease type the number of your choice.",
                'af': "📋 *Hoofkieslys*\n\n1. Bekyk Distrik\n2. Bekyk Munisipaliteit\n3. Bekyk Kaart\n4. Dien Klagte In\n5. Nooddienste\n6. My Klagtes\n7. Verander Taal\n\nTik asseblief die nommer van u keuse.",
                'zu': "📋 *Imenyu Eyinhloko*\n\n1. Buka Isifunda\n2. Buka Umasipala\n3. Buka Imephu\n4. Faka Isikhalazo\n5. Izinsizakalo Zesimo Siphakamisile\n6. Izikhalazo Zami\n7. Shintsha Ulimi\n\nSicela uthayipe inombolo yokuzikhethela kwakho.",
                'xh': "📋 *Imenyu Eyintloko*\n\n1. Jonga iSithili\n2. Jonga uMasipala\n3. Jonga iMaphu\n4. Faka isiKhalazo\n5. iinKonzo zeeMvukelo\n6. iziKhalazo Zam\n7. Tshintsha uLwimi\n\nNceda uthayiphe inombolo yokuzikhethela kwakho."
            },
            'language_selection': {
                'en': "🌍 *Language Selection*\n\n1. English\n2. Afrikaans\n3. isiZulu\n4. isiXhosa\n\nPlease select your preferred language:",
                'af': "🌍 *Taalkeuse*\n\n1. English\n2. Afrikaans\n3. isiZulu\n4. isiXhosa\n\nKies asseblief u voorkeur taal:",
                'zu': "🌍 *Ukukhetha Ulimi*\n\n1. English\n2. Afrikaans\n3. isiZulu\n4. isiXhosa\n\nSicela ukhethe ulimi lwakho oluncamela:",
                'xh': "🌍 *Ukukhetha uLwimi*\n\n1. English\n2. Afrikaans\n3. isiZulu\n4. isiXhosa\n\nNceda ukhethe ulwimi lwakho olukhethelayo:"
            },
            'language_changed': {
                'en': "✅ Language changed to English.",
                'af': "✅ Taal verander na Afrikaans.",
                'zu': "✅ Ulimi lwashintshwa lwaba yisiZulu.",
                'xh': "✅ Ulwimi lutshintshiwe lwaba yisiXhosa."
            },
            'welcome': {
                'en': "👋 Welcome to Muni-Info!\n\nWe help you access municipal services and lodge complaints.\n\n📍 Share your location to get started, or type 'menu' for options.",
                'af': "👋 Welkom by Muni-Info!\n\nOns help u om munisipale dienste te verkry en klagtes in te dien.\n\n📍 Deel u ligging om te begin, of tik 'menu' vir opsies.",
                'zu': "👋 Siyakwamukela ku-Muni-Info!\n\nSikusiza ukufinyelela izinsizakalo zamasipala nokufaka izikhalazo.\n\n📍 Yabelana ngendawo yakho ukuze uqale, noma uthayipe 'menu' ukuthola izinketho.",
                'xh': "👋 Wamkelekile ku-Muni-Info!\n\nSikunceda ukufikelela kwiinkonzo zikamasipala kunye nokufaka izikhalazo.\n\n📍 Yabelana ngendawo yakho ukuze uqale, okanye uthayiphe 'menu' ukufumana ezongezelelo."
            },
            'complaint_categories': {
                'en': "🎯 *Complaint Categories*\n\n1. Water\n2. Electricity\n3. Sanitation\n4. Roads\n5. Other\n\nPlease type the number of your complaint category.",
                'af': "🎯 *Klagtekategorieë*\n\n1. Water\n2. Elektrisiteit\n3. Sanitasie\n4. Paaie\n5. Ander\n\nTik asseblief die nommer van u klagtekategorie.",
                'zu': "🎯 *Izigaba Zezikhalazo*\n\n1. Amanzi\n2. Ugesi\n3. Izindawo Zokuhlanza\n4. Imigwaqo\n5. Okunye\n\nSicela uthayipe inombolo yesigaba sesikhalazo sakho.",
                'xh': "🎯 *Iindidi zeziKhalazo*\n\n1. Amanzi\n2. Umbane\n3. Isiseko sezeMpilo\n4. Iindlela\n5. Ezinye\n\nNceda uthayiphe inombolo yohlobo lwesikhalazo sakho."
            },
            'complaint_description': {
                'en': "📝 You've selected: *{complaint_type}*\n\nPlease describe your complaint in detail. You can also include an image if needed. 📸",
                'af': "📝 U het gekies: *{complaint_type}*\n\nBeskryf asseblief u klagte in detail. U kan ook 'n beeld insluit indien nodig. 📸",
                'zu': "📝 Ukhethe: *{complaint_type}*\n\nSicela uchaze isikhalazo sakho ngokugcwele. Ungafaka nesithombe uma kudingeka. 📸",
                'xh': "📝 Ukhethe: *{complaint_type}*\n\nNceda uchaze isikhalazo sakho ngokupheleleyo. Unokubandakanya nomfanekiso xa kufuneka. 📸"
            },
            'complaint_submitted': {
                'en': "✅ *Complaint Submitted Successfully!*\n\n**Reference:** {reference_id}\n**Type:** {complaint_type}\n**Priority:** {priority}\n\nWe'll keep you updated on progress. Save this reference number for future inquiries.",
                'af': "✅ *Klagte Suksesvol Ingedien!*\n\n**Verwysing:** {reference_id}\n**Tipe:** {complaint_type}\n**Prioriteit:** {priority}\n\nOns sal u op hoogte hou van vordering. Stoor hierdie verwysingsnommer vir toekomstige navrae.",
                'zu': "✅ *Isikhalazo Sithunyelwe Ngempumelelo!*\n\n**Inkomba:** {reference_id}\n**Uhlobo:** {complaint_type}\n**Okubalulekile:** {priority}\n\nSizokwazisa ngenqubekela phambili. Gcina le nombolo yenkomba yemibuzo yesikhathi esizayo.",
                'xh': "✅ *IsiKhalazo siThunyezelwe Ngempumelelo!*\n\n**Isalathiso:** {reference_id}\n**Uhlobo:** {complaint_type}\n**Okuphambili:** {priority}\n\nSiza kukwazisa ngenkqubela phambili. Gcina eli nombolo lesalathiso lemibuzo yexesha elizayo."
            },
            'location_info': {
                'en': "📍 *Your Location Information*\n\nProvince: {province}\nDistrict: {district}\nMunicipality: {municipality}",
                'af': "📍 *U Liggingsinligting*\n\nProvinsie: {province}\nDistrik: {district}\nMunisipaliteit: {municipality}",
                'zu': "📍 *Ulwazi Lwendawo Yakho*\n\nIesifundazwe: {province}\nIsifunda: {district}\nUmasipala: {municipality}",
                'xh': "📍 *Ulwazi Lwendawo Yakho*\n\nIphondo: {province}\nIsithili: {district}\nUmasipala: {municipality}"
            },
            'emergency_services': {
                'en': "🚨 *Emergency Services*\n\nPolice: 10111\nAmbulance: 10177\nFire: 10177\n\nFor life-threatening emergencies, call immediately!",
                'af': "🚨 *Nooddienste*\n\nPolisie: 10111\nAmbulans: 10177\nBrandweer: 10177\n\nVir lewensbedreigende noodgevalle, bel dadelik!",
                'zu': "🚨 *Izinsizakalo Zesimo Siphakamisile*\n\nAmaphoyisa: 10111\nIambulense: 10177\nAbasebenzi bokucisha umlilo: 10177\n\nUma kunezingozi eziyingozi yokuphila, shayela ngokushesha!",
                'xh': "🚨 *iinKonzo zeeMvukelo*\n\nAmapolisa: 10111\nIambulanse: 10177\nAbasebenzi bokucima umlilo: 10177\n\nUkuba kukho iimvukelo ezisongela ubomi, fumana uncedo ngokukhawuleza!"
            },
            'no_location': {
                'en': "❌ Could not identify your location. Please share your GPS location or try again.",
                'af': "❌ Kon nie u ligging identifiseer nie. Deel asseblief u GPS-ligging of probeer weer.",
                'zu': "❌ Asikwazanga ukuhlonza indawo yakho. Sicela wabelane ngendawo yakho ye-GPS noma uzame futhi.",
                'xh': "❌ Asikwazanga ukuhlongoloze indawo yakho. Nceda wabelane ngendawo yakho ye-GPS okanye uzame kwakhona."
            },
            'invalid_choice': {
                'en': "❌ Invalid choice. Please try again.",
                'af': "❌ Ongeldige keuse. Probeer asseblief weer.",
                'zu': "❌ Ukhethe okungalungile. Sicela uzame futhi.",
                'xh': "❌ Ukhethe okungalunganga. Nceda uzame kwakhona."
            },
            'error_occurred': {
                'en': "❌ An error occurred. Please try again or type 'menu' for options.",
                'af': "❌ 'n Fout het voorgekom. Probeer asseblief weer of tik 'menu' vir opsies.",
                'zu': "❌ Kuye kwenzeka iphutha. Sicela uzame futhi noma uthayipe 'menu' ukuthola izinketho.",
                'xh': "❌ Kwenzeke impazamo. Nceda uzame kwakhona okanye uthayiphe 'menu' ukufumana ezongezelelo."
            },
            'complaints_history': {
                'en': "📋 *Your Complaints History* ({count} total)\n\n{complaints_list}\n\nReply with a reference number to view details.",
                'af': "📋 *U Klagtegeskiedenis* ({count} totaal)\n\n{complaints_list}\n\nAntwoord met 'n verwysingsnommer om details te sien.",
                'zu': "📋 *Umlando Wezikhalazo Zakho* ({count} konke)\n\n{complaints_list}\n\nPhendula ngenombolo yenkomba ukuze ubone imininingwane.",
                'xh': "📋 *Imbali yeziKhalazo Zakho* ({count} zizonke)\n\n{complaints_list}\n\nPhendula ngenombolo yesalathiso ukuze ubone iinkcukacha."
            },
            'no_complaints': {
                'en': "📝 No complaints found for your number.",
                'af': "📝 Geen klagtes gevind vir u nommer nie.",
                'zu': "📝 Azikho izikhalazo ezitholakele ngenombolo yakho.",
                'xh': "📝 Azikho izikhalazo zifunyanwe ngenombolo yakho."
            }
        }
        
        # Language detection keywords
        self.language_keywords = {
            'af': ['afrikaans', 'af', 'afrika', 'boere'],
            'zu': ['zulu', 'isizulu', 'zu', 'sawubona'],
            'xh': ['xhosa', 'isixhosa', 'xh', 'molo']
        }
    
    def detect_language(self, text: str) -> Language:
        text_lower = text.lower()
        
        for lang_code, keywords in self.language_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return Language(lang_code)
        
        return Language.ENGLISH  # Default to English
    
    def get_text(self, key: str, language: Language = Language.ENGLISH, **kwargs) -> str:
        translations = self.translations.get(key, {})
        text = translations.get(language.value, translations.get('en', f'[{key}]'))
        
        try:
            return text.format(**kwargs) if kwargs else text
        except KeyError as e:
            print(f"Missing translation variable {e} for key {key}")
            return text
    
    def get_language_from_choice(self, choice: str) -> Language:
        language_map = {
            '1': Language.ENGLISH,
            '2': Language.AFRIKAANS,
            '3': Language.ZULU,
            '4': Language.XHOSA
        }
        return language_map.get(choice, Language.ENGLISH)
    
    def is_valid_language_choice(self, choice: str) -> bool:
        return choice in ['1', '2', '3', '4']
    
    def get_complaint_type_translation(self, complaint_type: str, language: Language) -> str:
        translations = {
            'Water': {
                'en': 'Water',
                'af': 'Water',
                'zu': 'Amanzi',
                'xh': 'Amanzi'
            },
            'Electricity': {
                'en': 'Electricity',
                'af': 'Elektrisiteit',
                'zu': 'Ugesi',
                'xh': 'Umbane'
            },
            'Sanitation': {
                'en': 'Sanitation',
                'af': 'Sanitasie',
                'zu': 'Izindawo Zokuhlanza',
                'xh': 'Isiseko sezeMpilo'
            },
            'Roads': {
                'en': 'Roads',
                'af': 'Paaie',
                'zu': 'Imigwaqo',
                'xh': 'Iindlela'
            },
            'Other': {
                'en': 'Other',
                'af': 'Ander',
                'zu': 'Okunye',
                'xh': 'Ezinye'
            }
        }
        
        type_translations = translations.get(complaint_type, {})
        return type_translations.get(language.value, complaint_type)
    
    def get_priority_translation(self, priority: str, language: Language) -> str:
        translations = {
            'urgent': {
                'en': '🔴 Urgent',
                'af': '🔴 Dringend',
                'zu': '🔴 Okuphakeme',
                'xh': '🔴 Ngxamisekile'
            },
            'high': {
                'en': '🟠 High',
                'af': '🟠 Hoog',
                'zu': '🟠 Okuphezulu',
                'xh': '🟠 Ephakamileyo'
            },
            'medium': {
                'en': '🟡 Medium',
                'af': '🟡 Medium',
                'zu': '🟡 Phakathi',
                'xh': '🟡 Phakathi'
            },
            'low': {
                'en': '🟢 Low',
                'af': '🟢 Laag',
                'zu': '🟢 Okuphansi',
                'xh': '🟢 Ephantsi'
            }
        }
        
        priority_translations = translations.get(priority.lower(), {})
        return priority_translations.get(language.value, f"❓ {priority}")

language_service = LanguageService()