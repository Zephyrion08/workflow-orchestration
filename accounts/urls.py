from django.urls import path
from .views import signup_request_view, pending_requests_view, create_user_from_request, login_view, logout_view, change_password_view, home,profile_view, profile_edit_view, user_list,delete_signup_request

urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup_request_view, name='signup_request'),
    path('pending-requests/', pending_requests_view, name='pending_requests'),
    path('create-user/<int:request_id>/', create_user_from_request, 
    name='create_user_from_request'),
     path('delete-signup-request/<int:request_id>/', delete_signup_request, name='delete_signup_request'),
]
urlpatterns += [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('change-password/', change_password_view, name='change_password'),
     path('profile/', profile_view, name='profile'),
      path('profile/edit/', profile_edit_view, name='profile_edit'),
      path('users/', user_list, name='user_list'),

]