import os
import pandas as pd
from geopy.distance import geodesic
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Завантаження укриттів
df = pd.read_csv("shelters.csv")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton(text="Надіслати геолокацію", request_location=True)
    reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Надішли свою геолокацію, і я знайду найближчі укриття.", reply_markup=reply_markup)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_location = (update.message.location.latitude, update.message.location.longitude)
    df["distance"] = df.apply(lambda row: geodesic(user_location, (row["latitude"], row["longitude"])).meters, axis=1)
    nearest = df.nsmallest(3, "distance")

    response = "Найближчі укриття:\n"
    
    for _, row in nearest.iterrows():
        url = f"https://www.google.com/maps/search/?api=1&query={row['latitude']},{row['longitude']}"
        response += f"{row['name']} – {int(row['distance'])} м
{url}

"

    await update.message.reply_text(response)

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.run_polling()

if __name__ == "__main__":
    main()
