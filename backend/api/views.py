from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import (
    search_lectures,
    similar_lectures,
    get_lecture_by_number,
    list_lectures,
    list_study_tracks,
    list_level1_categories,
    list_level2_categories,
    list_level3_categories,
    get_category_tree,
    smart_suggest,
    get_offered_in,
    resolve_category_path,
)


def _semester(request):
    return request.query_params.get("semester", "").strip() or None


class SearchView(APIView):
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=status.HTTP_400_BAD_REQUEST)
        k = int(request.query_params.get("k", 20))
        study_track = request.query_params.get("study_track", "").strip()
        study_track = study_track or None
        cross_semester = request.query_params.get("cross_semester", "").strip().lower() in ("true", "1")
        results = search_lectures(query, k, study_track, semester=_semester(request), cross_semester=cross_semester)
        return Response({"query": query, "count": len(results), "results": results})


class SimilarLecturesView(APIView):
    def get(self, request, number):
        k = int(request.query_params.get("k", 20))
        results = similar_lectures(number, k, semester=_semester(request))
        if results is None:
            return Response({"error": f"Lecture '{number}' not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"lecture_number": number, "count": len(results), "results": results})


class LectureDetailView(APIView):
    def get(self, request, number):
        lecture = get_lecture_by_number(number, semester=_semester(request))
        if not lecture:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        offered_in = get_offered_in(lecture.get("id"), semester=_semester(request))
        lecture["offered_in"] = offered_in
        return Response(lecture)


class LectureListView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "").strip()
        search = search or None
        study_track = request.query_params.get("study_track", "").strip()
        study_track = study_track or None
        fields = request.query_params.get("fields", "").strip()
        fields = fields or None
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        if page < 1: page = 1
        if page_size < 1: page_size = 20
        if page_size > 100: page_size = 100
        level1_id = request.query_params.get("level1_id")
        level2_id = request.query_params.get("level2_id")
        level3_id = request.query_params.get("level3_id")
        level1_id = int(level1_id) if level1_id else None
        level2_id = int(level2_id) if level2_id else None
        level3_id = int(level3_id) if level3_id else None
        lectures, total = list_lectures(search, study_track, fields, page, page_size, semester=_semester(request), level1_id=level1_id, level2_id=level2_id, level3_id=level3_id)
        return Response({"count": len(lectures), "total": total, "page": page, "page_size": page_size, "results": lectures})


class StudyTracksView(APIView):
    def get(self, request):
        tracks = list_study_tracks(semester=_semester(request))
        return Response({"count": len(tracks), "results": tracks})


class Level1CategoriesView(APIView):
    def get(self, request):
        study_track = request.query_params.get("study_track", "").strip()
        if not study_track:
            return Response({"error": "study_track query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        categories = list_level1_categories(study_track, semester=_semester(request))
        return Response({"count": len(categories), "results": categories})


class Level2CategoriesView(APIView):
    def get(self, request):
        study_track = request.query_params.get("study_track", "").strip()
        level1_id = request.query_params.get("level1_id", "").strip()
        if not study_track or not level1_id:
            return Response({"error": "study_track and level1_id query parameters are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            level1_id = int(level1_id)
        except ValueError:
            return Response({"error": "level1_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        categories = list_level2_categories(study_track, level1_id, semester=_semester(request))
        return Response({"count": len(categories), "results": categories})


class Level3CategoriesView(APIView):
    def get(self, request):
        study_track = request.query_params.get("study_track", "").strip()
        level1_id = request.query_params.get("level1_id", "").strip()
        level2_id = request.query_params.get("level2_id", "").strip()
        if not study_track or not level1_id or not level2_id:
            return Response({"error": "study_track, level1_id, and level2_id query parameters are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            level1_id = int(level1_id)
            level2_id = int(level2_id)
        except ValueError:
            return Response({"error": "level1_id and level2_id must be integers"}, status=status.HTTP_400_BAD_REQUEST)
        categories = list_level3_categories(study_track, level1_id, level2_id, semester=_semester(request))
        return Response({"count": len(categories), "results": categories})


class CategoryTreeView(APIView):
    def get(self, request):
        study_track = request.query_params.get("study_track", "").strip()
        if not study_track:
            return Response({"error": "study_track query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        tree = get_category_tree(study_track, semester=_semester(request))
        return Response({"study_track": study_track, "tree": tree})


class SmartSuggestView(APIView):
    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q or len(q) < 2:
            return Response({"error": "q query parameter is required (min 2 chars)"}, status=status.HTTP_400_BAD_REQUEST)
        limit = int(request.query_params.get("limit", 8))
        results = smart_suggest(q, limit, semester=_semester(request))
        return Response({"query": q, "count": len(results), "results": results})


class CategoryPathView(APIView):
    def get(self, request):
        study_track = request.query_params.get("study_track", "").strip()
        level = request.query_params.get("level", "").strip()
        category_id = request.query_params.get("category_id", "").strip()
        if not study_track or not level or not category_id:
            return Response({"error": "study_track, level, and category_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            level = int(level)
            category_id = int(category_id)
        except ValueError:
            return Response({"error": "level and category_id must be integers"}, status=status.HTTP_400_BAD_REQUEST)
        if level not in (1, 2, 3):
            return Response({"error": "level must be 1, 2, or 3"}, status=status.HTTP_400_BAD_REQUEST)
        path = resolve_category_path(study_track, level, category_id, semester=_semester(request))
        if not path:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(path)
