from moviepy.editor import *
from gtts import gTTS
import os
import logging
from openai import OpenAI

def generate_script(product_name):
    # Simple fallback if OpenAI is unavailable
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = f"Write a 15-second viral TikTok ad script for a trending product called '{product_name}'. Make it hype, short, persuasive."
        chat = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        logging.warning(f"OpenAI failed, using fallback script: {e}")
        return f"{product_name} is blowing up right now! Grab it before it's gone. Link in bio!"

def create_video(product_name, image_path, output_path="autoposts/video.mp4"):
    try:
        os.makedirs("autoposts", exist_ok=True)

        # Generate script & voiceover
        script = generate_script(product_name)
        tts = gTTS(script)
        audio_path = "autoposts/voiceover.mp3"
        tts.save(audio_path)

        # Build video
        img_clip = ImageClip(image_path).set_duration(10).resize(height=720)
        audio_clip = AudioFileClip(audio_path).subclip(0, img_clip.duration)
        final_clip = img_clip.set_audio(audio_clip)

        final_clip.write_videofile(output_path, fps=24)
        return output_path
    except Exception as e:
        logging.error(f"Video generation failed: {e}")
        return None
