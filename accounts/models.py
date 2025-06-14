from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)  # new
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # new
    is_first_login = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} "


class SignupRequest(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.employee_id})"
