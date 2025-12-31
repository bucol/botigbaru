import random

class HashtagGenerator:
    def __init__(self):
        # Base hashtag populer, bisa tambah di .env kalau mau
        self.base_tags = {
            'general': ['love', 'instagood', 'photooftheday', 'fashion', 'beautiful'],
            'food': ['food', 'foodporn', 'delicious', 'yum', 'eat'],
            'travel': ['travel', 'adventure', 'wanderlust', 'vacation', 'explore'],
            # Tambah kategori lain kalau perlu
        }

    def generate_hashtags(self, keyword: str, count: int = 5):
        """Generate variasi hashtag kreatif dari keyword, mirip manusia (acak + variasi)"""
        tags = []
        words = keyword.lower().split()
        for word in words:
            tags.append(word)
            tags.append(f"{word}love")  # Variasi random
            tags.append(f"best{word}")
        # Tambah dari base
        category = random.choice(list(self.base_tags.keys()))
        tags.extend(random.sample(self.base_tags[category], min(3, len(self.base_tags[category]))))
        # Acak dan limit
        random.shuffle(tags)
        return [f"#{tag}" for tag in tags[:count]]