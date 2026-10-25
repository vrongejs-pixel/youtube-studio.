import datetime as dt
import json
import os
import google.generativeai as genai
import pandas as pd
import requests
import streamlit as st

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="YouTube Viral Clone Studio", page_icon="🎥", layout="wide"
)

# --- ИСТОРИЯ ПРОЕКТОВ (JSON файл) ---
HISTORY_FILE = "projects_history.json"


def load_history():
  if os.path.exists(HISTORY_FILE):
    try:
      with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      return []
  return []


def save_history(history_list):
  with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history_list, f, ensure_ascii=False, indent=2)


# --- БОКОВАЯ ПАНЕЛЬ (НАСТРОЙКИ) ---
with st.sidebar:
  st.image("https://img.icons8.com/color/96/youtube-play.png", width=64)
  st.title("Settings / Настройки")

  # Переключатель языка интерфейса
  lang_choice = st.selectbox("Language / Язык", ["Русский 🇷🇺", "English 🇬🇧"])
  is_ru = lang_choice == "Русский 🇷🇺"

  st.divider()
  st.subheader(
      "🔑 API Keys" if not is_ru else "🔑 Ключи доступа (API Keys)"
  )

  gemini_key = st.text_input(
      "Gemini API Key",
      value=os.environ.get("GEMINI_API_KEY", ""),
      type="password",
  )
  yt_key = st.text_input(
      "YouTube Data API Key",
      value=os.environ.get("YT_API_KEY", ""),
      type="password",
  )

  st.divider()
  st.subheader("📂 История проектов" if is_ru else "📂 Projects History")
  history = load_history()

  if history:
    project_titles = [p.get("title", f"Проект {i}") for i, p in enumerate(history)]
    selected_proj_idx = st.selectbox(
        "Выберите прошлый проект" if is_ru else "Select past project",
        range(len(history)),
        format_func=lambda x: project_titles[x],
    )
  else:
    st.info("История пока пуста" if is_ru else "History is empty")


# --- ГЛАВНЫЙ ЭКРАН ---
if is_ru:
  st.title("🎥 YouTube Viral Clone Studio")
  st.markdown(
      "Вставьте ссылку на успешный YouTube-ролик — ИИ проведет разведку ниши,"
      " разберет секрет успеха и сгенерирует полный пакет для вашего клона"
      " (сценарий, голос, промпты для визуала и план монтажа для CapCut)."
  )
  url_input = st.text_input(
      "🔗 Ссылка на YouTube-видео",
      placeholder="https://www.youtube.com/watch?v=...",
  )
  run_btn = st.button("🚀 Проанализировать и создать клон", type="primary")
else:
  st.title("🎥 YouTube Viral Clone Studio")
  st.markdown(
      "Paste a successful YouTube video URL — AI will analyze the niche, break"
      " down the success factors, and generate a complete production package"
      " for your clone (script, voiceover, visual prompts, and CapCut plan)."
  )
  url_input = st.text_input(
      "🔗 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=..."
  )
  run_btn = st.button("🚀 Analyze & Create Clone", type="primary")


# Функция извлечения ID видео
def extract_video_id(url):
  if "youtu.be/" in url:
    return url.split("youtu.be/")[1].split("?")[0]
  elif "watch?v=" in url:
    return url.split("watch?v=")[1].split("&")[0]
  return None


# --- ЛОГИКА ОБРАБОТКИ ---
if run_btn:
  if not gemini_key:
    st.error(
        "Пожалуйста, введите Gemini API Key в боковой панели!"
        if is_ru
        else "Please enter Gemini API Key in the sidebar!"
    )
  elif not url_input:
    st.warning(
        "Введите ссылку на видео!" if is_ru else "Please enter a video URL!"
    )
  else:
    vid_id = extract_video_id(url_input)
    if not vid_id:
      st.error(
          "Неверная ссылка на YouTube!" if is_ru else "Invalid YouTube URL!"
      )
    else:
      with st.spinner(
          "🔄 ИИ собирает данные, анализирует конкурентов и генерирует"
          " пакет..."
          if is_ru
          else "🔄 AI is gathering data, analyzing competitors, and generating"
          " package..."
      ):
        try:
          genai.configure(api_key=gemini_key)
          # Использование актуальной модели gemini-3.8-flash
          model = genai.GenerativeModel("gemini-3.8-flash")

          video_title = "Видео по ссылке (Ancient Mysteries / Lost Civilizations)"
          video_stats_text = (
              f"Ссылка на оригинал: https://www.youtube.com/watch?v={vid_id}"
          )

          if yt_key:
            yt_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={vid_id}&key={yt_key}"
            resp = requests.get(yt_url).json()
            if "items" in resp and len(resp["items"]) > 0:
              item = resp["items"][0]
              video_title = item["snippet"]["title"]
              views = item["statistics"].get("viewCount", "N/A")
              channel_title = item["snippet"]["channelTitle"]
              video_stats_text += f"\nНазвание: {video_title}\nКанал: {channel_title}\nПросмотры: {views}"

          prompt = f"""
                    You are an expert YouTube documentary producer, script analyst, visual director, and audience-retention strategist for a channel about "Ancient Mysteries & Lost Civilizations".
                    
                    Analyze the following YouTube video information:
                    {video_stats_text}
                    
                    Provide a comprehensive, professional breakdown and complete production package for creating an original, high-performing clone video in English (with clear sections so the user can easily translate if needed).
                    
                    Structure your response in these exact sections using Markdown headers:
                    
                    ## 1. 🔍 Niche & Competitor Intelligence (Разведка ниши и конкурентов)
                    - Are there similar videos on YouTube? Evaluate the market saturation.
                    - Estimated potential success / likelihood of outperforming the original if we clone it.
                    
                    ## 2. 🎯 Success Breakdown & Retention Analysis (Анализ успеха и удержание)
                    - Why did this video succeed? (Hook, psychological triggers, thumbnail/title hook).
                    - Estimated peak retention timeline (which minutes keep the viewer engaged and where drop-offs happen).
                    
                    ## 3. 📜 Original Script-Analogue (Уникальный сценарий-аналог)
                    - Write a full, compelling script in English about a related ancient mystery or lost civilization that captures the exact same narrative momentum without copying text.
                    
                    ## 4. 🎙️ Voiceover Script & Delivery Instructions (Текст для озвучки)
                    - Provide the script formatted for text-to-speech (ElevenLabs), including pauses [pause], emotional emphasis, and pacing notes.
                    
                    ## 5. 🎨 AI Visual Generation Prompts (Промпты для генерации картинок по кадрам)
                    - Provide 5-8 sequential visual prompts for AI image generators (Midjourney/DALL-E) to illustrate the story scene by scene.
                    
                    ## 6. 🎬 CapCut Editing & Pacing Plan (План монтажа для CapCut)
                    - Step-by-step timeline editing instructions: where to apply fast zooms, cinematic transitions, sound effects (SFX), and atmospheric background music style.
                    
                    Language requirement: Respond in {'Russian' if is_ru else 'English'} for the analysis parts, but keep the script and visual prompts in English as requested by the user.
                    """

          response = model.generate_content(prompt)
          result_text = response.text

          new_project = {
              "title": video_title,
              "url": url_input,
              "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
              "content": result_text,
          }
          history = load_history()
          history.insert(0, new_project)
          save_history(history[:20])

          st.success(
              "✅ Анализ и генерация успешно завершены!"
              if is_ru
              else "✅ Analysis and generation completed successfully!"
          )
          st.markdown(result_text)

          st.download_button(
              label=(
                  "📥 Скачать весь пакет (TXT)"
                  if is_ru
                  else "📥 Download Full Package (TXT)"
              ),
              data=result_text,
              file_name=f"clone_package_{vid_id}.txt",
              mime="text/plain",
          )

        except Exception as e:
            st.error(f"❌ Ошибка при обработке: {e}")

elif history and "selected_proj_idx" in locals():
  selected_proj = history[selected_proj_idx]
  st.divider()
  st.subheader(
      f"📂 Проект из истории: {selected_proj['title']}"
      if is_ru
      else f"📂 Historical Project: {selected_proj['title']}"
  )
  st.caption(
      f"Дата: {selected_proj['date']} | Ссылка: {selected_proj['url']}"
  )
  st.markdown(selected_proj["content"])

  st.download_button(
      label=(
          "📥 Скачать этот пакет (TXT)" if is_ru else "📥 Download Package (TXT)"
      ),
      data=selected_proj["content"],
      file_name="saved_clone_package.txt",
      mime="text/plain",
  )
