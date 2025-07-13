from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ResumeUploadForm, CandidateSignUpForm
from .models import CandidateProfile
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import logout, login
from django.contrib import messages


@login_required(login_url='/candidate/login/')
def candidate_dashboard(request):
    try:
        candidate_profile, created = CandidateProfile.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            form = ResumeUploadForm(request.POST, request.FILES, instance=candidate_profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Resume uploaded successfully!')
                return redirect('candidate_dashboard')
            else:
                messages.error(request, 'Error uploading resume. Please try again.')
        else:
            form = ResumeUploadForm(instance=candidate_profile)

        return render(request, 'candidates/dashboard.html', {
            'form': form,
            'candidate_profile': candidate_profile,
            'meeting_link': candidate_profile.meeting_link,
            'meeting_time': candidate_profile.meeting_time
        })
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('candidate_login')


def candidate_logout(request):
    """Handle candidate logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


class CandidateLoginView(LoginView):
    template_name = 'candidates/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('candidate_dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


def candidate_signup(request):
    if request.user.is_authenticated:
        return redirect('candidate_dashboard')
        
    if request.method == 'POST':
        form = CandidateSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Create a CandidateProfile for the new user
                CandidateProfile.objects.create(user=user)
                # Log the user in after sign-up
                login(request, user)
                messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
                return redirect('candidate_dashboard')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CandidateSignUpForm()
    return render(request, 'candidates/signup.html', {'form': form})
