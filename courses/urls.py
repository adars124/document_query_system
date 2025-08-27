from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseCategoryViewSet,
    InstructorViewSet,
    CourseViewSet,
    SyllabusViewSet,
    ModuleViewSet,
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"categories", CourseCategoryViewSet, basename="category")
router.register(r"instructors", InstructorViewSet, basename="instructor")
router.register(r"", CourseViewSet, basename="course")
router.register(r"syllabi", SyllabusViewSet, basename="syllabus")
router.register(r"modules", ModuleViewSet, basename="module")

urlpatterns = [
    path("", include(router.urls)),
]
