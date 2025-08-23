from django.db import models
import uuid


# Base abstract model for UUID + timestamps
class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CourseCategory(TimeStampedUUIDModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Course Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Instructor(TimeStampedUUIDModel):
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    years_of_experience = models.PositiveIntegerField()
    companies = models.TextField(help_text="Comma-separated list of companies involved")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(TimeStampedUUIDModel):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    duration_weeks = models.PositiveIntegerField()
    num_enrolled = models.PositiveIntegerField(default=0)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    category = models.ForeignKey(
        CourseCategory, related_name="courses", on_delete=models.SET_NULL, null=True
    )

    # Many-to-many instructor relationship
    instructors = models.ManyToManyField(Instructor, related_name="courses")

    # Bullet point fields
    accessibility_features = models.JSONField(
        default=list,
        help_text="List of access features, e.g. ['Lifetime access', 'Certificate']",
    )
    learning_objectives = models.JSONField(
        default=list, help_text="List of learning objectives as bullet points"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["category"]),
            models.Index(fields=["price"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return self.title


class Syllabus(TimeStampedUUIDModel):
    course = models.OneToOneField(
        Course, related_name="syllabus", on_delete=models.CASCADE
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Syllabi"

    def __str__(self):
        return f"Syllabus for {self.course.title}"


class Module(TimeStampedUUIDModel):
    syllabus = models.ForeignKey(
        Syllabus, related_name="modules", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    duration_weeks = models.PositiveIntegerField()
    topics = models.JSONField(
        default=list, help_text="List of bullet points describing module topics"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} ({self.syllabus.course.title})"
