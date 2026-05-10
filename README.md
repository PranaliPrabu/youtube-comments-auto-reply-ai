🤖 YouTube Comment AI Replier

An AI-powered Streamlit application that automatically fetches YouTube comments, analyzes sentiment and tone, detects language, and generates intelligent multilingual replies using multiple AI models including GPT-4, GPT-3.5, Gemini, and LLaMA.

🚀 Features
🎥 Fetch YouTube video metadata
💬 Extract YouTube comments automatically
🌍 Multilingual language detection & translation
😊 Sentiment Analysis (Positive / Negative / Neutral)
🎭 Tone Detection (Praise, Humor, Criticism, Request, etc.)
🤖 AI-generated replies using:
  GPT-4
  GPT-3.5
  Gemini
  LLaMA
📊 Analytics dashboard with visualizations
📥 Download generated replies as CSV
🎵 Extract movie and singer details from video description

🛠️ Technologies Used
  Python
  Streamlit
  OpenAI API
  Google Gemini API
  Pandas
  Seaborn
  Matplotlib
  TextBlob
  LangDetect
  Deep Translator
  yt-dlp
  YouTube Comment Downloader

📂 Project Workflow
User enters a YouTube video URL
Application fetches:
  Video details
  Comments
Detects:
  Language
  Tone
  Sentiment
Generates AI-based replies
Displays analytics and downloadable results

▶️ Installation
Clone Repository
git clone <your-github-repo-link>
cd <project-folder>

Install Dependencies
pip install -r requirements.txt

🔑 Environment Variables
Create a .env file and add:
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_gemini_api_key

▶️ Run Application
streamlit run app.py

📊 Output
The application:
  Fetches YouTube comments
  Detects language and sentiment
  Generates contextual AI replies
  Displays analytics dashboards
  Allows CSV export of generated replies

📌 Future Enhancements
  Instagram Reels comment support
  Real-time comment monitoring
  Advanced emotion detection
  AI reply customization
  Deployment using Streamlit Cloud

👩‍💻 Author
Pranali P
AIML Engineer | Machine Learning & Generative AI Enthusiast
