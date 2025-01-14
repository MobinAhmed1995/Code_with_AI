import os
import dotenv
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from google.generativeai import GenerativeModel
from fpdf import FPDF
from datetime import datetime
from gtts import gTTS
import PyPDF2

# Load environment variables
dotenv.load_dotenv()

# Initialize Gemini
genai.configure(api_key="Your_API-KEY")
model = GenerativeModel('gemini-1.5-pro')

class YouTubeTranscriptLoader:
    @staticmethod
    def get_video_id(url):
        # Extract video ID from YouTube URL
        if 'youtu.be' in url:
            return url.split('/')[-1]
        elif 'youtube.com' in url:
            return url.split('v=')[1].split('&')[0]
        return url

    def load_transcript(self, url):
        video_id = self.get_video_id(url)
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return ' '.join([item['text'] for item in transcript_list])
        except Exception as e:
            print(f"Error getting transcript: {str(e)}")
            return None

class AnalysisAgent:
    def __init__(self):
        self.model = model

    def generate_summary(self, transcript):
        prompt = f"Summarize this transcript concisely: {transcript}"
        response = self.model.generate_content(prompt)
        return response.text

    def create_bullet_points(self, summary):
        prompt = f"""Based on this summary, create 50 detailed bullet points that capture key insights:
        Summary: {summary}
        Please format as a list of 50 bullet points."""
        
        response = self.model.generate_content(prompt)
        return response.text

class PDFAgent:
    def save_to_pdf(self, summary, bullet_points, youtube_link):
        pdf = FPDF()
        pdf.add_page()
        
        # Add title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'YouTube Video Analysis', ln=True, align='C')
        
        # Add timestamp and link
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True)
        pdf.cell(0, 10, f'Video Link: {youtube_link}', ln=True)
        
        # Add summary
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Summary:', ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 10, summary)
        
        # Add bullet points
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Detailed Analysis Points:', ln=True)
        pdf.set_font('Arial', '', 10)
        
        for point in bullet_points.split('\n'):
            if point.strip():
                pdf.multi_cell(0, 10, point)
        
        # Save PDF
        filename = f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf.output(filename)
        return filename

class AudioAgent:
    def __init__(self):
        self.output_dir = "audio_outputs"
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def extract_text_from_pdf(self, pdf_path):
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def create_audio(self, pdf_path):
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"{self.output_dir}/analysis_audio_{timestamp}.mp3"
            
            # Convert text to speech
            print("Converting text to speech...")
            tts = gTTS(text=text, lang='en')
            tts.save(audio_filename)
            print(f"Audio file saved as: {audio_filename}")
            
            return audio_filename
            
        except Exception as e:
            print(f"Error creating audio: {str(e)}")
            return None

def analyze_youtube_video(video_url):
    try:
        # Get transcript
        loader = YouTubeTranscriptLoader()
        transcript = loader.load_transcript(video_url)
        
        if not transcript:
            raise Exception("Could not load transcript")

        # Initialize agents
        analysis_agent = AnalysisAgent()
        pdf_agent = PDFAgent()
        audio_agent = AudioAgent()

        # Generate summary
        summary = analysis_agent.generate_summary(transcript)
        print("Summary generated successfully")

        # Generate bullet points
        bullet_points = analysis_agent.create_bullet_points(summary)
        print("Bullet points generated successfully")

        # Save to PDF
        pdf_file = pdf_agent.save_to_pdf(summary, bullet_points, video_url)
        print(f"PDF saved as: {pdf_file}")

        # Create audio version
        audio_file = audio_agent.create_audio(pdf_file)
        print(f"Audio version saved as: {audio_file}")

        return {
            'summary': summary,
            'bullet_points': bullet_points,
            'pdf_file': pdf_file,
            'audio_file': audio_file
        }

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    video_url = input("Enter YouTube video URL: ")
    results = analyze_youtube_video(video_url)
    
    if results:
        print("\nSummary:")
        print(results['summary'])
        print("\nBullet Points:")
        print(results['bullet_points'])
        print(f"\nPDF Report: {results['pdf_file']}")
        print(f"Audio Report: {results['audio_file']}")
