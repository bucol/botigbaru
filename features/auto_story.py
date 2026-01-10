"""
Auto Story Viewer
Otomatis view stories untuk meningkatkan engagement
"""

import time
import json
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class AutoStory:
    """Auto view stories dengan smart targeting"""
    
    def __init__(self, client):
        self.client = client
        self.data_file = Path("data/viewed_stories.json")
        self.viewed_stories = self._load_viewed()
        
        # Configuration
        self.config = {
            'daily_limit': 200,
            'delay_between_views': (2, 5),
            'delay_between_users': (10, 30),
            'skip_ads': True,
            'view_duration': (1, 3),
            'react_probability': 0.1,
            'reply_probability': 0.05
        }
        
        # Reaction emojis
        self.reactions = ['😍', '🔥', '👏', '❤️', '😮', '💯']
        
        # Reply templates
        self.reply_templates = [
            "Keren banget! 🔥",
            "Wow amazing! 😍",
            "Mantap! 👏",
            "Suka banget sama ini!",
            "Goals! ❤️"
        ]
        
        # Stats
        self.stats = {
            'viewed_today': 0,
            'reacted_today': 0,
            'replied_today': 0
        }
        
    def _load_viewed(self) -> dict:
        """Load viewed stories history"""
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text())
            except:
                pass
        return {'stories': [], 'last_reset': str(datetime.now().date())}
        
    def _save_viewed(self):
        """Save viewed stories"""
        self.data_file.parent.mkdir(exist_ok=True)
        self.data_file.write_text(json.dumps(self.viewed_stories, indent=2))
        
    def _check_daily_reset(self):
        """Reset daily counter if new day"""
        today = str(datetime.now().date())
        if self.viewed_stories.get('last_reset') != today:
            self.viewed_stories = {'stories': [], 'last_reset': today}
            self.stats = {'viewed_today': 0, 'reacted_today': 0, 'replied_today': 0}
            
    def _is_viewed(self, story_id: str) -> bool:
        """Check if story already viewed"""
        return story_id in self.viewed_stories.get('stories', [])
        
    def _mark_viewed(self, story_id: str):
        """Mark story as viewed"""
        if 'stories' not in self.viewed_stories:
            self.viewed_stories['stories'] = []
        self.viewed_stories['stories'].append(story_id)
        self._save_viewed()
        
    def view_user_stories(self, username: str) -> dict:
        """View all stories dari satu user"""
        self._check_daily_reset()
        
        result = {
            'success': False,
            'username': username,
            'viewed': 0,
            'reacted': 0,
            'replied': 0
        }
        
        try:
            # Get user info
            user_id = self.client.user_id_from_username(username)
            stories = self.client.user_stories(user_id)
            
            if not stories:
                logger.info(f"📭 @{username} tidak punya story aktif")
                return result
                
            logger.info(f"📖 Found {len(stories)} stories from @{username}")
            
            for story in stories:
                # Check daily limit
                if self.stats['viewed_today'] >= self.config['daily_limit']:
                    logger.warning("⚠️ Daily view limit reached")
                    break
                    
                story_id = str(story.pk)
                
                # Skip if already viewed
                if self._is_viewed(story_id):
                    continue
                    
                # Skip ads
                if self.config['skip_ads'] and hasattr(story, 'is_paid_partnership'):
                    if story.is_paid_partnership:
                        continue
                        
                # View story
                try:
                    self.client.story_seen([story.pk])
                    
                    # Simulate viewing duration
                    view_time = random.uniform(*self.config['view_duration'])
                    time.sleep(view_time)
                    
                    self._mark_viewed(story_id)
                    result['viewed'] += 1
                    self.stats['viewed_today'] += 1
                    
                    # Random reaction
                    if random.random() < self.config['react_probability']:
                        reaction = random.choice(self.reactions)
                        # Note: story reaction API may vary
                        try:
                            self.client.story_send_reaction(story.pk, reaction)
                            result['reacted'] += 1
                            self.stats['reacted_today'] += 1
                            logger.info(f"  ❤️ Reacted with {reaction}")
                        except:
                            pass
                            
                    # Random reply
                    if random.random() < self.config['reply_probability']:
                        reply = random.choice(self.reply_templates)
                        try:
                            self.client.direct_send(reply, user_ids=[user_id])
                            result['replied'] += 1
                            self.stats['replied_today'] += 1
                            logger.info(f"  💬 Replied: {reply}")
                        except:
                            pass
                            
                    # Delay between stories
                    delay = random.uniform(*self.config['delay_between_views'])
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"  ❌ Error viewing story: {e}")
                    
            result['success'] = True
            logger.info(f"✅ Viewed {result['viewed']} stories from @{username}")
            
        except Exception as e:
            logger.error(f"❌ Error getting stories from @{username}: {e}")
            
        return result
        
    def view_followers_stories(self, limit: int = 20) -> dict:
        """View stories dari followers"""
        self._check_daily_reset()
        
        result = {
            'success': False,
            'users_processed': 0,
            'viewed': 0,
            'reacted': 0,
            'replied': 0
        }
        
        try:
            # Get current user ID
            user_id = self.client.user_id
            
            # Get followers
            followers = self.client.user_followers(user_id, amount=limit)
            
            logger.info(f"📋 Processing stories from {len(followers)} followers")
            
            for follower_id, follower_info in followers.items():
                # Check daily limit
                if self.stats['viewed_today'] >= self.config['daily_limit']:
                    break
                    
                username = follower_info.username
                
                # View their stories
                user_result = self.view_user_stories(username)
                
                if user_result['viewed'] > 0:
                    result['users_processed'] += 1
                    result['viewed'] += user_result['viewed']
                    result['reacted'] += user_result['reacted']
                    result['replied'] += user_result['replied']
                    
                # Delay between users
                delay = random.uniform(*self.config['delay_between_users'])
                time.sleep(delay)
                
            result['success'] = True
            
        except Exception as e:
            logger.error(f"❌ Error viewing followers stories: {e}")
            
        return result
        
    def view_following_stories(self, limit: int = 30) -> dict:
        """View stories dari akun yang di-follow"""
        self._check_daily_reset()
        
        result = {
            'success': False,
            'users_processed': 0,
            'viewed': 0
        }
        
        try:
            # Get feed stories (people you follow)
            reels_tray = self.client.reels_tray()
            
            count = 0
            for reel in reels_tray:
                if count >= limit:
                    break
                    
                if self.stats['viewed_today'] >= self.config['daily_limit']:
                    break
                    
                username = reel.user.username
                user_result = self.view_user_stories(username)
                
                if user_result['viewed'] > 0:
                    result['users_processed'] += 1
                    result['viewed'] += user_result['viewed']
                    count += 1
                    
                # Delay
                time.sleep(random.uniform(*self.config['delay_between_users']))
                
            result['success'] = True
            
        except Exception as e:
            logger.error(f"❌ Error viewing following stories: {e}")
            
        return result
        
    def view_hashtag_stories(self, hashtag: str, limit: int = 10) -> dict:
        """View stories dari hashtag tertentu"""
        self._check_daily_reset()
        
        result = {
            'success': False,
            'viewed': 0
        }
        
        try:
            hashtag = hashtag.lstrip('#')
            
            # Get hashtag stories
            stories = self.client.hashtag_stories(hashtag)
            
            logger.info(f"📋 Found {len(stories)} stories for #{hashtag}")
            
            count = 0
            for story in stories:
                if count >= limit:
                    break
                    
                if self.stats['viewed_today'] >= self.config['daily_limit']:
                    break
                    
                story_id = str(story.pk)
                
                if self._is_viewed(story_id):
                    continue
                    
                try:
                    self.client.story_seen([story.pk])
                    self._mark_viewed(story_id)
                    result['viewed'] += 1
                    self.stats['viewed_today'] += 1
                    count += 1
                    
                    # Delay
                    time.sleep(random.uniform(*self.config['delay_between_views']))
                    
                except Exception as e:
                    logger.error(f"  ❌ Error viewing story: {e}")
                    
            result['success'] = True
            
        except Exception as e:
            logger.error(f"❌ Error viewing hashtag stories: {e}")
            
        return result
        
    def get_stats(self) -> dict:
        """Get viewing statistics"""
        return {
            'today': self.stats,
            'total_viewed': len(self.viewed_stories.get('stories', [])),
            'remaining_today': self.config['daily_limit'] - self.stats['viewed_today']
        }
