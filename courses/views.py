from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404

from core.utils import Response

from .models import CourseCategory, Instructor, Course, Syllabus, Module
from .serializers import (
    CourseCategorySerializer,
    InstructorSerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    SyllabusSerializer,
    SyllabusCreateUpdateSerializer,
    ModuleSerializer,
    ModuleCreateUpdateSerializer,
)


class CourseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing course categories.
    Provides CRUD operations and category-specific endpoints.
    """

    queryset = CourseCategory.objects.all().order_by("name")
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def list(self, request, *args, **kwargs):
        """List all course categories"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            message="Course categories retrieved successfully",
            data=serializer.data,
            additional_info={"total_count": queryset.count()},
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific course category"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Category '{instance.name}' retrieved successfully",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        """Create a new course category"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response(
            status=status.HTTP_201_CREATED,
            message=f"Category '{instance.name}' created successfully",
            data=serializer.data,
            additional_info={"category_id": str(instance.id)},
        )

    def update(self, request, *args, **kwargs):
        """Update a course category"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            message=f"Category '{updated_instance.name}' updated successfully",
            data=serializer.data,
            additional_info={
                "category_id": str(updated_instance.id),
                "update_type": "partial" if partial else "full",
            },
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a course category"""
        instance = self.get_object()
        category_name = instance.name
        category_id = str(instance.id)

        self.perform_destroy(instance)
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            message=f"Category '{category_name}' deleted successfully",
            additional_info={"deleted_category_id": category_id},
        )

    @action(detail=True, methods=["get"])
    def courses(self, request, pk=None):
        """Get all courses in this category"""
        category = self.get_object()
        courses = category.courses.all().order_by("-created_at")
        serializer = CourseListSerializer(
            courses, many=True, context={"request": request}
        )
        return Response(
            status=status.HTTP_200_OK,
            message=f"Courses in category '{category.name}' retrieved successfully",
            data=serializer.data,
        )


class InstructorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing instructors.
    Provides CRUD operations and instructor-specific endpoints.
    """

    queryset = Instructor.objects.all().order_by("name")
    serializer_class = InstructorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "designation", "companies"]
    ordering_fields = ["name", "years_of_experience", "created_at"]
    filterset_fields = ["years_of_experience"]
    ordering = ["name"]

    def list(self, request, *args, **kwargs):
        """List all instructors"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            message="Instructors retrieved successfully",
            data=serializer.data,
            additional_info={"total_count": queryset.count()},
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific instructor"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Instructor '{instance.name}' retrieved successfully",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        """Create a new instructor"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response(
            status=status.HTTP_201_CREATED,
            message=f"Instructor '{instance.name}' created successfully",
            data=serializer.data,
            additional_info={
                "instructor_id": str(instance.id),
                "years_of_experience": instance.years_of_experience,
            },
        )

    def update(self, request, *args, **kwargs):
        """Update an instructor"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            message=f"Instructor '{updated_instance.name}' updated successfully",
            data=serializer.data,
            additional_info={
                "instructor_id": str(updated_instance.id),
                "update_type": "partial" if partial else "full",
            },
        )

    def destroy(self, request, *args, **kwargs):
        """Delete an instructor"""
        instance = self.get_object()
        instructor_name = instance.name
        instructor_id = str(instance.id)

        self.perform_destroy(instance)
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            message=f"Instructor '{instructor_name}' deleted successfully",
            additional_info={"deleted_instructor_id": instructor_id},
        )

    @action(detail=True, methods=["get"])
    def courses(self, request, pk=None):
        """Get all courses taught by this instructor"""
        instructor = self.get_object()
        courses = instructor.courses.all().order_by("-created_at")
        serializer = CourseListSerializer(
            courses, many=True, context={"request": request}
        )
        return Response(
            status=status.HTTP_200_OK,
            message=f"Courses taught by '{instructor.name}' retrieved successfully",
            data=serializer.data,
        )

    @action(detail=False, methods=["get"])
    def top_experienced(self, request):
        """Get instructors with highest years of experience"""
        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10

        instructors = self.queryset.order_by("-years_of_experience")[:limit]
        serializer = self.get_serializer(instructors, many=True)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Top {limit} experienced instructors retrieved successfully",
            data=serializer.data,
        )


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing courses.
    Provides CRUD operations, filtering, and course-specific endpoints.
    """

    queryset = (
        Course.objects.select_related("category")
        .prefetch_related("instructors")
        .order_by("-created_at")
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["title", "description", "category__name", "instructors__name"]
    ordering_fields = [
        "title",
        "price",
        "rating",
        "duration_weeks",
        "num_enrolled",
        "created_at",
    ]
    filterset_fields = ["level", "category", "instructors"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by price range
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass

        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass

        # Filter by rating range
        min_rating = self.request.query_params.get("min_rating")
        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass

        # Filter by duration range
        min_duration = self.request.query_params.get("min_duration")
        max_duration = self.request.query_params.get("max_duration")

        if min_duration:
            try:
                queryset = queryset.filter(duration_weeks__gte=int(min_duration))
            except (ValueError, TypeError):
                pass

        if max_duration:
            try:
                queryset = queryset.filter(duration_weeks__lte=int(max_duration))
            except (ValueError, TypeError):
                pass

        return queryset

    def list(self, request, *args, **kwargs):
        """List all courses with filtering"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return Response(
                status=status.HTTP_200_OK,
                message="Courses retrieved successfully",
                data=paginated_response.data,
                additional_info={
                    "total_count": queryset.count(),
                    "filters_applied": bool(request.query_params),
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            message="Courses retrieved successfully",
            data=serializer.data,
            additional_info={
                "total_count": queryset.count(),
                "filters_applied": bool(request.query_params),
            },
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific course"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Course '{instance.title}' retrieved successfully",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        """Create a new course"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response(
            status=status.HTTP_201_CREATED,
            message=f"Course '{instance.title}' created successfully",
            data=serializer.data,
            additional_info={
                "course_id": str(instance.id),
                "level": instance.level,
                "duration_weeks": instance.duration_weeks,
            },
        )

    def update(self, request, *args, **kwargs):
        """Update a course"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            message=f"Course '{updated_instance.title}' updated successfully",
            data=serializer.data,
            additional_info={
                "course_id": str(updated_instance.id),
                "update_type": "partial" if partial else "full",
            },
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a course"""
        instance = self.get_object()
        course_title = instance.title
        course_id = str(instance.id)

        self.perform_destroy(instance)
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            message=f"Course '{course_title}' deleted successfully",
            additional_info={
                "deleted_course_id": course_id,
            },
        )

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured courses (top rated with high enrollment)"""
        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10

        courses = (
            self.get_queryset()
            .filter(rating__gte=4.0, num_enrolled__gte=100)
            .order_by("-rating", "-num_enrolled")[:limit]
        )

        serializer = CourseListSerializer(
            courses, many=True, context={"request": request}
        )
        return Response(
            status=status.HTTP_200_OK,
            message=f"Featured courses retrieved successfully",
            data=serializer.data,
            additional_info={"total_count": courses.count(), "limit": limit},
        )

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get most popular courses by enrollment"""
        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10

        courses = self.get_queryset().order_by("-num_enrolled")[:limit]
        serializer = CourseListSerializer(
            courses, many=True, context={"request": request}
        )
        return Response(
            status=status.HTTP_200_OK,
            message=f"Popular courses retrieved successfully",
            data=serializer.data,
            additional_info={"total_count": courses.count(), "limit": limit},
        )

    @action(detail=False, methods=["get"])
    def top_rated(self, request):
        """Get top rated courses"""
        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10

        courses = (
            self.get_queryset()
            .filter(rating__gt=0)
            .order_by("-rating", "-num_enrolled")[:limit]
        )
        serializer = CourseListSerializer(
            courses, many=True, context={"request": request}
        )
        return Response(
            status=status.HTTP_200_OK,
            message=f"Top rated courses retrieved successfully",
            data=serializer.data,
            additional_info={"total_count": courses.count(), "limit": limit},
        )

    @action(detail=False, methods=["get"])
    def by_level(self, request):
        """Get courses grouped by level"""
        level = request.query_params.get("level")
        if not level or level not in ["beginner", "intermediate", "advanced"]:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                message="Invalid level parameter",
                error_details={
                    "level": [
                        "Please provide a valid level: beginner, intermediate, or advanced"
                    ]
                },
            )

        courses = self.get_queryset().filter(level=level)
        serializer = CourseListSerializer(
            courses, many=True, context={"request": request}
        )
        return Response(
            status=status.HTTP_200_OK,
            message=f"Courses at '{level}' level retrieved successfully",
            data=serializer.data,
            additional_info={"level": level, "total_count": courses.count()},
        )

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get course statistics"""
        queryset = self.get_queryset()

        stats = {
            "total_courses": queryset.count(),
            "average_rating": queryset.aggregate(avg_rating=Avg("rating"))["avg_rating"]
            or 0,
            "average_price": queryset.aggregate(avg_price=Avg("price"))["avg_price"]
            or 0,
            "total_enrolled": queryset.aggregate(total=Count("num_enrolled"))["total"]
            or 0,
            "level_distribution": {
                "beginner": queryset.filter(level="beginner").count(),
                "intermediate": queryset.filter(level="intermediate").count(),
                "advanced": queryset.filter(level="advanced").count(),
            },
            "categories_count": CourseCategory.objects.count(),
            "instructors_count": Instructor.objects.count(),
        }

        return Response(
            status=status.HTTP_200_OK,
            message="Course statistics retrieved successfully",
            data=stats,
        )

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        """Simulate course enrollment (increment num_enrolled)"""
        course = self.get_object()
        previous_enrollment = course.num_enrolled
        course.num_enrolled += 1
        course.save()

        serializer = self.get_serializer(course)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Successfully enrolled in course '{course.title}'",
            data={"course": serializer.data},
            additional_info={
                "previous_enrollment_count": previous_enrollment,
                "new_enrollment_count": course.num_enrolled,
            },
        )


class SyllabusViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing course syllabi.
    """

    queryset = (
        Syllabus.objects.select_related("course").prefetch_related("modules").all()
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["course__title", "description"]
    filterset_fields = ["course"]

    def list(self, request, *args, **kwargs):
        """List all syllabi"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            message="Course syllabi retrieved successfully",
            data=serializer.data,
            additional_info={"total_count": queryset.count()},
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific syllabus"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Syllabus for '{instance.course.title}' retrieved successfully",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        """Create a new syllabus"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response(
            status=status.HTTP_201_CREATED,
            message=f"Syllabus for '{instance.course.title}' created successfully",
            data=serializer.data,
            additional_info={
                "syllabus_id": str(instance.id),
                "course_title": instance.course.title,
            },
        )

    def update(self, request, *args, **kwargs):
        """Update a syllabus"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            message=f"Syllabus for '{updated_instance.course.title}' updated successfully",
            data=serializer.data,
            additional_info={
                "syllabus_id": str(updated_instance.id),
                "update_type": "partial" if partial else "full",
            },
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a syllabus"""
        instance = self.get_object()
        course_title = instance.course.title
        syllabus_id = str(instance.id)

        self.perform_destroy(instance)
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            message=f"Syllabus for '{course_title}' deleted successfully",
            additional_info={"deleted_syllabus_id": syllabus_id},
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SyllabusCreateUpdateSerializer
        return SyllabusSerializer

    @action(detail=True, methods=["get"])
    def modules(self, request, pk=None):
        """Get all modules for this syllabus"""
        syllabus = self.get_object()
        modules = syllabus.modules.all().order_by("order")
        serializer = ModuleSerializer(modules, many=True, context={"request": request})
        return Response(
            status=status.HTTP_200_OK,
            message=f"Modules for '{syllabus.course.title}' syllabus retrieved successfully",
            data=serializer.data,
            additional_info={
                "course_title": syllabus.course.title,
                "total_modules": modules.count(),
            },
        )


class ModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing syllabus modules.
    """

    queryset = Module.objects.select_related("syllabus", "syllabus__course").all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["title", "syllabus__course__title"]
    ordering_fields = ["order", "title", "duration_weeks"]
    filterset_fields = ["syllabus"]
    ordering = ["order"]

    def list(self, request, *args, **kwargs):
        """List all modules"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            message="Course modules retrieved successfully",
            data=serializer.data,
            additional_info={"total_count": queryset.count()},
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific module"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Module '{instance.title}' retrieved successfully",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        """Create a new module"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response(
            status=status.HTTP_201_CREATED,
            message=f"Module '{instance.title}' created successfully",
            data=serializer.data,
            additional_info={
                "module_id": str(instance.id),
                "course_title": instance.syllabus.course.title,
                "duration_weeks": instance.duration_weeks,
            },
        )

    def update(self, request, *args, **kwargs):
        """Update a module"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            message=f"Module '{updated_instance.title}' updated successfully",
            data=serializer.data,
            additional_info={
                "module_id": str(updated_instance.id),
                "update_type": "partial" if partial else "full",
            },
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a module"""
        instance = self.get_object()
        module_title = instance.title
        module_id = str(instance.id)

        self.perform_destroy(instance)
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            message=f"Module '{module_title}' deleted successfully",
            additional_info={"deleted_module_id": module_id},
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ModuleCreateUpdateSerializer
        return ModuleSerializer

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """Reorder modules within a syllabus"""
        module_orders = request.data.get("modules", [])
        if not isinstance(module_orders, list):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                message="Invalid request format",
                error_details={
                    "modules": ["modules must be a list of {id, order} objects"]
                },
            )

        updated_modules = []
        skipped_items = []
        for item in module_orders:
            if not isinstance(item, dict) or "id" not in item or "order" not in item:
                skipped_items.append(item)
                continue

            try:
                module = Module.objects.get(id=item["id"])
                module.order = item["order"]
                module.save()
                updated_modules.append(module)
            except Module.DoesNotExist:
                skipped_items.append(item)
                continue

        serializer = ModuleSerializer(
            updated_modules, many=True, context={"request": request}
        )
        return Response(
            status=status.HTTP_200_OK,
            message=f"Successfully reordered {len(updated_modules)} modules",
            data={"modules": serializer.data},
            additional_info={
                "updated_count": len(updated_modules),
                "skipped_count": len(skipped_items),
                "skipped_items": skipped_items if skipped_items else None,
            },
        )
