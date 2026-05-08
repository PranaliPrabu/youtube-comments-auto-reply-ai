import streamlit as st
from streamlit_lottie import st_lottie
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import emoji
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import requests
import openai
import google.generativeai as genai
from dotenv import load_dotenv
from youtube_comment_downloader import YoutubeCommentDownloader
from yt_dlp import YoutubeDL
import random
from textblob import TextBlob

# --- Load Keys ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Constants ---
allowed_languages = ["en", "hi", "kn", "te", "ta", "ko", "ja"]
fallback_responses = [
    "Appreciate you sharing this!",
    "Thanks for chiming in!",
    "Grateful for your comment! 🙏",
    "Good to hear from you!",
    "Thanks for dropping your thoughts!",
    "That's interesting – thanks for the input!",
]

# --- Language Detection ---
def safe_detect_language(text):
    try:
        if not text or len(text.strip()) < 3:
            return "en"
        if all(char in emoji.EMOJI_DATA for char in text.strip()):
            return "emoji"

        transliterated_keywords = {
            "hi": ["kon", "kya", "kaise", "video", "dekh", "pyar", "mera", "bhot", "acha", "dil"],
            "ta": ["ungal", "pudhu", "nalla", "enna", "romba"],
            "te": ["chala", "video", "manchi", "meeru"],
            "kn": ["hesaru", "ondhu", "nodi"]
        }
        text_lower = text.lower()
        for lang, keywords in transliterated_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return lang

        lang = detect(text)
        return lang if lang in allowed_languages else "en"
    except LangDetectException:
        return "en"

# --- Tone Detection ---
def detect_tone(text):
    if not text:
        return "Neutral"
    text_lower = text.lower()
    if all(char in emoji.EMOJI_DATA for char in text):
        return "Praise"
    if re.search(r"\b\d{1,2}:\d{2}\b", text_lower):
        return "Timestamp"
    if re.search(r"\b(19|20)\d{2}\b", text_lower):
        return "Year"
    if any(word in text_lower for word in ["lol", "lmao", "rofl", "haha"]):
        return "Humor"

    patterns = {
        "Praise": ["love", "beautiful", "amazing", "nice", "great", "wonderful", "awesome", "superb"],
        "Criticism": ["bad", "worst", "hate", "cringe", "trash", "dislike"],
        "Support": ["respect", "keep it up", "well done", "good job"],
        "Confusion": ["what", "why", "confused"],
        "Request": ["please", "can you", "would you", "could you"]
    }
    for tone, keywords in patterns.items():
        if any(word in text_lower for word in keywords):
            return tone
    return "Neutral"

# --- Sentiment Detection ---
def detect_sentiment(text):
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.2:
            return "Positive"
        elif polarity < -0.2:
            return "Negative"
        return "Neutral"
    except:
        return "Neutral"

# --- Translation ---
def translate_to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text

def translate_back(reply, lang):
    try:
        if lang != "en" and lang in allowed_languages:
            return GoogleTranslator(source="en", target=lang).translate(reply)
        return reply
    except:
        return reply

def refine_reply(reply):
    if reply.strip().lower() in ["thanks for your feedback!", "thanks for your feedback! 👍"]:
        return random.choice(fallback_responses)
    return reply

# --- AI Reply Pipeline ---
def generate_reply(comment, lang="en", movie="", singer=""):
    comment_lower = comment.lower()

    movie_queries = ["which movie", "movie name", "film name", "name of the movie"]
    singer_queries = ["singer", "sung by", "singer name", "who sang"]

    if any(p in comment_lower for p in movie_queries):
        reply = f"This is from the movie '{movie}'." if movie and movie != "Unknown" else "Sorry, the movie name isn't available."
        return translate_back(reply, lang), "Context (Movie)"

    if any(p in comment_lower for p in singer_queries):
        reply = f"The singer is {singer}." if singer and singer != "Unknown" else "Sorry, I couldn't find the singer's name."
        return translate_back(reply, lang), "Context (Singer)"

    try:
        reply = gpt4_reply(comment)
        return translate_back(refine_reply(reply), lang), "GPT-4"
    except:
        try:
            reply = gpt35_reply(comment)
            return translate_back(refine_reply(reply), lang), "GPT-3.5"
        except:
            try:
                reply = gemini_reply(comment)
                return translate_back(refine_reply(reply), lang), "Gemini"
            except:
                try:
                    reply = llama_reply(comment)
                    return translate_back(refine_reply(reply), lang), "LLaMA"
                except:
                    return translate_back(random.choice(fallback_responses), lang), "Fallback"

def gpt4_reply(comment):
    prompt = f"You're a witty and helpful AI assistant. Reply to this comment naturally:\nComment: {comment}\nReply:"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def gpt35_reply(comment):
    prompt = f"You're a witty and helpful AI assistant. Reply to this comment naturally:\nComment: {comment}\nReply:"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def gemini_reply(comment):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Reply to this YouTube comment: {comment}")
    return response.text.strip()

def llama_reply(comment):
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3",
        "prompt": f"Reply to this YouTube comment: {comment}"
    }, timeout=20)
    return r.json().get("response", random.choice(fallback_responses)).strip()

# --- Video Info + Metadata ---
def extract_movie_and_singer(description):
    movie, singer = "", ""
    m = re.search(r"(?:Movie|Film)[\s:]([^\n,;])", description, re.IGNORECASE)
    s = re.search(r"(?:Singer|Vocals|Sung by)[\s:]([^\n,;])", description, re.IGNORECASE)
    movie = m.group(1).strip() if m else ""
    singer = s.group(1).strip() if s else ""

    if not movie or not singer:
        try:
            text = gpt35_reply(f"Extract the movie and singer name from: {description}")
            m = re.search(r"Movie[:\-]?\s*(.*?)[;\n]", text)
            s = re.search(r"Singer[:\-]?\s*(.*?)[;\n]", text)
            movie = m.group(1).strip() if m else movie or "Unknown"
            singer = s.group(1).strip() if s else singer or "Unknown"
        except:
            pass

    return movie or "Unknown", singer or "Unknown"

def get_video_info(url):
    try:
        with YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title", "Untitled")
        description = info.get("description", "")
        movie, singer = extract_movie_and_singer(description)
        genre = info.get("categories", ["Unknown"])[0]
        summary = description[:300] + "..." if len(description) > 300 else description
        children_keywords = ["kids", "nursery", "rhymes", "baby", "child", "cartoon"]
        children = "Yes" if any(k in description.lower() for k in children_keywords) else "No"
        return title, summary, genre, children, movie, singer
    except Exception as e:
        return "Unknown", f"Error: {e}", "Unknown", "Unknown", "Unknown", "Unknown"

# --- Streamlit App ---
def main():
    st.set_page_config(page_title="YouTube Comment AI", layout="wide", page_icon="🤖")
    st.title("🤖 YouTube Comment AI Replier")

    url = st.text_input("📺 YouTube Video URL")
    count = st.slider("Number of comments to fetch", 5, 50, 10)

    if st.button("✨ Generate Replies") and url:
        title, summary, genre, children, movie, singer = get_video_info(url)
        st.subheader("🎥 Video Info")
        st.markdown(f"*Title:* {title}")
        st.markdown(f"*Summary:* {summary}")
        st.markdown(f"*Genre:* {genre}")
        st.markdown(f"*Children Friendly:* {children}")
        st.markdown(f"*Movie:* {movie}")
        st.markdown(f"*Singer:* {singer}")

        downloader = YoutubeCommentDownloader()
        comments = [c["text"] for _, c in zip(range(count), downloader.get_comments_from_url(url))]

        data = []
        for comment in comments:
            lang = safe_detect_language(comment)
            translated = translate_to_english(comment) if lang not in ["en", "emoji"] else comment
            tone = detect_tone(translated)
            sentiment = detect_sentiment(translated)
            reply, model_used = generate_reply(translated, lang=lang, movie=movie, singer=singer)
            data.append({
                "Original Comment": comment,
                "Reply": reply,
                "Language": lang,
                "Tone": tone,
                "Sentiment": sentiment,
                "AI Agent": model_used
            })

        df = pd.DataFrame(data)
        st.subheader("💬 AI Replies")
        st.dataframe(df)
        st.download_button("📥 Download CSV", df.to_csv(index=False), "replies.csv")

        st.subheader("📊 Analytics")
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            sns.countplot(data=df, x="Sentiment", palette="viridis", ax=ax)
            ax.set_title("Sentiment Distribution")
            st.pyplot(fig)
        with col2:
            fig, ax = plt.subplots()
            sns.countplot(data=df, x="Tone", palette="coolwarm", ax=ax)
            ax.set_title("Tone Analysis")
            st.pyplot(fig)

if __name__ == "__main__":
    main()