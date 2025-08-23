from django.contrib import admin
from .models import CourseCategory, Instructor, Course, Syllabus, Module


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["name"]


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ["name", "designation", "years_of_experience", "created_at"]
    list_filter = ["years_of_experience", "created_at"]
    search_fields = ["name", "designation", "companies"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["name"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "designation", "years_of_experience")},
        ),
        (
            "Experience",
            {
                "fields": ("companies",),
                "description": "Enter company names separated by commas",
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ["title", "duration_weeks", "order"]
    ordering = ["order"]


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ["course", "created_at", "updated_at"]
    list_filter = ["created_at", "course__category"]
    search_fields = ["course__title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [ModuleInline]

    fieldsets = (
        ("Course Information", {"fields": ("course", "description")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["title", "syllabus", "duration_weeks", "order", "created_at"]
    list_filter = ["duration_weeks", "created_at", "syllabus__course__category"]
    search_fields = ["title", "syllabus__course__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["syllabus", "order"]

    fieldsets = (
        (
            "Module Information",
            {"fields": ("syllabus", "title", "duration_weeks", "order")},
        ),
        (
            "Content",
            {
                "fields": ("topics",),
                "description": 'Enter topics as a JSON list, e.g., ["Topic 1", "Topic 2"]',
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "level",
        "duration_weeks",
        "price",
        "rating",
        "num_enrolled",
        "created_at",
    ]
    list_filter = ["level", "category", "duration_weeks", "created_at", "rating"]
    search_fields = ["title", "description", "category__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    filter_horizontal = ["instructors"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "category")}),
        (
            "Course Details",
            {"fields": ("level", "duration_weeks", "price", "rating", "num_enrolled")},
        ),
        ("Instructors", {"fields": ("instructors",)}),
        (
            "Features & Objectives",
            {
                "fields": ("accessibility_features", "learning_objectives"),
                "description": 'Enter as JSON lists, e.g., ["Feature 1", "Feature 2"]',
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    # Add some useful actions
    actions = ["mark_as_beginner", "mark_as_intermediate", "mark_as_advanced"]

    def mark_as_beginner(self, request, queryset):
        updated = queryset.update(level="beginner")
        self.message_user(request, f"{updated} courses marked as beginner level.")

    mark_as_beginner.short_description = "Mark selected courses as beginner"

    def mark_as_intermediate(self, request, queryset):
        updated = queryset.update(level="intermediate")
        self.message_user(request, f"{updated} courses marked as intermediate level.")

    mark_as_intermediate.short_description = "Mark selected courses as intermediate"

    def mark_as_advanced(self, request, queryset):
        updated = queryset.update(level="advanced")
        self.message_user(request, f"{updated} courses marked as advanced level.")

    mark_as_advanced.short_description = "Mark selected courses as advanced"
