"""
Auto DM Sender
Kirim DM otomatis dengan personalisasi
"""

import time
import json
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class AutoDM:
    """Auto DM dengan template dan personalisasi"""
    
    def __init__(self, client):
        self.client = client
        self.data_file = Path("data/sent_dms.json")
        self.sent_dms = self._load_sent()
        
        # Configuration
        self.config = {
            'daily_limit': 30,
            'delay_between_dms': (60, 180),
            'check_following_back': True,
            'skip_business': False,
            'skip_verified': False,
            'min_followers': 50,
            'max_followers': 50000
        }
        
        # DM Templates - Welcome messages
        self.welcome_templates = [
            "Hai {name}! 👋 Thanks udah follow! Senang bisa connect sama kamu. Kalau ada pertanyaan feel free to ask ya! 😊",
            "Hey {name}! Makasih udah follow! 🙏 Semoga konten-konten aku bermanfaat buat kamu ya! ✨",
            "Halo {name}! Thanks for the follow! 💫 Aku appreciate banget. Let's connect! 😄",
            "Hi {name}! 👋 Welcome! Glad to have you here. Hope you enjoy the content! ❤️"
        ]
        
        # Promo templates
        self.promo_templates = [
            "Hai {name}! 👋 Mau info exclusive? Check out link di bio ya! Ada promo special buat followers baru! 🎉",
            "Hey {name}! Thanks udah follow! 🙏 FYI, aku lagi ada giveaway nih. Check post terakhir ya! 🎁"
        ]
        
        # Follow-up templates
        self.followup_templates = [
            "Hey {name}! Just checking in. Gimana kabarnya? 😊",
            "Hi {name}! Hope you're doing great! Ada yang bisa aku bantu? 💫"
        ]
        
        # Stats
        self.stats = {
            'sent_today': 0,
            'delivered': 0,
            'failed': 0
        }
        
    def _load_sent(self) -> dict:
        """Load sent DMs history"""
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text())
            except:
                pass
        return {'dms': {}, 'last_reset': str(datetime.now().date())}
        
    def _save_sent(self):
        """Save sent DMs"""
        self.data_file.parent.mkdir(exist_ok=True)
        self.data_file.write_text(json.dumps(self.sent_dms, indent=2))
        
    def _check_daily_reset(self):
        """Reset daily counter if new day"""
        today = str(datetime.now().date())
        if self.sent_dms.get('last_reset') != today:
            self.sent_dms = {'dms': self.sent_dms.get('dms', {}), 'last_reset': today}
            self.stats = {'sent_today': 0, 'delivered': 0, 'failed': 0}
            
    def _is_dm_sent(self, user_id: str, dm_type: str = 'welcome') -> bool:
        """Check if DM already sent to user"""
        user_dms = self.sent_dms.get('dms', {}).get(str(user_id), {})
        return dm_type in user_dms
        
    def _mark_dm_sent(self, user_id: str, dm_type: str = 'welcome'):
        """Mark DM as sent"""
        if 'dms' not in self.sent_dms:
            self.sent_dms['dms'] = {}
        if str(user_id) not in self.sent_dms['dms']:
            self.sent_dms['dms'][str(user_id)] = {}
        self.sent_dms['dms'][str(user_id)][dm_type] = str(datetime.now())
        self._save_sent()
        
    def _personalize_message(self, template: str, user_info: dict) -> str:
        """Personalize message dengan user info"""
        name = user_info.get('full_name') or user_info.get('username', 'there')
        # Use first name only
        name = name.split()[0] if ' ' in name else name
        
        return template.format(
            name=name,
            username=user_info.get('username', ''),
            followers=user_info.get('follower_count', 0)
        )
        
    def _should_dm_user(self, user_info: dict) -> bool:
        """Check if should DM this user based on filters"""
        # Check follower count
        followers = user_info.get('follower_count', 0)
        if followers < self.config['min_followers']:
            return False
        if followers > self.config['max_followers']:
            return False
            
        # Skip business accounts
        if self.config['skip_business'] and user_info.get('is_business'):
            return False
            
        # Skip verified
        if self.config['skip_verified'] and user_info.get('is_verified'):
            return False
            
        return True
        
    def send_dm(self, username: str, message: str, dm_type: str = 'custom') -> dict:
        """Send DM ke satu user"""
        self._check_daily_reset()
        
        result = {
            'success': False,
            'username': username,
            'message': message[:50] + '...' if len(message) > 50 else message
        }
        
        try:
            # Check daily limit
            if self.stats['sent_today'] >= self.config['daily_limit']:
                result['error'] = 'Daily limit reached'
                return result
                
            # Get user info
            user_id = self.client.user_id_from_username(username)
            
            # Check if already sent
            if self._is_dm_sent(user_id, dm_type):
                result['error'] = 'Already sent'
                return result
                
            # Send DM
            self.client.direct_send(message, user_ids=[user_id])
            
            # Mark as sent
            self._mark_dm_sent(user_id, dm_type)
            self.stats['sent_today'] += 1
            self.stats['delivered'] += 1
            
            result['success'] = True
            logger.info(f"✅ DM sent to @{username}")
            
        except Exception as e:
            result['error'] = str(e)
            self.stats['failed'] += 1
            logger.error(f"❌ Failed to DM @{username}: {e}")
            
        return result
        
    def send_welcome_dm(self, username: str) -> dict:
        """Send welcome DM ke new follower"""
        try:
            # Get user info
            user_id = self.client.user_id_from_username(username)
            user_info = self.client.user_info(user_id).dict()
            
            # Check filters
            if not self._should_dm_user(user_info):
                return {'success': False, 'error': 'User filtered out'}
                
            # Check if already sent
            if self._is_dm_sent(user_id, 'welcome'):
                return {'success': False, 'error': 'Already welcomed'}
                
            # Select and personalize template
            template = random.choice(self.welcome_templates)
            message = self._personalize_message(template, user_info)
            
            return self.send_dm(username, message, 'welcome')
            
        except Exception as e:
            logger.error(f"❌ Welcome DM error: {e}")
            return {'success': False, 'error': str(e)}
            
    def send_promo_dm(self, username: str) -> dict:
        """Send promotional DM"""
        try:
            user_id = self.client.user_id_from_username(username)
            user_info = self.client.user_info(user_id).dict()
            
            if self._is_dm_sent(user_id, 'promo'):
                return {'success': False, 'error': 'Already received promo'}
                
            template = random.choice(self.promo_templates)
            message = self._personalize_message(template, user_info)
            
            return self.send_dm(username, message, 'promo')
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def send_bulk_welcome(self, limit: int = 10) -> dict:
        """Send welcome DM ke new followers"""
        self._check_daily_reset()
        
        result = {
            'success': False,
            'sent': 0,
            'skipped': 0,
            'failed': 0
        }
        
        try:
            # Get pending follow requests / new followers
            user_id = self.client.user_id
            followers = self.client.user_followers(user_id, amount=limit * 2)
            
            count = 0
            for follower_id, follower_info in followers.items():
                if count >= limit:
                    break
                    
                if self.stats['sent_today'] >= self.config['daily_limit']:
                    logger.warning("⚠️ Daily DM limit reached")
                    break
                    
                username = follower_info.username
                
                # Check if already DMed
                if self._is_dm_sent(follower_id, 'welcome'):
                    result['skipped'] += 1
                    continue
                    
                # Send welcome
                dm_result = self.send_welcome_dm(username)
                
                if dm_result.get('success'):
                    result['sent'] += 1
                    count += 1
                else:
                    if dm_result.get('error') == 'User filtered out':
                        result['skipped'] += 1
                    else:
                        result['failed'] += 1
                        
                # Delay between DMs
                delay = random.uniform(*self.config['delay_between_dms'])
                time.sleep(delay)
                
            result['success'] = True
            
        except Exception as e:
            logger.error(f"❌ Bulk welcome error: {e}")
            
        return result
        
    def send_to_list(self, usernames: List[str], message: str, dm_type: str = 'custom') -> dict:
        """Send DM ke list of usernames"""
        self._check_daily_reset()
        
        result = {
            'success': False,
            'sent': 0,
            'failed': 0
        }
        
        for username in usernames:
            if self.stats['sent_today'] >= self.config['daily_limit']:
                break
                
            dm_result = self.send_dm(username, message, dm_type)
            
            if dm_result.get('success'):
                result['sent'] += 1
            else:
                result['failed'] += 1
                
            # Delay
            time.sleep(random.uniform(*self.config['delay_between_dms']))
            
        result['success'] = True
        return result
        
    def get_stats(self) -> dict:
        """Get DM statistics"""
        return {
            'today': self.stats,
            'total_sent': len(self.sent_dms.get('dms', {})),
            'remaining_today': self.config['daily_limit'] - self.stats['sent_today']
        }
