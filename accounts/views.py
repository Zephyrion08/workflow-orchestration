from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.http import require_POST
from .forms import SignupRequestForm, UserProfileForm
from .models import SignupRequest, CustomUser
from workflow.models import Task


@login_required
def home(request):
    user = request.user
    group = user.groups.first()  # Assumes one group per user

    if user.is_superuser or (group and group.name == 'Manager'):
        # Admins and Managers see all 'todo' or 'in_progress' tasks
        pending_tasks = Task.objects.filter(status__in=['todo', 'in_progress'])
    else:
        # Members see only their own 'todo' or 'in_progress' tasks
        pending_tasks = Task.objects.filter(status__in=['todo', 'in_progress'], assigned_to=user)

    return render(request, 'accounts/home.html', {
        'pending_tasks_count': pending_tasks.count()
    })

def signup_request_view(request):
    if request.method == 'POST':
        form = SignupRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Signup request sent! Please wait for admin approval.")
            return redirect('signup_request')
        else:
            messages.error(request, "There was an error with your submission. Please check the form below.")
    else:
        form = SignupRequestForm()
    return render(request, 'accounts/signup_request.html', {'form': form})


# Check if user is admin
def is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(is_admin)
def pending_requests_view(request):
    signup_requests = SignupRequest.objects.all().order_by('created_at')
    return render(request, 'accounts/pending_requests.html', {'requests': signup_requests})


@login_required
@user_passes_test(is_admin)
def create_user_from_request(request, request_id):
    signup_req = get_object_or_404(SignupRequest, id=request_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'Member')  # default Member if not selected

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'accounts/create_user.html', {'signup_req': signup_req})
        elif not password or len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'accounts/create_user.html', {'signup_req': signup_req})
        else:
            user = CustomUser.objects.create(
                username=username,
                password=make_password(password),
                name=signup_req.name,
                employee_id=signup_req.employee_id,
                is_first_login=True
            )
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            user.save()

            signup_req.delete()
            messages.success(request, f"User {username} created with role {role}.")
            return redirect('pending_requests')

    return render(request, 'accounts/create_user.html', {'signup_req': signup_req})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_first_login:
                return redirect('change_password')
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'accounts/login.html')


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def change_password_view(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            user = request.user
            user.set_password(new_password)
            user.is_first_login = False
            user.save()
            update_session_auth_hash(request, user)  # keeps session valid
            messages.success(request, "Password changed successfully.")
            return redirect('profile')

    return render(request, 'accounts/change_password.html')


@login_required
def profile_view(request):
    user = request.user
    return render(request, 'accounts/profile.html', {'user': user})


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


def is_admin_or_manager(user):
    return user.is_superuser or user.groups.filter(name='Manager').exists()

@login_required
@user_passes_test(is_admin_or_manager)
def user_list(request):
    users = CustomUser.objects.filter(is_superuser=False)
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_signup_request(request, request_id):
    signup_request = get_object_or_404(SignupRequest, id=request_id)
    signup_request.delete()
    messages.success(request, "Signup request deleted successfully.")
    return redirect('pending_requests')