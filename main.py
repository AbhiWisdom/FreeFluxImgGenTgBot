import logging
import requests
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import random

# Initialize logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = ''
API_URL = "https://api.abhibhai.com/api/v4/dreambooth"
KEY = ""  # Get free api from Tg Bot - @abhibotsbot 
CHANNEL_CHAT_ID = '@abhibots'
GROUP_CHAT_ID = -4.... # Group ID for membership check
# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)


# Negative prompt to exclude unwanted features in image generation
Negative_image_prompt = (
    "dark skin, painting, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, "
    "deformed body, unattractive, blurry details, bad anatomy, incorrect proportions, extra limbs, "
    "cloned or duplicate features, overly thin or exaggerated body shapes, glitch effects, double torso, "
    "extra arms, extra hands, distorted or mangled fingers, missing facial features, unattractive or distorted face, "
    "extra legs, cartoon or anime style, unrealistic textures, blemishes, rough skin, unclear face, low resolution, "
    "noise, incorrect lighting, unnatural body poses, asymmetry, and unappealing aesthetics."
)

bot = telebot.TeleBot(BOT_TOKEN)

# Initialize a dictionary to store user-specific model IDs
user_model_ids = {}
default_model_id = "flux"

# Helper function to check if a user is a member of a chat
def is_user_member(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status not in ['left', 'kicked']
    except Exception as e:
        logging.error(f"Error checking user membership: {str(e)}")
        return False

# Function to select image size based on prompt
def select_image_size(prompt):
    size_options = [(1024, 1024), (1024, 768), (768, 1024)]
    if "wide" in prompt or "landscape" in prompt:
        return 1024, 768
    elif "tall" in prompt or "portrait" in prompt:
        return 768, 1024
    elif "square" in prompt:
        return 1024, 1024
    else:
        return random.choice(size_options)

# /changemodel command: changes the AI model for the user
@bot.message_handler(commands=['changemodel'])
def change_model_id(message):
    user_id = message.from_user.id
    new_model_id = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if new_model_id:
        user_model_ids[user_id] = new_model_id
        bot.send_message(message.chat.id, f"Model ID changed to {new_model_id} for you.")
    else:
        bot.send_message(message.chat.id, "Please provide a new model ID after the command.")


@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = message.from_user.id

    inline_markup = InlineKeyboardMarkup()
    see_more_button = InlineKeyboardButton("Join AbhiBts", url="t.me/abhibots")
    inline_markup.add(see_more_button)
    
    # Updated welcome message with only the available commands
    welcome_text = (
        "🌟 Welcome to the AI Image Bot! 🌟\n\n"
        "Here's what I can do for you:\n\n"
        "✨ **Image Generation:**\n"
        "- Use /gen followed by your prompt to generate unique images.\n"
        "- Change the AI model with /changemodel followed by the model ID.\n\n"
        "👉 Join our channel @Abhibots for more cool features and updates.\n\n"
        "Get started by sending a prompt or try out the commands listed above!"
    )

    bot.send_message(message.chat.id, welcome_text, reply_markup=inline_markup)


# /gen command: generates an image based on a prompt
@bot.message_handler(commands=['gen'])
def generate_image(message):
    user_id = message.from_user.id
    model_id_to_use = user_model_ids.get(user_id, default_model_id)
    channel_username = "@Abhibots"

    # Check if the user is a member of the required channel
    if not is_user_member(channel_username, user_id):
        bot.send_message(message.chat.id, "Please join @Abhibots to use this feature.")
        return

    prompt = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not prompt or len(prompt.split()) <= 1:
        bot.send_message(message.chat.id, "Please provide a prompt longer than 5 words after the /gen command.")
        return

    width, height = select_image_size(prompt)
    payload = {
        "api_key": KEY,
        "model_id": model_id_to_use,
        "negative_prompt": Negative_image_prompt,
        "prompt": prompt,
        "width": width,
        "height": height,
        "samples": "1",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "seed": "null",
        "guidance_scale": "7.5",
        "multi_lingual": "yes",
        "panorama": "no",
        "self_attention": "no",
        "upscale": "yes",
        "embeddings_model": None,
        "lora_model": "",
        "tomesd": "yes",
        "clip_skip": "2",
        "use_karras_sigmas": "yes",
        "vae": None,
        "lora_strength": "0.5",
        "scheduler": "UniPCMultistepScheduler",
        "webhook": None,
        "track_id": None
    }
    
    headers = {
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'YourUserAgent'
    }

    notification_message = bot.send_message(message.chat.id, "🌈 Generating your image...")

    # Send the request to the Stable Diffusion API
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        try:
            data = response.json()
            image_url = data.get('output', [None])[0]
            if not image_url:
                bot.send_message(message.chat.id, "No image URL found in the API response.")
                return

            # Download the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                image_data = image_response.content
                caption = f"✨ Model ID: {model_id_to_use}\n📝 User Prompt:\n {prompt}\n🤖 Bot - @Abhimg_Bot"
                bot.send_photo(chat_id=message.chat.id, photo=image_data, caption=caption)
                bot.delete_message(chat_id=message.chat.id, message_id=notification_message.message_id)
            else:
                bot.send_message(message.chat.id, "Failed to download the image.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Error processing API response: {str(e)}")
    else:
        bot.send_message(message.chat.id, "Failed to generate the image.")

while True:
    try:
        bot.polling()
    except Exception as e:
        logging.error(f"Bot polling failed: {e}")
        time.sleep(5)  # Wait before restarting
