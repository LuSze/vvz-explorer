from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.SearchView.as_view(), name="search"),
    path("similar/<str:number>/", views.SimilarLecturesView.as_view(), name="similar"),
    path("lectures/<str:number>/", views.LectureDetailView.as_view(), name="lecture-detail"),
    path("lectures/", views.LectureListView.as_view(), name="lecture-list"),
    path("study-tracks/", views.StudyTracksView.as_view(), name="study-tracks"),
    path("categories/level1/", views.Level1CategoriesView.as_view(), name="categories-level1"),
    path("categories/level2/", views.Level2CategoriesView.as_view(), name="categories-level2"),
    path("categories/level3/", views.Level3CategoriesView.as_view(), name="categories-level3"),
    path("categories/tree/", views.CategoryTreeView.as_view(), name="category-tree"),
    path("suggest/", views.SmartSuggestView.as_view(), name="smart-suggest"),
    path("categories/path/", views.CategoryPathView.as_view(), name="category-path"),
]
