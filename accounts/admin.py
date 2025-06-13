from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SignupRequest

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'employee_id', 'name', 'is_first_login', 'is_superuser')

    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('employee_id', 'name', 'is_first_login')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(SignupRequest)
