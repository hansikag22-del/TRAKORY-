from django.urls import path
from . import views
from . import browse_views
from . import stats_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('list/', views.content_list, name='list'),
    path('add/', views.add_content, name='add'),
    path('edit/<int:pk>/', views.edit_content, name='edit'),
    path('delete/<int:pk>/', views.delete_content, name='delete'),
    path('browse/', browse_views.browse, name='browse'),
    path('stats/', stats_views.stats_page, name='stats'),
    path('mood/', stats_views.mood_page, name='mood'),
    path('api/browse/', browse_views.api_browse, name='api_browse'),
    path('api/search/', browse_views.api_search, name='api_search'),
    path('api/recommendations/', browse_views.api_recommendations, name='api_recommendations'),
    path('api/add-to-list/', browse_views.api_add_to_list, name='api_add_to_list'),
    path('api/stats/', stats_views.api_stats, name='api_stats'),
    path('api/mood/', stats_views.api_mood, name='api_mood'),
]
