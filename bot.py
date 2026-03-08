"""
🚀 FINAL IVASMS OTP TELEGRAM BOT - COMPLETE VERSION
═══════════════════════════════════════════════════════════════════

FINAL FEATURES:
✅ Fetches REAL numbers from YOUR ivasms account
✅ Shows ONLY numbers YOU have listed
✅ Groups by country (only countries with numbers)
✅ Service selection for each number
✅ 6 MINUTES timeout (360 seconds)
✅ Smart OTP extraction by service
✅ Fair credit system (deduct only on success)
✅ Prevent reuse (same combo not shown again)
✅ Admin panel for monitoring
✅ Referral system
✅ Complete database tracking
"""

import os
import time
import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv

# Web Scraping
from bs4 import BeautifulSoup
BEAUTIFUL_SOUP_PARSER = 'html.parser'  # Use html.parser instead of lxml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

# ════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
IVASMS_EMAIL = os.getenv('IVASMS_EMAIL')
IVASMS_PASSWORD = os.getenv('IVASMS_PASSWORD')

if not BOT_TOKEN or not IVASMS_EMAIL or not IVASMS_PASSWORD:
    raise ValueError("❌ Missing required environment variables")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 6 MINUTES TIMEOUT
OTP_TIMEOUT_SECONDS = 360  # 6 minutes

# ════════════════════════════════════════════════════════════════════
# COUNTRY & SERVICE MAPPINGS
# ════════════════════════════════════════════════════════════════════

COUNTRY_FLAGS = {
    'US': '🇺🇸', 'UK': '🇬🇧', 'CA': '🇨🇦', 'AU': '🇦🇺',
    'IN': '🇮🇳', 'KE': '🇰🇪', 'NG': '🇳🇬', 'ZA': '🇿🇦',
    'BR': '🇧🇷', 'MX': '🇲🇽', 'DE': '🇩🇪', 'FR': '🇫🇷',
    'IT': '🇮🇹', 'ES': '🇪🇸', 'SE': '🇸🇪', 'NL': '🇳🇱',
    'JP': '🇯🇵', 'CN': '🇨🇳', 'SG': '🇸🇬', 'MY': '🇲🇾',
    'TH': '🇹🇭', 'VN': '🇻🇳', 'ID': '🇮🇩', 'PH': '🇵🇭',
    'BD': '🇧🇩', 'PK': '🇵🇰', 'AE': '🇦🇪', 'SA': '🇸🇦',
    'EG': '🇪🇬', 'GH': '🇬🇭', 'NZ': '🇳🇿', 'IE': '🇮🇪',
}

PHONE_PREFIXES = {
    '1': 'US', '44': 'UK', '91': 'IN', '254': 'KE', '234': 'NG',
    '27': 'ZA', '55': 'BR', '52': 'MX', '61': 'AU', '49': 'DE',
    '33': 'FR', '39': 'IT', '34': 'ES', '46': 'SE', '31': 'NL',
    '81': 'JP', '86': 'CN', '65': 'SG', '60': 'MY', '66': 'TH',
    '84': 'VN', '62': 'ID', '63': 'PH', '880': 'BD', '92': 'PK',
    '971': 'AE', '966': 'SA', '20': 'EG', '233': 'GH', '64': 'NZ',
    '353': 'IE',
}

COUNTRY_NAMES = {
    'US': 'United States', 'UK': 'United Kingdom', 'CA': 'Canada',
    'AU': 'Australia', 'IN': 'India', 'KE': 'Kenya', 'NG': 'Nigeria',
    'ZA': 'South Africa', 'BR': 'Brazil', 'MX': 'Mexico', 'DE': 'Germany',
    'FR': 'France', 'IT': 'Italy', 'ES': 'Spain', 'SE': 'Sweden',
    'NL': 'Netherlands', 'JP': 'Japan', 'CN': 'China', 'SG': 'Singapore',
    'MY': 'Malaysia', 'TH': 'Thailand', 'VN': 'Vietnam', 'ID': 'Indonesia',
    'PH': 'Philippines', 'BD': 'Bangladesh', 'PK': 'Pakistan',
    'AE': 'United Arab Emirates', 'SA': 'Saudi Arabia', 'EG': 'Egypt',
    'GH': 'Ghana', 'NZ': 'New Zealand', 'IE': 'Ireland',
}

SERVICES = {
    'google': {'emoji': '🔐', 'name': 'Google'},
    'tiktok': {'emoji': '🎵', 'name': 'TikTok'},
    'whatsapp': {'emoji': '💬', 'name': 'WhatsApp'},
    'telegram': {'emoji': '📱', 'name': 'Telegram'},
    'facebook': {'emoji': '👍', 'name': 'Facebook'},
    'instagram': {'emoji': '📸', 'name': 'Instagram'},
    'twitter': {'emoji': '🐦', 'name': 'Twitter'},
    'discord': {'emoji': '⚡', 'name': 'Discord'},
    'linkedin': {'emoji': '💼', 'name': 'LinkedIn'},
    'uber': {'emoji': '🚗', 'name': 'Uber'},
}

SERVICE_PATTERNS = {
    'google': [r'google.*?(\d{4,6})', r'verification.*?code[:\s]+(\d{4,6})'],
    'tiktok': [r'tiktok.*?(\d{4,6})', r'verification.*?code[:\s]+(\d{4,6})'],
    'whatsapp': [r'whatsapp.*?(\d{4,6})', r'(\d{4,6})'],
    'telegram': [r'telegram.*?(\d{4,6})', r'code[:\s]+(\d{4,6})'],
    'facebook': [r'facebook.*?(\d{4,6})', r'code[:\s]+(\d{4,6})'],
    'instagram': [r'instagram.*?(\d{4,6})', r'code[:\s]+(\d{4,6})'],
    'twitter': [r'twitter.*?(\d{4,6})', r'code[:\s]+(\d{4,6})'],
    'discord': [r'discord.*?(\d{4,6})', r'code[:\s]+(\d{4,6})'],
    'linkedin': [r'linkedin.*?(\d{4,6})', r'code[:\s]+(\d{4,6})'],
    'uber': [r'uber.*?(\d{4,6})', r'(\d{4,6})'],
}

# ════════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════════

class Database:
    DB_FILE = 'bot_database.json'
    
    @staticmethod
    def get_default():
        return {
            'users': {},
            'referrals': {},
            'credits': {},
            'otp_history': [],
            'used_combinations': {},
            'analytics': {
                'total_otps': 0,
                'total_users': 0,
                'total_referrals': 0,
                'successful_otps': 0,
                'failed_otps': 0,
                'start_time': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def load():
        try:
            if os.path.exists(Database.DB_FILE):
                with open(Database.DB_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"DB load error: {e}")
        return Database.get_default()
    
    @staticmethod
    def save(db):
        try:
            with open(Database.DB_FILE, 'w') as f:
                json.dump(db, f, indent=2)
        except Exception as e:
            logger.error(f"DB save error: {e}")
    
    @staticmethod
    def register_user(user_id: int, username: str, referrer_id: Optional[int] = None):
        db = Database.load()
        
        if str(user_id) not in db['users']:
            db['users'][str(user_id)] = {
                'id': user_id,
                'username': username,
                'joined_at': datetime.now().isoformat(),
                'otp_count': 0,
                'referrer_id': referrer_id,
                'referral_count': 0
            }
            
            expires = datetime.now() + timedelta(days=5)
            db['credits'][str(user_id)] = {
                'total': 3,
                'used': 0,
                'expires': expires.isoformat()
            }
            
            db['used_combinations'][str(user_id)] = []
            db['analytics']['total_users'] += 1
            
            if referrer_id:
                referrer_id_str = str(referrer_id)
                if referrer_id_str not in db['referrals']:
                    db['referrals'][referrer_id_str] = []
                db['referrals'][referrer_id_str].append(user_id)
                db['analytics']['total_referrals'] += 1
                
                if len(db['referrals'][referrer_id_str]) % 3 == 0:
                    if referrer_id_str in db['credits']:
                        db['credits'][referrer_id_str]['total'] += 1
            
            Database.save(db)
            return True
        return False
    
    @staticmethod
    def get_balance(user_id: int) -> Dict:
        db = Database.load()
        user_id_str = str(user_id)
        
        if user_id_str not in db['credits']:
            return {'total': 0, 'available': 0, 'used': 0, 'expires': None}
        
        credits = db['credits'][user_id_str]
        expires = datetime.fromisoformat(credits['expires'])
        
        if datetime.now() > expires:
            return {'total': 0, 'available': 0, 'used': 0, 'expires': credits['expires'], 'expired': True}
        
        available = credits['total'] - credits['used']
        return {
            'total': credits['total'],
            'available': max(0, available),
            'used': credits['used'],
            'expires': credits['expires'],
            'expired': False
        }
    
    @staticmethod
    def deduct_credit(user_id: int) -> bool:
        db = Database.load()
        user_id_str = str(user_id)
        balance = Database.get_balance(user_id)
        
        if balance['available'] <= 0:
            return False
        
        db['credits'][user_id_str]['used'] += 1
        db['analytics']['successful_otps'] += 1
        Database.save(db)
        return True
    
    @staticmethod
    def record_used_combination(user_id: int, country: str, phone: str, service: str):
        db = Database.load()
        user_id_str = str(user_id)
        
        if user_id_str not in db['used_combinations']:
            db['used_combinations'][user_id_str] = []
        
        db['used_combinations'][user_id_str].append({
            'country': country,
            'phone': phone,
            'service': service,
            'used_at': datetime.now().isoformat()
        })
        Database.save(db)
    
    @staticmethod
    def get_used_combinations(user_id: int) -> List[Tuple[str, str, str]]:
        db = Database.load()
        user_id_str = str(user_id)
        
        combos = db['used_combinations'].get(user_id_str, [])
        return [(c['country'], c['phone'], c['service']) for c in combos]
    
    @staticmethod
    def record_otp(user_id: int, country: str, phone: str, service: str, otp: str, status: str):
        db = Database.load()
        db['otp_history'].append({
            'user_id': user_id,
            'country': country,
            'phone': phone,
            'service': service,
            'otp': otp,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        if str(user_id) in db['users']:
            db['users'][str(user_id)]['otp_count'] += 1
        db['analytics']['total_otps'] += 1
        if status == 'timeout':
            db['analytics']['failed_otps'] += 1
        Database.save(db)

# ════════════════════════════════════════════════════════════════════
# IVASMS SCRAPER
# ════════════════════════════════════════════════════════════════════

class IvasmsScraper:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.logged_in = False
    
    def _get_chrome_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
        return options
    
    async def login(self) -> bool:
        """Login to ivasms"""
        try:
            logger.info("🔐 Logging into ivasms...")
            options = self._get_chrome_options()
            self.driver = webdriver.Chrome(options=options)
            self.driver.get('https://ivasms.com/login')
            
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'email')))
            self.driver.find_element(By.NAME, 'email').send_keys(self.email)
            self.driver.find_element(By.NAME, 'password').send_keys(self.password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'dashboard')))
            self.logged_in = True
            logger.info("✅ ivasms login successful")
            return True
        except Exception as e:
            logger.error(f"❌ Login error: {str(e)}")
            return False
    
    @staticmethod
    def get_country_code_from_phone(phone: str) -> Optional[str]:
        """Detect country code from phone number"""
        phone_clean = phone.replace('+', '').replace('-', '').replace(' ', '')
        
        for prefix in sorted(PHONE_PREFIXES.keys(), key=len, reverse=True):
            if phone_clean.startswith(prefix):
                return PHONE_PREFIXES[prefix]
        
        return None
    
    async def get_all_numbers_grouped_by_country(self) -> Dict[str, List[str]]:
        """Fetch ALL REAL numbers from ivasms account and group by country"""
        try:
            if not self.logged_in:
                logger.error("Not logged in")
                return {}
            
            logger.info("📱 Fetching ALL numbers from ivasms...")
            self.driver.get('https://ivasms.com/numbers')
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'number-item'))
            )
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            countries_dict = {}
            total_numbers = 0
            
            for item in soup.find_all('div', class_='number-item'):
                try:
                    number_element = item.find('span', class_='number')
                    if not number_element:
                        continue
                    
                    phone_number = number_element.text.strip()
                    country_code = self.get_country_code_from_phone(phone_number)
                    
                    if not country_code:
                        logger.warning(f"⚠️ Could not detect country for: {phone_number}")
                        continue
                    
                    if country_code not in countries_dict:
                        countries_dict[country_code] = []
                    
                    countries_dict[country_code].append(phone_number)
                    total_numbers += 1
                    logger.info(f"✓ {country_code}: {phone_number}")
                    
                except Exception as e:
                    logger.warning(f"Error parsing item: {e}")
                    continue
            
            logger.info(f"✅ Total numbers found: {total_numbers} in {len(countries_dict)} countries")
            return countries_dict
            
        except Exception as e:
            logger.error(f"❌ Error fetching numbers: {str(e)}")
            return {}
    
    async def monitor_for_otp_by_service(self, phone_number: str, service: str, wait_seconds: int = OTP_TIMEOUT_SECONDS) -> Optional[str]:
        """Monitor SMS inbox and extract OTP for selected service - 6 MINUTES TIMEOUT"""
        try:
            logger.info(f"📨 Monitoring {phone_number} for {service} ({wait_seconds}s = {wait_seconds//60}min)...")
            number_id = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            self.driver.get(f'https://ivasms.com/number/{number_id}/messages')
            
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'sms-list')))
            
            start_time = time.time()
            last_count = 0
            check_interval = 2  # Check every 2 seconds
            
            while (time.time() - start_time) < wait_seconds:
                try:
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    sms_items = soup.find_all('div', class_='sms-item')
                    current_count = len(sms_items)
                    
                    if current_count > last_count and sms_items:
                        logger.info(f"📬 New SMS! ({current_count} total)")
                        newest = sms_items[0]
                        sms_text = newest.get_text().lower()
                        
                        otp = self._extract_otp_by_service(sms_text, service)
                        if otp:
                            logger.info(f"✅ OTP Found for {service}: {otp}")
                            return otp
                        last_count = current_count
                    
                    await asyncio.sleep(check_interval)
                except Exception as e:
                    logger.warning(f"Check error: {e}")
                    await asyncio.sleep(check_interval)
            
            logger.warning(f"⏱️ Timeout after {wait_seconds}s - no {service} OTP")
            return None
        except Exception as e:
            logger.error(f"❌ Monitor error: {str(e)}")
            return None
    
    @staticmethod
    def _extract_otp_by_service(text: str, service: str) -> Optional[str]:
        """Extract OTP using service-specific patterns"""
        patterns = SERVICE_PATTERNS.get(service.lower(), [r'\b(\d{4,6})\b'])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.logged_in = False

# ════════════════════════════════════════════════════════════════════
# TELEGRAM BOT HANDLERS
# ════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    
    referrer_id = None
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except:
            pass
    
    Database.register_user(user.id, user.username or user.first_name, referrer_id)
    balance = Database.get_balance(user.id)
    is_admin = user.id == ADMIN_ID
    
    text = f"""
👋 <b>Welcome to IVASMS OTP Bot!</b>

🎁 <b>Your Credits:</b>
<code>{balance['available']} OTP credits</code>
(Expires: {balance['expires'][:10] if balance['expires'] else 'N/A'})

📱 <b>Get OTP from any country number</b>

💡 <b>Earn More:</b>
Invite 3 friends → +1 credit

🔗 <b>Your Link:</b>
<code>https://t.me/YourBot?start={user.id}</code>
"""
    
    keyboard = [[InlineKeyboardButton("📱 Get OTP", callback_data='get_otp')],
                [InlineKeyboardButton("🎁 Referrals", callback_data='referrals'),
                 InlineKeyboardButton("💳 Balance", callback_data='balance')]]
    
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ ADMIN", callback_data='admin_panel')])
    
    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """STEP 1: Fetch and show available countries"""
    query = update.callback_query
    user_id = update.effective_user.id
    balance = Database.get_balance(user_id)
    
    if balance['available'] <= 0:
        await query.edit_message_text(
            f"❌ <b>No Credits</b>\n\nYour balance: {balance['available']}\n\nInvite 3 friends for 1 credit!",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Referrals", callback_data='referrals')]])
        )
        return
    
    await query.edit_message_text(
        "🔄 <b>Loading your available countries...</b>\n<i>Fetching from ivasms...</i>",
        parse_mode='HTML')
    
    try:
        scraper = IvasmsScraper(IVASMS_EMAIL, IVASMS_PASSWORD)
        
        if not await scraper.login():
            await query.edit_message_text("❌ Connection failed to ivasms", parse_mode='HTML')
            scraper.close()
            return
        
        countries_dict = await scraper.get_all_numbers_grouped_by_country()
        scraper.close()
        
        if not countries_dict:
            await query.edit_message_text(
                "❌ No numbers found in your ivasms account\n\nPlease add numbers to ivasms first!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data='start')]])
            )
            return
        
        context.user_data['countries_dict'] = countries_dict
        
        text = f"""
<b>🌍 Available Countries</b>

💳 <b>Your Balance:</b> {balance['available']} credit(s)

Select a country:
"""
        
        keyboard = []
        for country_code in sorted(countries_dict.keys()):
            flag = COUNTRY_FLAGS.get(country_code, '🌎')
            country_name = COUNTRY_NAMES.get(country_code, country_code)
            num_count = len(countries_dict[country_code])
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{flag} {country_name} ({num_count} numbers)",
                    callback_data=f"country_{country_code}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🏠 Home", callback_data='start')])
        
        await query.edit_message_text(text, parse_mode='HTML',
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}", parse_mode='HTML')

async def show_country_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """STEP 2: Show numbers for selected country"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    country_code = query.data.split('_')[1]
    countries_dict = context.user_data.get('countries_dict', {})
    
    if country_code not in countries_dict:
        await query.answer("❌ Country not found", show_alert=True)
        return
    
    all_numbers = countries_dict[country_code]
    
    # Filter out already used combinations
    used_combos = Database.get_used_combinations(user_id)
    available_numbers = []
    
    for phone in all_numbers:
        is_used = any(c[0] == country_code and c[1] == phone for c in used_combos)
        if not is_used:
            available_numbers.append(phone)
    
    if not available_numbers:
        await query.edit_message_text(
            f"⚠️ All {COUNTRY_NAMES.get(country_code, country_code)} numbers have been used",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data='get_otp')]])
        )
        return
    
    context.user_data['country_code'] = country_code
    context.user_data['available_numbers'] = available_numbers
    
    country_name = COUNTRY_NAMES.get(country_code, country_code)
    flag = COUNTRY_FLAGS.get(country_code, '🌎')
    
    text = f"""
<b>{flag} {country_name} Numbers</b>

Available: {len(available_numbers)}/{len(all_numbers)}

Select a number:
"""
    
    keyboard = []
    for idx, number in enumerate(available_numbers):
        keyboard.append([InlineKeyboardButton(number, callback_data=f"phone_{idx}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data='get_otp')])
    
    await query.edit_message_text(text, parse_mode='HTML',
                                  reply_markup=InlineKeyboardMarkup(keyboard))

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """STEP 3: Show services to choose from"""
    query = update.callback_query
    
    try:
        idx = int(query.data.split('_')[1])
        available_numbers = context.user_data.get('available_numbers', [])
        
        if idx >= len(available_numbers):
            await query.answer("❌ Number not found", show_alert=True)
            return
        
        selected_phone = available_numbers[idx]
        context.user_data['selected_phone'] = selected_phone
        
        text = f"""
<b>🔐 Select Service</b>

📱 <b>Number:</b>
<code>{selected_phone}</code>

Which service do you need OTP for?
"""
        
        keyboard = []
        for service_key, service_info in sorted(SERVICES.items()):
            keyboard.append([InlineKeyboardButton(
                f"{service_info['emoji']} {service_info['name']}",
                callback_data=f"service_{service_key}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Back", callback_data='get_otp')])
        
        await query.edit_message_text(text, parse_mode='HTML',
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}", parse_mode='HTML')

async def wait_for_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """STEP 4: Wait for OTP from selected service - 6 MINUTES TIMEOUT"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    service = query.data.split('_')[1]
    phone = context.user_data.get('selected_phone')
    country = context.user_data.get('country_code')
    
    if not phone or not service or not country:
        await query.answer("❌ Missing information", show_alert=True)
        return
    
    # Show waiting message with 6 minute timer
    await query.edit_message_text(
        f"⏳ <b>Waiting for {SERVICES[service]['name']} OTP...</b>\n\n"
        f"📱 {phone}\n"
        f"⏱️ Max 6 minutes (360 seconds)\n\n"
        f"<i>Please enter the number in your service and we'll capture the OTP automatically!</i>",
        parse_mode='HTML')
    
    try:
        scraper = IvasmsScraper(IVASMS_EMAIL, IVASMS_PASSWORD)
        
        if not await scraper.login():
            await query.edit_message_text("❌ Connection failed", parse_mode='HTML')
            scraper.close()
            return
        
        # Monitor for OTP with 6 minutes timeout
        otp = await scraper.monitor_for_otp_by_service(
            phone, 
            service, 
            wait_seconds=OTP_TIMEOUT_SECONDS
        )
        scraper.close()
        
        if otp:
            # ✅ SUCCESS - Deduct credit and save combination
            if Database.deduct_credit(user_id):
                Database.record_used_combination(user_id, country, phone, service)
                Database.record_otp(user_id, country, phone, service, otp, 'success')
                balance = Database.get_balance(user_id)
                
                text = f"""
<b>✅ OTP Received Successfully!</b>

🔐 <b>Your Code:</b>
<code>{otp}</code>

🔐 Service: {SERVICES[service]['name']}
📱 Phone: {phone}
💳 Credits Left: {balance['available']}

<i>Copy and use it now!</i>
"""
                
                await query.edit_message_text(text, parse_mode='HTML',
                                              reply_markup=InlineKeyboardMarkup([[
                                                  InlineKeyboardButton("📱 Get Another OTP", callback_data='get_otp'),
                                                  InlineKeyboardButton("🏠 Home", callback_data='start')
                                              ]]))
        else:
            # ❌ TIMEOUT - NO credit deduction
            Database.record_otp(user_id, country, phone, service, 'N/A', 'timeout')
            
            text = f"""
<b>❌ No SMS Detected</b>

No {SERVICES[service]['name']} OTP received in 6 minutes

<b>Why this happened?</b>
❌ Service didn't send OTP to this number
❌ User failed to enter number correctly
❌ Number might be inactive
❌ Service blocked the OTP
❌ Wrong service selected

<b>💡 Important: Your credit was NOT deducted!</b>

<b>What to do next?</b>
✓ Try with a different number
✓ Try with a different service
✓ Try with a different country
✓ Check if number is valid
✓ Try again later
"""
            
            await query.edit_message_text(text, parse_mode='HTML',
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton("📱 Try Another Number", callback_data='get_otp'),
                                              InlineKeyboardButton("🏠 Home", callback_data='start')
                                          ]]))
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}", parse_mode='HTML')

async def show_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral status"""
    query = update.callback_query
    user_id = update.effective_user.id
    db = Database.load()
    
    user_id_str = str(user_id)
    total_referrals = len(db['referrals'].get(user_id_str, []))
    progress = total_referrals % 3
    next_needed = 3 - progress
    
    text = f"""
🏆 <b>Referral Challenge</b>

👥 <b>Invite 3 friends</b>
💰 <b>Earn 1 OTP credit</b>

📊 <b>Your Progress:</b> {progress} / 3
<b>Total Referrals:</b> {total_referrals}
<b>Credits Earned:</b> {total_referrals // 3}

🔗 <b>Your Invite Link:</b>
<code>https://t.me/YourBot?start={user_id}</code>

⚡ Invite {next_needed} more friend(s) for next credit!
"""
    
    await query.edit_message_text(text, parse_mode='HTML',
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton("🏠 Home", callback_data='start')
                                  ]]))

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show credit balance"""
    query = update.callback_query
    user_id = update.effective_user.id
    balance = Database.get_balance(user_id)
    
    if balance['expired']:
        text = f"""
💳 <b>Your Credits</b>

❌ <b>Credits Expired</b>

Your free credits expired on:
{balance['expires'][:10]}

💡 <b>Get More Credits:</b>
Invite 3 friends for 1 credit!
"""
    else:
        days_left = (datetime.fromisoformat(balance['expires']) - datetime.now()).days
        text = f"""
💳 <b>Your Credits</b>

💰 <b>Available:</b> {balance['available']}
📊 <b>Total:</b> {balance['total']}
✅ <b>Used:</b> {balance['used']}

⏰ <b>Expires In:</b> {days_left} days
({balance['expires'][:10]})

📱 <b>Each OTP costs:</b> 1 credit
"""
    
    await query.edit_message_text(text, parse_mode='HTML',
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton("📱 Get OTP", callback_data='get_otp'),
                                      InlineKeyboardButton("🏠 Home", callback_data='start')
                                  ]]))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("❌ Admin only!", show_alert=True)
        return
    
    db = Database.load()
    
    text = f"""
⚙️ <b>ADMIN PANEL</b>

📊 <b>Statistics:</b>
👥 Total Users: {db['analytics']['total_users']}
📱 Total OTPs: {db['analytics']['total_otps']}
✅ Successful: {db['analytics']['successful_otps']}
❌ Failed: {db['analytics']['failed_otps']}
🎁 Total Referrals: {db['analytics']['total_referrals']}

📅 Started: {db['analytics']['start_time'][:10]}
"""
    
    await query.edit_message_text(text, parse_mode='HTML',
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton("🏠 Home", callback_data='start')
                                  ]]))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all buttons"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'get_otp':
        await get_otp(update, context)
    elif query.data == 'referrals':
        await show_referrals(update, context)
    elif query.data == 'balance':
        await show_balance(update, context)
    elif query.data == 'start':
        await query.edit_message_text("🏠 <b>Main Menu</b>", parse_mode='HTML',
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 Get OTP", callback_data='get_otp')],
                                                                        [InlineKeyboardButton("🎁 Referrals", callback_data='referrals'),
                                                                         InlineKeyboardButton("💳 Balance", callback_data='balance')]]))
    elif query.data == 'admin_panel':
        await admin_panel(update, context)
    elif query.data.startswith('country_'):
        await show_country_numbers(update, context)
    elif query.data.startswith('phone_'):
        await show_services(update, context)
    elif query.data.startswith('service_'):
        await wait_for_otp(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

async def main():
    logger.info("=" * 70)
    logger.info("🚀 FINAL IVASMS OTP BOT - COMPLETE VERSION")
    logger.info(f"OTP Timeout: {OTP_TIMEOUT_SECONDS}s = {OTP_TIMEOUT_SECONDS//60} minutes")
    logger.info("=" * 70)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    
    logger.info("✅ Bot running with 6 minute timeout...")
    async with app:
        await app.updater.start_polling(allowed_updates=['message', 'callback_query'])

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
