import logging
import os
import requests
import time
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from fpdf import FPDF
import PyPDF2
from reportlab.pdfgen import canvas


class Service:
  def __init__(self, name, status):
    self.name = name
    if status == 'available':
      self.status  = "💎"
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
    bot.send_document(chat_id=update.effective_chat.id, document=open('Ressources/certificate_of_travel_exemption.pdf', 'rb'))
    #update.effective_message.reply_text(getAppleServiceStatus())

def sendPdf(bot,update):

    #Create PDF with user data 
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(100, 10, txt="Thomas Droin De la vera", ln=1, align="L")
    pdf.cell(100, 10, txt="Tom DRN", ln=50, align="L")
    pdf.cell(100, 10, txt="06/08/1991", ln=1, align="L")
    pdf.cell(100, 10, txt="Address", ln=1, align="L")
    pdf.output("simple_demo.pdf")

    c = canvas.Canvas("hello.pdf")
    c.drawString(120,625,"Thomas Droin De la vera")
    c.drawString(120,600,"06/08/1991")
    c.drawString(120,575,"9B BOULEVARD DE ROCHECHOUART 75009 PARIS")
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
    update.effective_message.reply_text("Salut je suis Covid19 Bot 👨🏻‍💻,\n send \'/status\' to get last Apple Service Status")

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
    dp.add_handler(CommandHandler('sendPdf', sendPdf))
    dp.add_handler(MessageHandler(Filters.text, start))
    dp.add_error_handler(error)
    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
    updater.idle()
