import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import ContentItem

TMDB_API_KEY = 'e4d066183388802a3ae8d91da0579af9'
TMDB_BASE = 'https://api.themoviedb.org/3'
JIKAN_BASE = 'https://api.jikan.moe/v4'
OPENLIBRARY_BASE = 'https://openlibrary.org'

CTX = ssl.create_default_context()


def fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Trakory/1.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        print(f"[TRAKORY] fetch error: {url} -> {e}")
        return {}


def tmdb_get(endpoint, params=None):
    p = {'api_key': TMDB_API_KEY, 'language': 'en-US'}
    if params:
        p.update(params)
    url = f"{TMDB_BASE}{endpoint}?{urllib.parse.urlencode(p)}"
    return fetch(url)


def jikan_get(endpoint):
    return fetch(f"{JIKAN_BASE}{endpoint}")


def openlibrary_get(query):
    url = f"{OPENLIBRARY_BASE}/search.json?q={urllib.parse.quote(query)}&limit=8&fields=key,title,author_name,first_publish_year,cover_i,subject,ratings_average"
    return fetch(url)


def format_movie(item):
    return {
        'id': f"mv_{item.get('id')}",
        'title': item.get('title', ''),
        'year': (item.get('release_date') or '')[:4],
        'rating': round(item.get('vote_average', 0), 1),
        'genre': 'Movie',
        'overview': item.get('overview', ''),
        'img': f"https://image.tmdb.org/t/p/w200{item['poster_path']}" if item.get('poster_path') else '',
        'type': 'movie',
    }


def format_series(item):
    return {
        'id': f"tv_{item.get('id')}",
        'title': item.get('name', ''),
        'year': (item.get('first_air_date') or '')[:4],
        'rating': round(item.get('vote_average', 0), 1),
        'genre': 'Series',
        'overview': item.get('overview', ''),
        'img': f"https://image.tmdb.org/t/p/w200{item['poster_path']}" if item.get('poster_path') else '',
        'type': 'series',
    }


def format_anime(item):
    return {
        'id': f"an_{item.get('mal_id')}",
        'title': item.get('title', ''),
        'year': str(item.get('year') or ''),
        'rating': round(item.get('score') or 0, 1),
        'genre': (item.get('genres') or [{}])[0].get('name', 'Anime') if item.get('genres') else 'Anime',
        'overview': item.get('synopsis', ''),
        'img': (item.get('images') or {}).get('jpg', {}).get('image_url', ''),
        'type': 'anime',
    }


def format_book(item):
    cover_id = item.get('cover_i')
    return {
        'id': f"bk_{(item.get('key','/')).split('/')[-1]}",
        'title': item.get('title', ''),
        'year': str(item.get('first_publish_year') or ''),
        'rating': round(float(item.get('ratings_average') or 0), 1),
        'genre': (item.get('subject') or ['Book'])[0][:20],
        'overview': f"By {', '.join((item.get('author_name') or ['Unknown'])[:2])}",
        'img': f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else '',
        'type': 'book',
    }


@login_required
def browse(request):
    return render(request, 'tracker/browse.html')


@login_required
@require_GET
def api_browse(request):
    tab = request.GET.get('tab', 'movies')
    results = {}

    if tab == 'movies':
        trending = tmdb_get('/trending/movie/week')
        top_rated = tmdb_get('/movie/top_rated')
        upcoming = tmdb_get('/movie/upcoming')
        results = {
            'Trending This Week': [format_movie(m) for m in (trending.get('results') or [])[:10]],
            'Top Rated': [format_movie(m) for m in (top_rated.get('results') or [])[:10]],
            'Upcoming': [format_movie(m) for m in (upcoming.get('results') or [])[:10]],
        }
    elif tab == 'series':
        trending = tmdb_get('/trending/tv/week')
        top_rated = tmdb_get('/tv/top_rated')
        popular = tmdb_get('/tv/popular')
        results = {
            'Trending This Week': [format_series(s) for s in (trending.get('results') or [])[:10]],
            'Top Rated': [format_series(s) for s in (top_rated.get('results') or [])[:10]],
            'Popular Now': [format_series(s) for s in (popular.get('results') or [])[:10]],
        }
    elif tab == 'anime':
        top = jikan_get('/top/anime?filter=airing&limit=10')
        popular = jikan_get('/top/anime?filter=bypopularity&limit=10')
        results = {
            'Currently Airing': [format_anime(a) for a in (top.get('data') or [])[:10]],
            'Most Popular': [format_anime(a) for a in (popular.get('data') or [])[:10]],
        }
    elif tab == 'books':
        for label, query in [('Fiction Bestsellers','fiction bestseller'),('Self Help','self help popular'),('Science','science nonfiction')]:
            data = openlibrary_get(query)
            results[label] = [format_book(b) for b in (data.get('docs') or [])[:10]]

    return JsonResponse({'sections': results})


@login_required
@require_GET
def api_search(request):
    q = request.GET.get('q', '').strip()
    tab = request.GET.get('tab', 'movies')
    if not q:
        return JsonResponse({'results': []})

    items = []
    if tab == 'movies':
        data = tmdb_get('/search/movie', {'query': q})
        items = [format_movie(m) for m in (data.get('results') or [])[:10]]
    elif tab == 'series':
        data = tmdb_get('/search/tv', {'query': q})
        items = [format_series(s) for s in (data.get('results') or [])[:10]]
    elif tab == 'anime':
        data = fetch(f"{JIKAN_BASE}/anime?q={urllib.parse.quote(q)}&limit=10")
        items = [format_anime(a) for a in (data.get('data') or [])[:10]]
    elif tab == 'books':
        data = openlibrary_get(q)
        items = [format_book(b) for b in (data.get('docs') or [])[:10]]

    return JsonResponse({'results': items})


@login_required
@require_GET
def api_recommendations(request):
    user_items = ContentItem.objects.filter(user=request.user)
    high_rated = list(user_items.filter(rating__gte=4).order_by('-rating')[:5])
    completed = list(user_items.filter(status='Completed').order_by('-rating')[:5])
    seed_items = high_rated or completed

    if not seed_items:
        return JsonResponse({'recommendations': [], 'reason': 'no_data'})

    genres_liked = [i.genre for i in seed_items if i.genre]
    titles_liked = [i.title for i in seed_items]
    cat_count = {}
    for i in seed_items:
        cat_count[i.category] = cat_count.get(i.category, 0) + 1

    top_category = max(cat_count, key=cat_count.get)
    top_genre = genres_liked[0] if genres_liked else ''
    recs = []

    if top_category in ('movie', 'series'):
        media_type = 'movie' if top_category == 'movie' else 'tv'
        genre_map = {'Action':28,'Comedy':35,'Drama':18,'Horror':27,'Sci-Fi':878,
                     'Romance':10749,'Thriller':53,'Crime':80,'Fantasy':14,'Animation':16}
        genre_id = genre_map.get(top_genre)
        if genre_id:
            data = tmdb_get(f'/discover/{media_type}', {'with_genres': genre_id, 'sort_by': 'vote_average.desc', 'vote_count.gte': 100})
            fmt = format_movie if media_type == 'movie' else format_series
            recs = [fmt(i) for i in (data.get('results') or [])[:8]]
        if not recs:
            data = tmdb_get(f'/{media_type}/popular')
            fmt = format_movie if media_type == 'movie' else format_series
            recs = [fmt(i) for i in (data.get('results') or [])[:8]]
    elif top_category == 'anime':
        data = jikan_get('/top/anime?filter=bypopularity&limit=10')
        recs = [format_anime(a) for a in (data.get('data') or [])[:8]]
    elif top_category == 'book':
        data = openlibrary_get(top_genre or 'bestseller')
        recs = [format_book(b) for b in (data.get('docs') or [])[:8]]

    tracked = {i.title.lower() for i in user_items}
    recs = [r for r in recs if r['title'].lower() not in tracked][:6]

    return JsonResponse({'recommendations': recs, 'based_on': titles_liked[:3], 'genre': top_genre, 'category': top_category})


@login_required
@csrf_exempt
@require_POST
def api_add_to_list(request):
    try:
        data = json.loads(request.body)
        title = data.get('title', '')
        category = {'movie':'movie','series':'series','anime':'anime','book':'book'}.get(data.get('type','movie'),'movie')
        status = data.get('status', 'Plan to Watch')
        status_map = {'book': {'Plan to Watch':'Plan to Read','Watching':'Reading','Completed':'Completed'}}
        final_status = status_map.get(category, {}).get(status, status)
        existing = ContentItem.objects.filter(user=request.user, title__iexact=title).first()
        if existing:
            existing.status = final_status
            existing.save()
            return JsonResponse({'ok': True, 'action': 'updated'})
        ContentItem.objects.create(
            user=request.user, title=title, category=category,
            status=final_status, genre=data.get('genre',''), notes=data.get('overview','')[:200])
        return JsonResponse({'ok': True, 'action': 'added'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
