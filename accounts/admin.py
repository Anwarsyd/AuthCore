from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_verified")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_verified",)