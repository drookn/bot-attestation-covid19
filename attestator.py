import logging
import os
import requests
import time
import telegram
import PyPDF2
import datetime
import qrcode


from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, Handler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, PicklePersistence
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont

# Conversation states handlers
NAME, BIRTH_DATE, BORN_PLACE, STREET, POSTAL_CODE, CITY, REASON, MOTIF = range(8)

# Command handlers
def start(update, context):
    update.effective_message.reply_text("Salut 👋,\nJe vais te générer une attestation de déplacement en PDF 📄 dès que tu le souhaiteras.\n Envoi /create pour démarrer.")

def help(update, context):
    update.effective_message.reply_text("Voici la liste des commandes:\n\n/create - Créer une attestation\n/donate - Payes moi un ☕️\n/help - Liste des commandes\n/cancel - Arreter l'attestation")

def contact(update, context):
    update.effective_message.reply_text("Pour me contacter : attestator_telegram@protonmail.com")

def donate(update, context):
    update.effective_message.reply_text("Tu peux me payer un café ici : https://www.buymeacoffee.com/5PR1xt2")

def reset(update, context):
	update.effective_message.reply_text("Tes données ont été supprimées! Tape /create pour démarrer une nouvelle création")
	del context.user_data['name']
	del context.user_data['birthdate']
	del context.user_data['bornPlace']
	del context.user_data['street']
	del context.user_data['postalCode']
	del context.user_data['city']
	del context.user_data['reason']

def cancel(update, context):
    update.message.reply_text("Création annulé")
    return ConversationHandler.END

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

# Conversation handlers methods
def create(update, context):
	if context.user_data:
		update.message.reply_text("J'ai déja enregistrer tes informations!")
		motif(update,context)
		return REASON
	else:
		update.message.reply_text("Prénom Nom ? (ex: Thomas Martin)")
		return NAME

def name(update, context):
    context.user_data['name'] = update.message.text
    update.message.reply_text("Date de naissance ? (ex: 06/08/1991)")
    return BIRTH_DATE

def birthDate(update, context):
    context.user_data['birthdate'] = update.message.text
    update.message.reply_text("Lieu de naissance ?")
    return BORN_PLACE

def bornPlace(update, context):
    context.user_data['bornPlace'] = update.message.text
    update.message.reply_text("N° et Nom de la rue ? (ex: 12 rue Clignancourt)")
    return STREET

def street(update, context):
    context.user_data['street'] = update.message.text
    update.message.reply_text("Code Postal ? (ex: 75009)")
    return POSTAL_CODE

def postalCode(update, context):
    context.user_data['postalCode'] = update.message.text
    update.message.reply_text("Ville ? (ex: Paris)")
    return CITY

def city(update, context):
    context.user_data['city'] = update.message.text
    TOKEN = os.getenv("TOKEN")
    bot = telegram.Bot(TOKEN)
  
    # Create Custom reply
    custom_keyboard = [['travail', 'courses'], 
                   ['santé', 'famille'],
 ['sport', 'judiciaire', 'missions']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.effective_chat.id, 
                 text="Choisis ton motif:", 
                 reply_markup=reply_markup)
    return REASON

def motif(update, context):
    TOKEN = os.getenv("TOKEN")
    bot = telegram.Bot(TOKEN)
  
    # Create Custom reply
    custom_keyboard = [['travail', 'courses'], 
                   ['santé', 'famille'],
 ['sport', 'judiciaire', 'missions']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.effective_chat.id, 
                 text="Choisis ton motif:", 
                 reply_markup=reply_markup)
    return REASON

def reason(update, context):
    context.user_data['reason'] = update.message.text
    TOKEN = os.getenv("TOKEN")
    bot = telegram.Bot(TOKEN)
    bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)
    # createPdf(context.user_data['reason'])
    createQRcode(context,context.user_data['reason'])
    bot.send_message(chat_id=update.effective_chat.id, 
                 text="Voici ton QRcode, n'oublies pas de prendre tes précautions!",
                 reply_markup=ReplyKeyboardRemove())
    bot.send_photo(chat_id=update.effective_chat.id, photo=open('qrcode.jpg', 'rb'))
    return ConversationHandler.END

# def signature(update, context):
#     TOKEN = os.getenv("TOKEN")
#     bot = telegram.Bot(TOKEN)
#     #Download Image & save it
#     img = update.message.photo[-1].file_id
#     newFile = bot.get_file(img)
#     newFile.download('signature.png')

#     # Resizing image
#     imageOpen = Image.open("signature.png")
#     imageOpen = foo.resize((100,100),Image.ANTIALIAS)
#     imageOpen.save("signature_scaled_opt.png",optimize=True,quality=95)

#     # Create Custom reply
#     custom_keyboard = [['👩‍💻 Pro', '🍗 Achats de première nécessité'], 
#                    ['💊 Santé', '👨‍👩‍👧‍👦 Famille',
#  '⛹️‍♂️ Sport']]
#     reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
#     bot.send_message(chat_id=update.effective_chat.id, 
#                  text="Choisit ton motif:", 
#                  reply_markup=reply_markup)
#     return REASON


def createQRcode(context,reason):
	# Create qr code instance
	qr = qrcode.QRCode(
	    version = 1,
	    error_correction = qrcode.constants.ERROR_CORRECT_H,
	    box_size = 10,
	    border = 4,
	)
	today = datetime.datetime.now()
	# The data that you want to store
	
	data = "Cree le: " + today.strftime("%d") + "/" + today.strftime("%m") + "/" + today.strftime("%Y") + " a "+ today.strftime("%H") + "h" + today.strftime("%M") + "; Nom: " + str(context.user_data['name']) + "; Naissance: " + str(context.user_data['birthdate']) + "; Adresse: " + str(context.user_data['street']) + " " + str(context.user_data['postalCode']) + " " + str(context.user_data['city']) + "; Sortie: " + today.strftime("%d") + "/" + today.strftime("%m") + "/" + today.strftime("%Y") + " a "+ today.strftime("%H") + "h" + today.strftime("%M") + "; Motifs:" + str(reason)

	# Add data
	qr.add_data(data)
	qr.make(fit=True)

	# Create an image from the QR Code instance
	img = qr.make_image()

	# Save it somewhere, change the extension as needed:
	# img.save("image.png")
	# img.save("image.bmp")
	# img.save("image.jpeg")
	img.save("qrcode.jpg")


def createPdf(reason):

    # Create Canva
    c = canvas.Canvas("mask_info.pdf")

    # Write customer info on pdf
    c.drawString(130,625,context.user_data['name'])
    c.drawString(130,595,context.user_data['birthdate'])
    c.drawString(130,560,context.user_data['street'])
    c.drawString(130,545,context.user_data['postalCode'])
    c.drawString(130,530,context.user_data['city'])
    c.drawString(373,142,context.user_data['city'])

    # Get Day & month 
    today = datetime.datetime.now()

    # Write Day & month on Pdf
    c.drawString(475,142,today.strftime("%d"))
    c.drawString(500,142,today.strftime("%m"))

    # Get checkMarkLogo
    check_mark_logo = ImageReader('https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Check_mark_9x9.svg/24px-Check_mark_9x9.svg.png')

    # Write check mark on Pdf file
    if reason == "👩‍💻 Travail":
      c.drawImage(check_mark_logo, 45, 423, mask='auto')
    elif reason == "🍗 Courses":
      c.drawImage(check_mark_logo, 45, 348, mask='auto')
    elif reason == "💊 Santé":
      c.drawImage(check_mark_logo, 45, 271, mask='auto')
    elif reason == "👨‍👩‍👧‍👦 Famille":
      c.drawImage(check_mark_logo, 45, 303, mask='auto')
    else:
      c.drawImage(check_mark_logos, 45, 225, mask='auto')

    # Write check mark on Pdf file
    signature = ImageReader('signature_scaled_opt.png')
    c.drawImage(signature, 400, 0, mask='auto')

    # Save maskInfo pdf file
    c.save()

    # Merge two pdf
    certifFile = open('Ressources/certificate_of_travel_exemption.pdf', 'rb')
    pdfReader = PyPDF2.PdfFileReader(certifFile)
    certifFileFirstPage = pdfReader.getPage(0)
    maskInfoReader = PyPDF2.PdfFileReader(open('mask_info.pdf', 'rb'))
    certifFileFirstPage.mergePage(maskInfoReader.getPage(0))
    pdfWriter = PyPDF2.PdfFileWriter()
    pdfWriter.addPage(certifFileFirstPage)
    for pageNum in range(1, pdfReader.numPages):
           pageObj = pdfReader.getPage(pageNum)
           pdfWriter.addPage(pageObj)
    resultPdfFile = open('Attestation_Deplacement.pdf', 'wb')

    # Save merged Pdf file
    pdfWriter.write(resultPdfFile)
    certifFileFirstPage.close()
    resultPdfFile.close()

if __name__ == "__main__":
    # Get env variables from heroku configuration
    TOKEN = os.getenv("TOKEN")
    HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
    PORT = os.environ.get('PORT')

    my_persistence = PicklePersistence(filename='persistence')

    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    # Setup persistence
    pp = PicklePersistence(filename='conversationbot')
    updater = Updater(TOKEN, persistence=my_persistence, use_context=True)
    # Set up the Updater
    dp = updater.dispatcher
    # Add handlers
    dp.add_error_handler(error)
    dp.add_handler(CommandHandler("help",help))
    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CommandHandler("donate",donate))
    dp.add_handler(CommandHandler("reset",reset))
    dp.add_handler(CommandHandler("contact",contact))
    # Create conversation handler
    create_conversation_handler = ConversationHandler(
        entry_points = [CommandHandler('create',create)],

        states = {

            NAME: [MessageHandler(Filters.text, name)],

            BIRTH_DATE: [MessageHandler(Filters.text, birthDate)],

            BORN_PLACE: [MessageHandler(Filters.text, bornPlace)],

            STREET: [MessageHandler(Filters.text, street)],

            POSTAL_CODE: [MessageHandler(Filters.text, postalCode)],

            CITY: [MessageHandler(Filters.text, city)],

            REASON: [MessageHandler(Filters.text, reason)],

            MOTIF: [Handler(motif)]
        },
        fallbacks = [MessageHandler(Filters.regex('^Stop$'), cancel)],
        name="attestation_conversation",
        persistent=True
    )
    dp.add_handler(create_conversation_handler)
    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
    updater.idle()
