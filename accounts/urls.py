from django.urls import path
from .views import signup_request_view, pending_requests_view, create_user_from_request, login_view, logout_view, change_password_view, home

urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup_request_view, name='signup_request'),
    path('pending-requests/', pending_requests_view, name='pending_requests'),
    path('create-user/<int:request_id>/', create_user_from_request, name='create_user_from_request'),
    # we'll add auth views next (login/logout/dashboard/change-password)
]
urlpatterns += [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('change-password/', change_password_view, name='change_password'),
]