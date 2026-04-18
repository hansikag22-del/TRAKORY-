from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Count, Avg, Sum
from .models import ContentItem
import json

MOOD_MAP = {
    'funny': {
        'genres': ['Comedy', 'Animation'],
        'keywords': ['comedy', 'funny', 'laugh', 'humor'],
        'tmdb_genre': 35,
        'emoji': '😂',
        'label': 'Something Funny',
        'color': '#f7c46a',
    },
    'scary': {
        'genres': ['Horror', 'Thriller'],
        'keywords': ['horror', 'scary', 'thriller', 'dark'],
        'tmdb_genre': 27,
        'emoji': '😱',
        'label': 'Something Scary',
        'color': '#f76a6a',
    },
    'romantic': {
        'genres': ['Romance', 'Drama'],
        'keywords': ['romance', 'love', 'drama', 'romantic'],
        'tmdb_genre': 10749,
        'emoji': '💕',
        'label': 'Something Romantic',
        'color': '#f76ab0',
    },
    'mindbending': {
        'genres': ['Sci-Fi', 'Mystery', 'Thriller'],
        'keywords': ['sci-fi', 'mystery', 'twist', 'mind'],
        'tmdb_genre': 878,
        'emoji': '🤯',
        'label': 'Mind-Bending',
        'color': '#7c6af7',
    },
    'action': {
        'genres': ['Action', 'Adventure'],
        'keywords': ['action', 'adventure', 'fight', 'war'],
        'tmdb_genre': 28,
        'emoji': '💥',
        'label': 'Full of Action',
        'color': '#f7946a',
    },
    'chill': {
        'genres': ['Animation', 'Family', 'Comedy'],
        'keywords': ['chill', 'relax', 'family', 'light'],
        'tmdb_genre': 16,
        'emoji': '😌',
        'label': 'Something Chill',
        'color': '#6af7c4',
    },
    'inspiring': {
        'genres': ['Drama', 'Documentary', 'Biography'],
        'keywords': ['inspiring', 'motivating', 'true story', 'biography'],
        'tmdb_genre': 18,
        'emoji': '✨',
        'label': 'Inspiring Story',
        'color': '#6aaff7',
    },
    'fantasy': {
        'genres': ['Fantasy', 'Adventure'],
        'keywords': ['fantasy', 'magic', 'adventure', 'epic'],
        'tmdb_genre': 14,
        'emoji': '🧙',
        'label': 'Fantasy & Magic',
        'color': '#c46af7',
    },
}

EPISODE_RUNTIME = {
    'movie': 120,
    'series': 45,
    'anime': 24,
    'book': 0,
    'game': 0,
}


@login_required
def stats_page(request):
    return render(request, 'tracker/stats.html')


@login_required
def mood_page(request):
    return render(request, 'tracker/mood.html', {'moods': MOOD_MAP})


@login_required
@require_GET
def api_stats(request):
    items = ContentItem.objects.filter(user=request.user)
    total = items.count()

    if total == 0:
        return JsonResponse({'empty': True})

    # Status breakdown
    status_data = {}
    for item in items:
        s = item.status
        status_data[s] = status_data.get(s, 0) + 1

    # Category breakdown
    cat_data = {}
    for key, label in [('movie','Movies'),('series','Series'),('anime','Anime'),('book','Books'),('game','Games')]:
        c = items.filter(category=key).count()
        if c > 0:
            cat_data[label] = c

    # Genre breakdown (top 6)
    genre_data = {}
    for item in items:
        if item.genre:
            genre_data[item.genre] = genre_data.get(item.genre, 0) + 1
    genre_data = dict(sorted(genre_data.items(), key=lambda x: x[1], reverse=True)[:6])

    # Rating distribution
    rating_dist = {str(i): 0 for i in range(1, 6)}
    for item in items.exclude(rating__isnull=True):
        rating_dist[str(item.rating)] = rating_dist.get(str(item.rating), 0) + 1

    # Average rating
    avg = items.exclude(rating__isnull=True).aggregate(avg=Avg('rating'))['avg']
    avg_rating = round(avg, 1) if avg else 0

    # Hours watched estimate
    hours = 0
    for item in items.filter(status='Completed'):
        runtime = EPISODE_RUNTIME.get(item.category, 0)
        progress = item.progress or 1
        hours += (runtime * progress) / 60
    hours = round(hours)

    # Top rated items
    top_rated = list(
        items.exclude(rating__isnull=True)
        .order_by('-rating', '-updated_at')[:5]
        .values('title', 'category', 'rating', 'status')
    )

    # Monthly activity (last 6 months)
    from datetime import datetime, timedelta
    from django.utils import timezone
    monthly = {}
    for i in range(5, -1, -1):
        d = timezone.now() - timedelta(days=30*i)
        label = d.strftime('%b')
        count = items.filter(
            updated_at__year=d.year,
            updated_at__month=d.month
        ).count()
        monthly[label] = count

    # Completion rate
    completed = items.filter(status='Completed').count()
    completion_rate = round((completed / total) * 100) if total > 0 else 0

    # Favourite genre
    fav_genre = max(genre_data, key=genre_data.get) if genre_data else 'N/A'

    return JsonResponse({
        'empty': False,
        'total': total,
        'completed': completed,
        'avg_rating': avg_rating,
        'hours_watched': hours,
        'completion_rate': completion_rate,
        'fav_genre': fav_genre,
        'status_data': status_data,
        'cat_data': cat_data,
        'genre_data': genre_data,
        'rating_dist': rating_dist,
        'monthly': monthly,
        'top_rated': top_rated,
    })


@login_required
@require_GET
def api_mood(request):
    import urllib.request
    import urllib.parse
    import ssl

    mood = request.GET.get('mood', 'action')
    category = request.GET.get('category', 'movie')

    mood_info = MOOD_MAP.get(mood, MOOD_MAP['action'])
    tmdb_genre = mood_info['tmdb_genre']

    try:
        from .browse_views import TMDB_API_KEY, format_movie, format_series, format_anime, jikan_get, fetch, CTX

        results = []

        if category == 'movie':
            url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={tmdb_genre}&sort_by=vote_average.desc&vote_count.gte=200&language=en-US"
            data = fetch(url)
            results = [format_movie(m) for m in (data.get('results') or [])[:12]]

        elif category == 'series':
            url = f"https://api.themoviedb.org/3/discover/tv?api_key={TMDB_API_KEY}&with_genres={tmdb_genre}&sort_by=vote_average.desc&vote_count.gte=100&language=en-US"
            data = fetch(url)
            results = [format_series(s) for s in (data.get('results') or [])[:12]]

        elif category == 'anime':
            genre_anime_map = {
                35: 'comedy', 27: 'horror', 878: 'psychological',
                28: 'action', 16: 'slice of life', 14: 'fantasy',
                10749: 'romance', 18: 'drama',
            }
            anime_genre = genre_anime_map.get(tmdb_genre, 'action')
            data = jikan_get(f'/anime?genres={anime_genre}&order_by=score&sort=desc&limit=12')
            results = [format_anime(a) for a in (data.get('data') or [])[:12]]

        # Filter already tracked
        user_items = ContentItem.objects.filter(user=request.user)
        tracked = {i.title.lower() for i in user_items}
        results = [r for r in results if r['title'].lower() not in tracked][:8]

        return JsonResponse({
            'results': results,
            'mood': mood,
            'mood_info': {
                'label': mood_info['label'],
                'emoji': mood_info['emoji'],
                'color': mood_info['color'],
            }
        })

    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)})
