from django.db import models
from django.contrib.auth.models import User

CATEGORY_CHOICES = [
    ('movie', 'Movie'),
    ('series', 'Web Series'),
    ('anime', 'Anime'),
    ('book', 'Book'),
    ('game', 'Game'),
]

STATUS_CHOICES_BY_CATEGORY = {
    'movie':  ['Watching', 'Completed', 'Plan to Watch', 'Dropped'],
    'series': ['Watching', 'Completed', 'Plan to Watch', 'On Hold', 'Dropped'],
    'anime':  ['Watching', 'Completed', 'Plan to Watch', 'On Hold', 'Dropped'],
    'book':   ['Reading', 'Completed', 'Plan to Read', 'On Hold', 'Dropped'],
    'game':   ['Playing', 'Completed', 'Plan to Play', 'On Hold', 'Dropped'],
}

ALL_STATUS_CHOICES = [
    ('Watching', 'Watching'),
    ('Reading', 'Reading'),
    ('Playing', 'Playing'),
    ('Completed', 'Completed'),
    ('Plan to Watch', 'Plan to Watch'),
    ('Plan to Read', 'Plan to Read'),
    ('Plan to Play', 'Plan to Play'),
    ('On Hold', 'On Hold'),
    ('Dropped', 'Dropped'),
]

RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

class ContentItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_items')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=ALL_STATUS_CHOICES)
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    progress = models.IntegerField(default=0, help_text="Episodes watched / Pages read")
    total = models.IntegerField(null=True, blank=True, help_text="Total episodes / pages")
    notes = models.TextField(blank=True)
    genre = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.category})"

    def progress_percent(self):
        if self.total and self.total > 0:
            return min(int((self.progress / self.total) * 100), 100)
        return 0

    def rating_stars(self):
        if self.rating:
            return '★' * self.rating + '☆' * (5 - self.rating)
        return '—'
