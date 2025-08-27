from rest_framework import serializers
from .models import CourseCategory, Instructor, Course, Syllabus, Module


class CourseCategorySerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseCategory
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
            "courses_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "courses_count"]

    def get_courses_count(self, obj):
        return obj.courses.count()


class InstructorSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    companies_list = serializers.SerializerMethodField()

    class Meta:
        model = Instructor
        fields = [
            "id",
            "name",
            "designation",
            "years_of_experience",
            "companies",
            "companies_list",
            "courses_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "companies_list",
            "courses_count",
        ]

    def get_courses_count(self, obj):
        return obj.courses.count()

    def get_companies_list(self, obj):
        """Convert comma-separated companies string to list"""
        if obj.companies:
            return [
                company.strip()
                for company in obj.companies.split(",")
                if company.strip()
            ]
        return []


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "duration_weeks",
            "topics",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SyllabusSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    modules_count = serializers.SerializerMethodField()

    class Meta:
        model = Syllabus
        fields = [
            "id",
            "description",
            "modules",
            "modules_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "modules_count"]

    def get_modules_count(self, obj):
        return obj.modules.count()


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing courses"""

    category_name = serializers.CharField(source="category.name", read_only=True)
    instructors_names = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "duration_weeks",
            "num_enrolled",
            "level",
            "rating",
            "price",
            "category_name",
            "instructors_names",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_instructors_names(self, obj):
        return [instructor.name for instructor in obj.instructors.all()]


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with nested relationships"""

    category = CourseCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )
    instructors = InstructorSerializer(many=True, read_only=True)
    instructor_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False, allow_empty=True
    )
    syllabus = SyllabusSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "duration_weeks",
            "num_enrolled",
            "level",
            "rating",
            "price",
            "accessibility_features",
            "learning_objectives",
            "category",
            "category_id",
            "instructors",
            "instructor_ids",
            "syllabus",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "num_enrolled"]

    def create(self, validated_data):
        category_id = validated_data.pop("category_id", None)
        instructor_ids = validated_data.pop("instructor_ids", [])

        course = Course.objects.create(**validated_data)

        if category_id:
            try:
                category = CourseCategory.objects.get(id=category_id)
                course.category = category
                course.save()
            except CourseCategory.DoesNotExist:
                pass

        if instructor_ids:
            instructors = Instructor.objects.filter(id__in=instructor_ids)
            course.instructors.set(instructors)

        return course

    def update(self, instance, validated_data):
        category_id = validated_data.pop("category_id", None)
        instructor_ids = validated_data.pop("instructor_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if category_id is not None:
            if category_id:
                try:
                    category = CourseCategory.objects.get(id=category_id)
                    instance.category = category
                    instance.save()
                except CourseCategory.DoesNotExist:
                    pass
            else:
                instance.category = None
                instance.save()

        if instructor_ids is not None:
            instructors = Instructor.objects.filter(id__in=instructor_ids)
            instance.instructors.set(instructors)

        return instance


class SyllabusCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating syllabus"""

    course_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Syllabus
        fields = ["id", "course_id", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        course_id = validated_data.pop("course_id")
        course = Course.objects.get(id=course_id)
        syllabus = Syllabus.objects.create(course=course, **validated_data)
        return syllabus


class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating modules"""

    syllabus_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Module
        fields = [
            "id",
            "syllabus_id",
            "title",
            "duration_weeks",
            "topics",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        syllabus_id = validated_data.pop("syllabus_id")
        syllabus = Syllabus.objects.get(id=syllabus_id)
        module = Module.objects.create(syllabus=syllabus, **validated_data)
        return module
