from django.urls import path
from .views import CandidateLoginView, candidate_dashboard, candidate_signup

urlpatterns = [
    path('login/', CandidateLoginView.as_view(), name='candidate_login'),
    path('signup/', candidate_signup, name='candidate_signup'),
    path('dashboard/', candidate_dashboard, name='candidate_dashboard'),
]