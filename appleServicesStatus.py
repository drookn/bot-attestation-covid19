import logging
import os
import requests
import time
import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, PicklePersistence
from fpdf import FPDF
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import datetime
from PIL import Image, ImageDraw, ImageFont

NAME, BIRTH_DATE, STREET, POSTAL_CODE, CITY, REASON, SIGNATURE = range(7)

def create(update, context):
    update.message.reply_text("Comment t’appelles tu ?")
    #bot.send_message(chat_id=update.effective_chat.id, text="Comment t’appelles tu ?")

    return NAME

def name(update, context):
    text =  update.message.text
    context.user_data['name'] = text
    #user_data = update.user_data
    #user_data[name] = update.message.text
    #update.send_message(chat_id=context.effective_chat.id, text="Quelle est ta date de naissance ?")
    update.message.reply_text("Quelle est ta date de naissance ?")


    return BIRTH_DATE

def birthDate(update, context):
    text =  update.message.text
    context.user_data['birthdate'] = text
    update.message.reply_text("Le n° et le nom de ta rue ?")

    return STREET

def street(update, context):
    text =  update.message.text
    context.user_data['street'] = text
    update.message.reply_text("Ton code postal ? 🔢")

    #context.user_data[street] = update.message.text
    #update.send_message(chat_id=context.effective_chat.id, text="Ton code postal ? 🔢")

    return POSTAL_CODE

def postalCode(update, context):
    text =  update.message.text
    context.user_data['postalCode'] = text
    update.message.reply_text("Ta ville ? 🔢")

    #context.user_data[postalCode] = context.message.text
    #update.send_message(chat_id=context.effective_chat.id, text="Ta ville ?")
    return CITY

def city(update, context):
    text =  update.message.text
    context.user_data['city'] = text
    update.message.reply_text("Envoi une photo de signature sur fond blanc")
    #update.send_message(chat_id=context.effective_chat.id, text="Thanks")
    return SIGNATURE


def reason(update, context):
    text =  update.message.text
    context.user_data['reason'] = text
    #update.send_message(chat_id=context.effective_chat.id, text="Thanks")

    c = canvas.Canvas("hello.pdf")
    c.drawString(130,625,context.user_data['name'])
    c.drawString(130,595,context.user_data['birthdate'])
    c.drawString(130,560,context.user_data['street'])
    c.drawString(130,545,context.user_data['postalCode'])
    c.drawString(130,530,context.user_data['city'])

    c.drawString(373,142,context.user_data['city'])

    today = datetime.datetime.now()
    c.drawString(475,142,today.strftime("%d"))
    c.drawString(500,142,today.strftime("%m"))


    logo = ImageReader('https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Check_mark_9x9.svg/24px-Check_mark_9x9.svg.png')

    if text == "👩‍🔧 Je vais bosser":
      c.drawImage(logo, 45, 423, mask='auto')
    elif text == "🍝 J’ai la dalle !":
      c.drawImage(logo, 45, 348, mask='auto')
    elif text == "💊 Je me soigne":
      c.drawImage(logo, 45, 271, mask='auto')
    elif text == "'👵 Je vais voir mamie'":
      c.drawImage(logo, 45, 303, mask='auto')
    else:
      c.drawImage(logo, 45, 225, mask='auto')

    #c.drawImage(logo, 45, 225, mask='auto')
    #c.drawImage(logo, 45, 271, mask='auto')
    #c.drawImage(logo, 45, 303, mask='auto')
    #c.drawImage(logo, 45, 348, mask='auto')
    #c.drawImage(logo, 45, 423, mask='auto')

    signature = ImageReader('signature_scaled_opt.png')

    c.drawImage(signature, 400, 0, mask='auto')
    c.save()


    minutesFile = open('Ressources/certificate_of_travel_exemption.pdf', 'rb')
    pdfReader = PyPDF2.PdfFileReader(minutesFile)
    minutesFirstPage = pdfReader.getPage(0)

    pdfWatermarkReader = PyPDF2.PdfFileReader(open('hello.pdf', 'rb'))
    
    minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
    pdfWriter = PyPDF2.PdfFileWriter()
    pdfWriter.addPage(minutesFirstPage)
    for pageNum in range(1, pdfReader.numPages):
           pageObj = pdfReader.getPage(pageNum)
           pdfWriter.addPage(pageObj)
    resultPdfFile = open('watermarkedCover.pdf', 'wb')
    pdfWriter.write(resultPdfFile)
    minutesFile.close()
    resultPdfFile.close()

    TOKEN = os.getenv("TOKEN")
    bot = telegram.Bot(TOKEN)

    bot.send_document(chat_id=update.effective_chat.id, document=open('watermarkedCover.pdf', 'rb'))
    return ConversationHandler.END

def signature(update, context):

    #Download Image & save it
    print("get photo")
    img = update.message.photo[-1].file_id

    TOKEN = os.getenv("TOKEN")
    bot = telegram.Bot(TOKEN)

    newFile = bot.get_file(img)

    newFile.download('signature.png')

    foo = Image.open("signature.png")
    foo = foo.resize((100,100),Image.ANTIALIAS)
    foo.save("signature_scaled_opt.png",optimize=True,quality=95)

    custom_keyboard = [['👩‍🔧 Je vais bosser ', '🍝 J’ai la dalle !'], 
                   ['💊 Je me soigne', '👵 Je vais voir mamie',
 '🏌️‍♂️ Petit sport, ça s’entretient un corps pareil']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    TOKEN = os.getenv("TOKEN")
    bot = telegram.Bot(TOKEN)

    bot.send_message(chat_id=update.effective_chat.id, 
                 text="Choisit ta raison parmis ces 5 propositions", 
                 reply_markup=reply_markup)

    return REASON

def cancel(bot,update):
    bot.send_message(chat_id=update.effective_chat.id, text="Cancel")
    return ConversationHandler.END

def status(bot,update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)
    bot.send_document(chat_id=update.effective_chat.id, document=open('Ressources/certificate_of_travel_exemption.pdf', 'rb'))
    #update.effective_message.reply_text(getAppleServiceStatus())

def sendPdf(bot,update):
    c = canvas.Canvas("hello.pdf")
    c.drawString(130,625,"Thomas Droin De la vera")
    c.drawString(130,595,"06/08/1991")
    c.drawString(130,560,"9B BOULEVARD DE ROCHECHOUART")
    c.drawString(130,545,"75009")
    c.drawString(130,530,"PARIS")

    c.drawString(373,142,"Paris")

    today = datetime.datetime.now()
    c.drawString(475,142,today.strftime("%d"))
    c.drawString(500,142,today.strftime("%m"))


    logo = ImageReader('https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Check_mark_9x9.svg/24px-Check_mark_9x9.svg.png')

    c.drawImage(logo, 45, 225, mask='auto')
    c.drawImage(logo, 45, 271, mask='auto')
    c.drawImage(logo, 45, 303, mask='auto')
    c.drawImage(logo, 45, 348, mask='auto')
    c.drawImage(logo, 45, 423, mask='auto')
    c.save()


    minutesFile = open('Ressources/certificate_of_travel_exemption.pdf', 'rb')
    pdfReader = PyPDF2.PdfFileReader(minutesFile)
    minutesFirstPage = pdfReader.getPage(0)

    pdfWatermarkReader = PyPDF2.PdfFileReader(open('hello.pdf', 'rb'))
    
    minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
    pdfWriter = PyPDF2.PdfFileWriter()
    pdfWriter.addPage(minutesFirstPage)
    for pageNum in range(1, pdfReader.numPages):
           pageObj = pdfReader.getPage(pageNum)
           pdfWriter.addPage(pageObj)
    resultPdfFile = open('watermarkedCover.pdf', 'wb')
    pdfWriter.write(resultPdfFile)
    minutesFile.close()
    resultPdfFile.close()

    bot.send_document(chat_id=update.effective_chat.id, document=open('watermarkedCover.pdf', 'rb'))

    
def start(bot, update):
    update.effective_message.reply_text("Salut 👋,\nJe vais te générer une attestation de déplacement en PDF 📄 dès que tu le souhaiteras.\nPour ça j’ai besoin que tu répondes à quelques questions.\nPromis une seule fois.")

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

    pp = PicklePersistence(filename='conversationbot')
    updater = Updater(TOKEN, persistence=pp, use_context=True)
    # Set up the Updater
    dp = updater.dispatcher
    # Add handlers
    dp.add_handler(CommandHandler('sendPdf', sendPdf))
    dp.add_error_handler(error)
    dp.add_handler(CommandHandler("help",start))

    create_conversation_handler = ConversationHandler(
        entry_points = [CommandHandler('create',create),CommandHandler('resend',city)],

        states = {

            NAME: [MessageHandler(Filters.text, name)],

            BIRTH_DATE: [MessageHandler(Filters.text, birthDate)],

            STREET: [MessageHandler(Filters.text, street)],

            POSTAL_CODE: [MessageHandler(Filters.text, postalCode)],

            CITY: [MessageHandler(Filters.text, city)],

            REASON: [MessageHandler(Filters.text, reason)],

            SIGNATURE: [MessageHandler(Filters.photo, signature)]

        },

        fallbacks = [MessageHandler(Filters.regex('^Done$'), cancel)]
    )
    dp.add_handler(create_conversation_handler)
   
    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
    updater.idle()
