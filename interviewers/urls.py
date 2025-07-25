from django.urls import path
from .views import InterviewerLoginView, interviewer_dashboard, interviewer_signup, interviewer_logout

urlpatterns = [
    path('login/', InterviewerLoginView.as_view(), name='interviewer_login'),
    path('signup/', interviewer_signup, name='interviewer_signup'),
    path('dashboard/', interviewer_dashboard, name='interviewer_dashboard'),
    path('logout/', interviewer_logout, name='interviewer_logout'),
]
