import requests
from bs4 import BeautifulSoup
import time

import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import Update
from telegram.ext import CallbackContext

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Create a model instance
model = genai.GenerativeModel('gemini-pro')

# Define conversation states
WAITING_FOR_USERNAME = 0

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("من روستتون میکنم. 🎬\nیوزرنیم لترباکستونو بزنید:")
    return WAITING_FOR_USERNAME

def handle_username(update: Update, context: CallbackContext) -> int:
    username = update.message.text.strip()
    
    if not username:
        update.message.reply_text("یوزرنیم خالی که نمیشه")
        return WAITING_FOR_USERNAME
    
    update.message.reply_text(f"دنبال فیلمام {username}...")
    
    try:
        five_star = get_five_star_movies(username)
        
        if five_star:
            # Send "generating roast" message
            update.message.reply_text("در حال توهین و تحقیر... 🔥")
            
            # Pass the update object to chat_with_gemini
            success = chat_with_gemini(username, five_star, update)
            if success:
                # The roast was successful, end the conversation
                update.message.reply_text("یکی دیگه?  /start")
                return ConversationHandler.END
        else:
            update.message.reply_text("فیلم میلم نداشت:")
            return WAITING_FOR_USERNAME
            
    except Exception as e:
        update.message.reply_text(f"ارور: {str(e)}\n:")
        return WAITING_FOR_USERNAME

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('بای!  /start')
    return ConversationHandler.END

def main():
    # Initialize bot with token from .env
    updater = Updater(os.getenv('TELEGRAM_BOT_TOKEN'))
    dp = updater.dispatcher

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_USERNAME: [MessageHandler(Filters.text & ~Filters.command, handle_username)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

def generate_roast_prompt(username, five_star_movies):
    return f"""Based on this Letterboxd user's ({username}) movie ratings, please create a humorous roast of their taste in movies. 

    
Their favorite movies (5 stars): {', '.join(five_star_movies)}
Don't mention the name of the movies at all, just do a general roast of their taste in movies.
give your answer in Farsi.
be creative and funny and rude, make it hurt, at least 2 paragraphs"""

def chat_with_gemini(username, five_star_movies, update):
    max_retries = 3
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            prompt = generate_roast_prompt(username, five_star_movies)
            response = model.generate_content(prompt,
                                           safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            })
            
            # Send the roast message using the passed update object
            update.message.reply_text(response.text)
            return True
                
        except Exception as e:
            print(f"\nError generating roast (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            
    update.message.reply_text("یه مشکلی هست قطعا")
    return False

def get_five_star_movies(username):
    url = f"https://letterboxd.com/{username}/films/rated/5/"
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Get the webpage
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        five_star_movies = [tag['data-film-slug'] for tag in soup.find_all(attrs={"data-film-slug": True})]

        # Find all movie entries
        
        if not five_star_movies:
            print(f"به هیچ فیلمی ۵ ندادی: {username}")
            return []
        
        return five_star_movies  # Return the list instead of printing
            
    except requests.exceptions.RequestException as e:
        print(f"لترباکس اذیت کرد: {str(e)}")
        return []
    except Exception as e:
        print(f"ارور: {str(e)}")
        return []

if __name__ == "__main__":
    main()
