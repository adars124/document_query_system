from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Tenant


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "tenant", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "tenant")
    fieldsets = UserAdmin.fieldsets + (("Tenant Info", {"fields": ("tenant",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Tenant Info", {"fields": ("tenant",)}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Tenant)
