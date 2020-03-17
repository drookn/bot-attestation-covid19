import logging
import os
import requests
import time
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

class Service:
  def __init__(self, name, status):
    self.name = name
    if status == 'available':
      self.status  = "✅"
    else:
      self.status  = "🎚"
  def toString(self):
      return self.status + ' ' + self.name

def getAppleServiceStatusData():
    ship_api_url = "https://app-stat-api.herokuapp.com/us/services.json"
    request_data = requests.get(ship_api_url)
    return request_data.json()['services']

def getAppleServiceStatus():
    allService = ""
    dictService = getAppleServiceStatusData()
    for service in dictService:
      name = service['title']
      status = service['status']
      serviceObject = Service(service['title'], service['status'])
      allService = allService + '\n' + serviceObject.toString()
    return allService

def status(bot,update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)
    update.effective_message.reply_text(getAppleServiceStatus())
    
def start(bot, update):
    update.effective_message.reply_text("Hello  I am an Apple Status Developer Bot 👨🏻‍💻,\n send \'/status\' to get last Apple Service Status")

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
    PORT = os.environ.get('PORT')
    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    # Set up the Updater
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    # Add handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('status', status))
    dp.add_handler(MessageHandler(Filters.text, start))
    dp.add_error_handler(error)
    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
    updater.idle()
