from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from candidates.models import CandidateProfile
from django.contrib.auth.views import LoginView
from .forms import InterviewerSignUpForm
from django.urls import reverse_lazy
from .utils import generate_interview_questions, schedule_meeting, transcribe_audio
from .models import InterviewerProfile
from django.contrib.auth import logout, login
from django.contrib import messages
from django.http import HttpResponseRedirect
import os


class InterviewerLoginView(LoginView):
    template_name = 'interviewers/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('interviewer_dashboard')
    
    def form_valid(self, form):
        """Handle successful login"""
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle failed login"""
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        """Handle already authenticated users"""
        if request.user.is_authenticated:
            return redirect('interviewer_dashboard')
        return super().dispatch(request, *args, **kwargs)


def interviewer_signup(request):
    if request.user.is_authenticated:
        return redirect('interviewer_dashboard')
        
    if request.method == 'POST':
        form = InterviewerSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Create an InterviewerProfile with Zoom credentials
                InterviewerProfile.objects.create(
                    user=user,
                    zoom_account_id=form.cleaned_data.get('zoom_account_id'),
                    zoom_client_id=form.cleaned_data.get('zoom_client_id'),
                    zoom_client_secret=form.cleaned_data.get('zoom_client_secret')
                )
                login(request, user)
                messages.success(request, f'Welcome {user.username}! Your interviewer account has been created successfully.')
                return redirect('interviewer_dashboard')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InterviewerSignUpForm()
    return render(request, 'interviewers/signup.html', {'form': form})

@login_required(login_url='interviewer_login')
def interviewer_dashboard(request):
    """Interviewer dashboard view"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access your dashboard.')
        return redirect('interviewer_login')

    # Add this check to verify session is maintained
    if not request.session.session_key:
        request.session.create()
    
    try:
        resumes = CandidateProfile.objects.exclude(resume__isnull=True).exclude(resume__exact='')
        questions_dict = {}  # Store questions per candidate ID
        meeting_link = None
        evaluation_reports = {}

        interviewer_profile, created = InterviewerProfile.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            try:
                resume_id = int(request.POST.get('resume_id'))
                candidate = CandidateProfile.objects.get(id=resume_id)

                if 'generate_questions' in request.POST:
                    try:
                        # Get the full path to the resume file
                        if candidate.resume and hasattr(candidate.resume, 'path'):
                            resume_path = candidate.resume.path
                        elif candidate.resume:
                            # Fallback: construct path from MEDIA_ROOT and resume name
                            from django.conf import settings
                            resume_path = os.path.join(settings.MEDIA_ROOT, str(candidate.resume))
                        else:
                            questions_dict[resume_id] = "Error: No resume found for this candidate"
                            messages.error(request, 'No resume found for this candidate.')
                            return render(request, 'interviewers/dashboard.html', {
                                'resumes': resumes,
                                'questions_dict': questions_dict,
                                'meeting_link': meeting_link,
                                'evaluation_reports': evaluation_reports
                            })
                        
                        # Generate questions for this specific candidate
                        generated_questions = generate_interview_questions(resume_path)
                        # Format questions for better display
                        formatted_questions = format_questions_for_display(generated_questions)
                        questions_dict[resume_id] = formatted_questions
                        messages.success(request, 'AI questions generated successfully!')
                    except Exception as e:
                        questions_dict[resume_id] = f"Error generating questions: {str(e)}"
                        messages.error(request, f'Error generating questions: {str(e)}')

                elif 'schedule_meeting' in request.POST:
                    try:
                        start_time = request.POST.get('start_time')
                        
                        # Verify we have all required credentials
                        if not all([interviewer_profile.zoom_account_id, 
                                interviewer_profile.zoom_client_id, 
                                interviewer_profile.zoom_client_secret]):
                            messages.error(request, 'Please configure your Zoom credentials in your profile before scheduling meetings.')
                            return redirect('interviewer_dashboard')
                            
                        # Fix: Pass the correct parameters to schedule_meeting
                        new_meeting_link = schedule_meeting(
                            topic=f"Interview with {candidate.user.username}",
                            start_time=start_time,
                            zoom_account_id=interviewer_profile.zoom_account_id,
                            zoom_client_id=interviewer_profile.zoom_client_id,  # Fixed: was zoom_client_secret
                            zoom_client_secret=interviewer_profile.zoom_client_secret
                        )

                        if new_meeting_link:
                            candidate.meeting_link = new_meeting_link
                            candidate.meeting_time = start_time
                            candidate.save()
                            meeting_link = new_meeting_link
                            messages.success(request, f'🎉 Interview successfully scheduled with {candidate.user.username}!')
                        else:
                            messages.error(request, 'Failed to schedule meeting. Please check your Zoom configuration.')
                    except Exception as e:
                        messages.error(request, f'Error scheduling meeting: {str(e)}')

                elif 'process_audio' in request.POST:
                    try:
                        audio_file = request.FILES.get('audio_file')
                        if not audio_file:
                            messages.error(request, 'Please select an audio file to upload.')
                            return redirect('interviewer_dashboard')
                        
                        # Handle file upload and processing
                        import tempfile
                        import os
                        
                        # Create temporary file
                        temp_dir = tempfile.mkdtemp()
                        temp_file_path = os.path.join(temp_dir, audio_file.name)
                        
                        with open(temp_file_path, 'wb+') as destination:
                            for chunk in audio_file.chunks():
                                destination.write(chunk)
                        
                        # Process the audio file
                        analysis_result = transcribe_audio(temp_file_path)
                        
                        # Store the result for display
                        evaluation_reports[resume_id] = analysis_result
                        
                        # Clean up
                        os.remove(temp_file_path)
                        os.rmdir(temp_dir)
                        
                        messages.success(request, 'Interview audio analyzed successfully!')
                        
                    except Exception as e:
                        messages.error(request, f'Error processing audio: {str(e)}')

            except (ValueError, CandidateProfile.DoesNotExist) as e:
                messages.error(request, f'Invalid candidate selection: {str(e)}')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')

        # Add questions to each resume object for template access
        for resume in resumes:
            resume.questions = questions_dict.get(resume.id, None)

        return render(request, 'interviewers/dashboard.html', {
            'resumes': resumes,
            'questions_dict': questions_dict,
            'meeting_link': meeting_link,
            'evaluation_reports': evaluation_reports
        })
    except Exception as e:
        messages.error(request, f'Dashboard error: {str(e)}')
        return redirect('interviewer_login')

def interviewer_logout(request):
    """Handle interviewer logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def format_questions_for_display(questions_text):
    """Format AI-generated questions for beautiful display while preserving categories"""
    if not questions_text or "Error" in questions_text:
        return questions_text
    
    lines = questions_text.split('\n')
    formatted_sections = []
    current_section = None
    current_subsection = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for main section headers (## format)
        if line.startswith('## '):
            section_title = line[3:].strip()
            current_section = {
                'type': 'header',
                'title': section_title,
                'subsections': []
            }
            formatted_sections.append(current_section)
            current_subsection = None
            
        # Check for difficulty level subsections (### format)
        elif line.startswith('### '):
            subsection_title = line[4:].strip()
            current_subsection = {
                'type': 'subsection',
                'title': subsection_title,
                'questions': []
            }
            if current_section:
                current_section['subsections'].append(current_subsection)
            
        # Check if it's a numbered question (1., 2., 3., etc.)
        elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ', '10. ')):
            # Extract question text (remove the number)
            question_text = line[3:].strip()  # Remove "1. " or similar
            
            if len(question_text) > 10:  # Only meaningful questions
                question_item = {
                    'type': 'question',
                    'text': question_text
                }
                
                # Add to current subsection
                if current_subsection:
                    current_subsection['questions'].append(question_item)
                elif current_section:
                    # Create a default subsection if none exists
                    if not current_section['subsections']:
                        current_section['subsections'].append({
                            'type': 'subsection', 
                            'title': 'Questions',
                            'questions': []
                        })
                    current_section['subsections'][0]['questions'].append(question_item)
        
        # Handle any other content lines
        elif len(line) > 10 and not line.startswith(('#', '*', '-')):
            # This could be a question without proper numbering
            if any(word in line.lower() for word in ['what', 'how', 'why', 'describe', 'explain', 'discuss', 'tell', 'which', 'when', 'where']):
                question_item = {
                    'type': 'question',
                    'text': line
                }
                
                if current_subsection:
                    current_subsection['questions'].append(question_item)
                elif current_section:
                    if not current_section['subsections']:
                        current_section['subsections'].append({
                            'type': 'subsection', 
                            'title': 'Questions',
                            'questions': []
                        })
                    current_section['subsections'][0]['questions'].append(question_item)
    
    # If no structured sections were found, create a fallback structure
    if not formatted_sections:
        # Parse as simple list and create default structure
        questions = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                # Clean up question formatting
                clean_question = line
                # Remove common prefixes
                prefixes_to_remove = ['Q.', 'Q1.', 'Q2.', 'Q3.', 'Q4.', 'Q5.', 'Q6.', 'Q7.', 'Q8.', 'Q9.', 'Q10.', 
                                    '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', 
                                    '11.', '12.', '13.', '14.', '15.', '16.', '17.', '18.', '19.', '20.',
                                    '-', '•', '*']
                
                for prefix in prefixes_to_remove:
                    if clean_question.startswith(prefix):
                        clean_question = clean_question[len(prefix):].strip()
                        break
                
                # Only add if it's a meaningful question
                if (len(clean_question) > 15 and 
                    (any(word in clean_question.lower() for word in ['what', 'how', 'why', 'describe', 'explain', 'discuss', 'tell', 'which', 'when', 'where']) or 
                     clean_question.endswith('?'))):
                    questions.append({
                        'type': 'question',
                        'text': clean_question
                    })
        
        if questions:
            formatted_sections = [{
                'type': 'header',
                'title': 'Interview Questions',
                'subsections': [{
                    'type': 'subsection',
                    'title': 'Generated Questions',
                    'questions': questions
                }]
            }]
    
    return formatted_sections

