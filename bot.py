import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import PyPDF2
import docx

# 🔑 توکن‌ها
TELEGRAM_TOKEN = "8215698550:AAEncX3bKn_GPw7VYY8iNamDRmSsYuRebN4"
OPENROUTER_API_KEY = "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"

# حافظه گفتگو و اسناد
conversation = []
documents_text = ""  # محتوای همه فایل‌های ارسال شده

# استخراج متن از PDF
def read_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

# استخراج متن از Word
def read_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# تابع ارتباط با OpenRouter
def ask_openrouter(prompt):
    global conversation
    full_prompt = f"{documents_text}\n\nسوال: {prompt}"
    conversation.append({"role": "user", "content": full_prompt})

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": conversation[-6:],  # فقط ۶ پیام آخر
        "temperature": 0.9
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        conversation.append({"role": "assistant", "content": reply})
        return reply
    else:
        return "❌ خطا در ارتباط با OpenRouter"

# هندلر شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات هوش مصنوعی با قابلیت جستجو در فایل‌ها هستم.\n"
                                    "فایل PDF یا Word بفرست تا از محتوای آن جواب بدم.")

# هندلر پیام‌ها
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global documents_text
    if update.message.document:
        # بررسی نوع فایل
        file = update.message.document
        file_name = file.file_name
        file_path = f"temp_{file_name}"
        await file.get_file().download(file_path)

        if file_name.endswith(".pdf"):
            text = read_pdf(file_path)
        elif file_name.endswith(".docx"):
            text = read_docx(file_path)
        else:
            await update.message.reply_text("فقط PDF یا Word پشتیبانی میشه.")
            return

        documents_text += "\n" + text
        await update.message.reply_text(f"✅ فایل {file_name} ذخیره شد و آماده پاسخگویی است.")
        os.remove(file_path)
    else:
        user_message = update.message.text
        reply = ask_openrouter(user_message)
        await update.message.reply_text(reply)

# اجرای ربات
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.Document.ALL, chat))
    print("🤖 ربات روشن شد و آماده کار است...")
    app.run_polling()

if __name__ == "__main__":
    main()
