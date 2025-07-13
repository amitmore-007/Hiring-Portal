# interviewers/utils.py
import os
from groq import Groq
import pdfplumber
import requests

def extract_text_from_pdf(pdf_file_path):
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""  # Extract text from each page
            return text.strip()
    except Exception as e:
        return f"Error reading PDF file: {e}"

def generate_interview_questions(pdf_file_path):
    try:
        # Import Django settings to get GROQ_API_KEY
        from django.conf import settings
        
        # Initialize the Groq client with API key from settings
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        if not settings.GROQ_API_KEY:
            return "Error: GROQ_API_KEY not found in settings. Please check your .env file and ensure python-decouple is installed."

        # Check if file exists
        if not os.path.exists(pdf_file_path):
            return f"Error: Resume file not found at {pdf_file_path}"

        # Extract text from the PDF resume
        resume_content = extract_text_from_pdf(pdf_file_path)
        if resume_content.startswith("Error"):
            return resume_content  # Return error message if PDF reading fails
    except Exception as e:
        return f"Error initializing question generation: {e}"

    # Enhanced template for generating consistently formatted interview questions
    template = (
        "You are an experienced interviewer creating well-structured interview questions. "
        "Based on the resume content: {resume_content}, generate questions in the following EXACT format:\n\n"

        "## General Skills Questions\n\n"
        "### Easy Questions\n"
        "1. What motivated you to pursue a career in your field?\n"
        "2. How do you stay updated with industry trends?\n"
        "3. Describe your approach to learning new technologies.\n\n"

        "### Medium Questions\n"
        "1. Tell me about a time you had to work under pressure.\n"
        "2. How do you prioritize tasks when managing multiple projects?\n"
        "3. Describe a situation where you had to adapt to change.\n\n"

        "### Hard Questions\n"
        "1. How would you handle a conflict with a team member?\n"
        "2. Describe a time you had to make a difficult decision with limited information.\n"
        "3. How do you approach problem-solving in complex situations?\n\n"

        "### Extreme Hard Questions\n"
        "1. How would you lead a team through a major organizational change?\n"
        "2. Describe your strategy for handling competing priorities from different stakeholders.\n"
        "3. How would you approach a situation where you disagreed with your manager's decision?\n\n"

        "## Technical Questions\n\n"
        "### Easy Questions\n"
        "1. [Generate 3 basic technical questions based on resume skills]\n\n"

        "### Medium Questions\n"
        "1. [Generate 3 practical technical questions]\n\n"

        "### Hard Questions\n"
        "1. [Generate 3 advanced technical questions]\n\n"

        "### Extreme Hard Questions\n"
        "1. [Generate 3 expert-level technical questions]\n\n"

        "## Project Questions\n\n"
        "### Easy Questions\n"
        "1. [Generate 3 basic project questions based on resume projects]\n\n"

        "### Medium Questions\n"
        "1. [Generate 3 detailed project questions]\n\n"

        "### Hard Questions\n"
        "1. [Generate 3 challenging project questions]\n\n"

        "### Extreme Hard Questions\n"
        "1. [Generate 3 strategic project questions]\n\n"

        "## Behavioral Questions\n\n"
        "### Easy Questions\n"
        "1. [Generate 3 basic behavioral questions]\n\n"

        "### Medium Questions\n"
        "1. [Generate 3 experience-based behavioral questions]\n\n"

        "### Hard Questions\n"
        "1. [Generate 3 challenging behavioral questions]\n\n"

        "### Extreme Hard Questions\n"
        "1. [Generate 3 leadership/ethical behavioral questions]\n\n"

        "IMPORTANT FORMATTING RULES:\n"
        "- Use exactly ## for main sections (General Skills Questions, Technical Questions, etc.)\n"
        "- Use exactly ### for difficulty levels (Easy Questions, Medium Questions, etc.)\n"
        "- Number all questions as 1., 2., 3. within each difficulty level\n"
        "- Make questions specific to the candidate's background and skills\n"
        "- Ensure each question is meaningful and interview-appropriate\n"
        "- Replace bracketed placeholders with actual questions relevant to the resume\n"
        "- Keep consistent formatting throughout\n"
    )

    # Format the template with the resume content
    prompt = template.format(resume_content=resume_content)

    try:
        # Send request to the Groq API using the formatted prompt
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Groq model choice
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Lower temperature for more focused questions
            max_tokens=4096,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Collect streaming response progressively
        response_chunks = []
        for message in completion:
            chunk = message.choices[0].delta.content or ""
            response_chunks.append(chunk)  # Append each chunk to the list

        # Join all chunks into a complete response
        full_response = "".join(response_chunks)
        return full_response.strip()

    except Exception as e:
        return f"Error generating interview questions: {e}"
    




def schedule_meeting(topic, start_time, zoom_account_id, zoom_client_id, zoom_client_secret):
    # Get OAuth Token
    def get_zoom_access_token():
        url = "https://zoom.us/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "account_credentials",
            "account_id": zoom_account_id
        }
        auth = (zoom_client_id, zoom_client_secret)

        response = requests.post(url, headers=headers, data=payload, auth=auth)

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print("Error getting access token:", response.text)
            return None

    try:
        # Validate input parameters
        if not all([topic, start_time, zoom_account_id, zoom_client_id, zoom_client_secret]):
            print("Error: Missing required Zoom credentials or meeting details")
            return None

        # Schedule the meeting
        access_token = get_zoom_access_token()
        if not access_token:
            return None

        url = "https://api.zoom.us/v2/users/me/meetings"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "topic": topic,
            "type": 2,
            "start_time": start_time,
            "duration": 30,  # 30-minute meeting
            "timezone": "UTC",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "mute_upon_entry": True,
                "waiting_room": False
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            return response.json()["join_url"]
        else:
            print("Error scheduling meeting:", response.text)
            return None
            
    except Exception as e:
        print(f"Unexpected error in schedule_meeting: {e}")
        return None
    




def transcribe_audio(audio_file_path):
    """Transcribes an audio file and analyzes the interview using LLaMA."""
    
    # Import Django settings to get GROQ_API_KEY
    from django.conf import settings
    
    # Initialize Groq Client
    client = Groq(api_key=settings.GROQ_API_KEY)

    # Step 1: Transcribe the Audio
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="distil-whisper-large-v3-en",
                file=audio_file,
                response_format="text"
            ).strip()
    except Exception as e:
        return f"Error transcribing audio: {e}"

    # Step 2: Analyze the Interview using LLaMA
    llama_prompt = f"""
You are an AI-powered interview evaluator assisting the interviewer in assessing a candidate's responses.  
The following is an automatically transcribed interview transcript, with raw and unprocessed text.  
Your task is to extract key insights, assess the quality of responses, and provide a structured evaluation based on the given criteria.
and also provide asked important question and candidate's answer. 

**Interview Transcript (raw):**  
{transcription}  

**Evaluation Criteria:**  
1. **Confidence & Delivery:** Assess whether the candidate speaks with confidence, assurance, and clarity. Explain why you believe they were (or were not) confident based on tone, hesitation, or assertiveness.  
2. **Relevance & Accuracy:** Evaluate whether the candidate’s responses align with the question. Provide reasons if their response was off-topic, partially correct, or completely accurate.  
3. **Coherence & Logical Flow:** Determine if the candidate’s thoughts are structured and make sense. Justify this based on their ability to present ideas sequentially and logically.  
4. **Overall Impression:** Provide a qualitative summary of the candidate’s performance, supported by specific examples from their responses.  
5. **Key Observations:** Highlight any notable strengths or weaknesses, explaining why they stood out.  

Please format your response in a detailed manner. Also, this is interviewer-tailored, so do not provide recommendations for the candidate.  

"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": llama_prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating interview analysis: {e}"
