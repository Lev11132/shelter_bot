import os
import pandas as pd
from geopy.distance import geodesic
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

df = pd.read_csv("shelters.csv")
TYPES = df["name"].unique().tolist()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton(text="Надіслати геолокацію", request_location=True)
    reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Надішли свою геолокацію для пошуку укриттів.", reply_markup=reply_markup)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_location = update.message.location
    context.user_data["user_location"] = (user_location.latitude, user_location.longitude)

    type_buttons = [[InlineKeyboardButton(t, callback_data=f"type_{t}")] for t in TYPES]
    reply_markup = InlineKeyboardMarkup(type_buttons + [[InlineKeyboardButton("Показати всі типи", callback_data="type_all")]])
    await update.message.reply_text("Оберіть тип укриття:", reply_markup=reply_markup)

async def type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_type = query.data.replace("type_", "")
    context.user_data["selected_type"] = selected_type

    radius_buttons = [
        [InlineKeyboardButton("1 км", callback_data="radius_1000")],
        [InlineKeyboardButton("3 км", callback_data="radius_3000")],
        [InlineKeyboardButton("5 км", callback_data="radius_5000")],
        [InlineKeyboardButton("Показати всі на мапі", callback_data="show_all_map")]
    ]
    reply_markup = InlineKeyboardMarkup(radius_buttons)
    await query.edit_message_text("Оберіть радіус пошуку:", reply_markup=reply_markup)

async def radius_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_location = context.user_data.get("user_location")
    selected_type = context.user_data.get("selected_type")

    if not user_location:
        await query.edit_message_text("Спочатку надішліть геолокацію.")
        return

    if query.data == "show_all_map":
        text = "Мапа з усіма укриттями: https://www.google.com/maps/d/u/0/viewer?mid=1VT7MBpAXCVfa3_ToOzlovSpW5RRO3lWZ"
        await query.edit_message_text(text)
        return

    radius = int(query.data.replace("radius_", ""))
    filtered = df.copy()

    if selected_type != "all":
        filtered = filtered[filtered["name"] == selected_type]

    filtered["distance"] = filtered.apply(lambda row: geodesic(user_location, (row["latitude"], row["longitude"])).meters, axis=1)
    nearby = filtered[filtered["distance"] <= radius].sort_values("distance").head(5)

    if nearby.empty:
        await query.edit_message_text(f"Укриттів типу '{selected_type}' у межах {radius // 1000} км не знайдено.")
        return

    response = f"Тип: {selected_type}, радіус: {radius // 1000} км

"
    for _, row in nearby.iterrows():
        url = f"https://www.google.com/maps/search/?api=1&query={row['latitude']},{row['longitude']}"
        response += f"{row['name']} – {int(row['distance'])} м
{url}

"

    await query.edit_message_text(response)

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(type_selected, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(radius_selected, pattern="^(radius_|show_all_map)"))
    app.run_polling()

if __name__ == "__main__":
    main()