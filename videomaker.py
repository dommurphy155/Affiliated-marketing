import os
import openai
import asyncio
import subprocess
import logging
from gtts import gTTS

logging.basicConfig(level=logging.INFO)

async def generate_openai_video(product, openai_api_key):
    openai.api_key = openai_api_key

    # Step 1: Generate product description script
    prompt = (
        f"Write a short, catchy, persuasive 30-second TikTok video script selling this product: {product['name']}. "
        "Make it sound urgent and appealing."
    )
    try:
        response = await asyncio.to_thread(
            lambda: openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.85,
            )
        )
        script = response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI script generation failed: {e}")
        raise

    # Step 2: Use gTTS to create voice audio file
    tts = gTTS(text=script, lang='en')
    audio_path = "/tmp/tts_audio.mp3"
    tts.save(audio_path)

    # Step 3: Create simple video with static image + audio using ffmpeg
    image_path = "assets/product_placeholder.jpg"  # Replace with your own image or AI-generated images later
    video_path = f"/tmp/{product['name'].replace(' ','_')}_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-t", "30",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        video_path
    ]

    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logging.error(f"FFmpeg error: {stderr.decode()}")
        raise Exception("Failed to generate video")

    return video_path
