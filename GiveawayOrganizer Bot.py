import telebot
import random
from threading import Timer
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7977031363:AAEp7lxvsNjEySeDu9oCK8tlwmaJP2qJqEk'
bot = telebot.TeleBot(API_TOKEN)

# Store giveaways separately per creator
giveaways = {}

# Admin ID (Only this user can manage the bot)
ADMIN_ID = '1042486814'

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 You are not authorized to use this bot.")
        return
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🎉 Start Giveaway", callback_data="start_giveaway"),
        InlineKeyboardButton("🏆 End Giveaway", callback_data="end_giveaway")
    )
    bot.send_message(message.chat.id, "👋 Welcome to the Giveaway Bot!", reply_markup=keyboard)

# Handle Button Clicks
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    if str(call.from_user.id) != ADMIN_ID:
        bot.answer_callback_query(call.id, "🚫 You are not authorized to manage giveaways.")
        return

    bot.answer_callback_query(call.id)

    if call.data == "start_giveaway":
        start_giveaway(call.message)
    elif call.data == "end_giveaway":
        end_giveaway(call.message)
    elif call.data in ["first_comment", "correct_answer", "random_winner", "custom_number_winner"]:
        choose_giveaway_type(call)
    elif call.data == "custom_number_of_winners":
        ask_custom_number_of_winners(call)

# Start Giveaway
def start_giveaway(message):
    user_id = message.chat.id
    
    giveaways[user_id] = {
        "type": None,
        "participants": [],
        "question": None,
        "correct_answers": [],
        "winner": None,
        "custom_message": None,
        "custom_number": None,
        "number_of_winners": 1,
        "timer": None
    }

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("1️⃣ First Comment", callback_data="first_comment"),
        InlineKeyboardButton("2️⃣ Correct Answer", callback_data="correct_answer"),
        InlineKeyboardButton("3️⃣ Random Winner", callback_data="random_winner"),
        InlineKeyboardButton("4️⃣ Custom Number Winner", callback_data="custom_number_winner")
    )
    bot.send_message(message.chat.id, "📢 Choose the giveaway type:", reply_markup=keyboard)

# Choose Giveaway Type
def choose_giveaway_type(call):
    user_id = call.message.chat.id
    if user_id not in giveaways:
        return bot.send_message(call.message.chat.id, "⚠️ No active giveaway found. Start a new one using 🎉 Start Giveaway.")

    giveaways[user_id]["type"] = call.data

    # Ask for the number of winners
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("📊 Custom Number of Winners", callback_data="custom_number_of_winners")
    )
    bot.send_message(call.message.chat.id, "🎯 Select the number of winners:", reply_markup=keyboard)

# Ask Admin to Enter Custom Number of Winners
def ask_custom_number_of_winners(call):
    user_id = call.message.chat.id
    if user_id not in giveaways:
        return bot.send_message(call.message.chat.id, "⚠️ No active giveaway found. Start a new one using 🎉 Start Giveaway.")
    
    bot.send_message(call.message.chat.id, "❓ Please enter the custom number of winners (e.g., 5, 10, 20).")

    # Wait for the admin to enter the number
    bot.register_next_step_handler(call.message, set_custom_number_of_winners)

# Set Custom Number of Winners
def set_custom_number_of_winners(message):
    user_id = message.chat.id
    if user_id not in giveaways:
        return bot.send_message(message.chat.id, "⚠️ No active giveaway found. Start a new one using 🎉 Start Giveaway.")

    try:
        number_of_winners = int(message.text)
        giveaways[user_id]["number_of_winners"] = number_of_winners
        bot.send_message(message.chat.id, f"✅ Custom number of winners set to {number_of_winners}!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid number. Please enter a valid integer for the custom number of winners.")

    # Continue with the giveaway process based on type
    if giveaways[user_id]["type"] == "first_comment":
        bot.send_message(message.chat.id, "🏆 Giveaway started! First commenter wins.")
    elif giveaways[user_id]["type"] == "correct_answer":
        bot.send_message(message.chat.id, "❓ Send me the giveaway question.")
        bot.register_next_step_handler(message, set_giveaway_question)
    elif giveaways[user_id]["type"] == "random_winner":
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("⏳ 10s", callback_data="10"),
            InlineKeyboardButton("⏳ 30s", callback_data="30"),
            InlineKeyboardButton("⏳ 60s", callback_data="60")
        )
        bot.send_message(message.chat.id, "⏳ Select the time before a winner is picked:", reply_markup=keyboard)
    elif giveaways[user_id]["type"] == "custom_number_winner":
        bot.send_message(message.chat.id, "❓ Enter the custom number (e.g., 5th, 10th) participant to win.")
        bot.register_next_step_handler(message, set_custom_number)

# Set Question & Multiple Answers
def set_giveaway_question(message):
    user_id = message.chat.id
    if user_id not in giveaways:
        return bot.send_message(message.chat.id, "⚠️ No active giveaway found. Start a new one using 🎉 Start Giveaway.")

    giveaways[user_id]["question"] = message.text
    bot.send_message(message.chat.id, "✅ Question saved! Now send the correct answer(s). Enter each answer on a new line.")
    bot.register_next_step_handler(message, set_multiple_answers)

def set_multiple_answers(message):
    user_id = message.chat.id
    if user_id not in giveaways:
        return bot.send_message(message.chat.id, "⚠️ No active giveaway found. Start a new one using 🎉 Start Giveaway.")

    answers = message.text.split("\n")
    giveaways[user_id]["correct_answers"] = [answer.strip() for answer in answers if answer.strip()]
    bot.send_message(message.chat.id, f"✅ Multiple answers saved! The correct answers are: {', '.join(giveaways[user_id]['correct_answers'])}")
    bot.send_message(message.chat.id, f"🎯 Giveaway question is set:\n\n❓ *{giveaways[user_id]['question']}*\n\nCorrect answers are saved!")

# Set Custom Number Winner
def set_custom_number(message):
    user_id = message.chat.id
    if user_id not in giveaways:
        return bot.send_message(message.chat.id, "⚠️ No active giveaway found. Start a new one using 🎉 Start Giveaway.")

    try:
        giveaways[user_id]["custom_number"] = int(message.text)
        bot.send_message(message.chat.id, f"🎉 Custom winner set! The winner will be the {message.text}th participant.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid number. Please enter a valid integer for the custom number winner.")

# Start Random Giveaway with Timer
def start_random_giveaway(call):
    user_id = call.message.chat.id
    if user_id not in giveaways:
        return bot.send_message(call.message.chat.id, "⚠️ No active giveaway found. Start a new one using 🎉 Start Giveaway.")

    delay = int(call.data)
    bot.send_message(call.message.chat.id, f"⏳ Giveaway started! A winner will be picked in {delay} seconds.")

    giveaways[user_id]["timer"] = Timer(delay, pick_random_winner, [user_id])
    giveaways[user_id]["timer"].start()

# Handle User Messages (Giveaway Entries)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    for creator_id in giveaways:
        if giveaways[creator_id]["type"] is None:
            continue

        if giveaways[creator_id]["type"] == 'first_comment' and not giveaways[creator_id]["participants"]:
            giveaways[creator_id]["participants"].append(message.from_user)
            forward_message_to_creator(creator_id, message.from_user, message.text)

        elif giveaways[creator_id]["type"] == 'correct_answer':
            if message.text in giveaways[creator_id]["correct_answers"] and giveaways[creator_id]["winner"] is None:
                giveaways[creator_id]["winner"] = message.from_user
                forward_message_to_creator(creator_id, message.from_user, message.text)

        elif giveaways[creator_id]["type"] == 'random_winner':
            if message.from_user not in giveaways[creator_id]["participants"]:
                giveaways[creator_id]["participants"].append(message.from_user)
            bot.send_message(message.chat.id, "🎟 You're entered into the giveaway!")

        elif giveaways[creator_id]["type"] == 'custom_number_winner':
            if message.from_user not in giveaways[creator_id]["participants"]:
                giveaways[creator_id]["participants"].append(message.from_user)
            bot.send_message(message.chat.id, f"🎟 You're entered into the giveaway! Waiting for the {giveaways[creator_id]['custom_number']}th winner.")

# Automatically Pick Random Winner After Timer Ends
def pick_random_winner(user_id):
    if user_id not in giveaways:
        return

    participants = giveaways[user_id]["participants"]
    number_of_winners = giveaways[user_id]["number_of_winners"]

    if len(participants) >= number_of_winners:
        winners = random.sample(participants, number_of_winners)
        for winner in winners:
            forward_message_to_creator(user_id, winner, f"🎉 Random Winner! @{winner.username if winner.username else winner.first_name} is one of the winners!")
    else:
        bot.send_message(user_id, f"❌ Not enough participants. Only {len(participants)} entered the giveaway.")

    giveaways.pop(user_id, None)  # Remove giveaway session

# Forward the Winner Message to the Giveaway Creator and Participant
def forward_message_to_creator(user_id, winner, winning_message):
    winner_text = f"🏆 Winner: @{winner.username if winner.username else winner.first_name}\n\nMessage: {winning_message}"

    # Send the winner's info to the giveaway creator
    bot.send_message(user_id, winner_text)

    # Send a private message to the winner
    try:
        bot.send_message(winner.id, "🎉 You won the giveaway! 🎁")
    except Exception:
        bot.send_message(user_id, f"⚠️ Couldn't send a private message to @{winner.username if winner.username else winner.first_name}")

# End Giveaway & Pick Winner
@bot.message_handler(commands=['endgiveaway'])
def end_giveaway(message):
    user_id = message.chat.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 You are not authorized to end giveaways.")
        return

    if user_id in giveaways:
        bot.send_message(message.chat.id, "🛑 Giveaway ended!")
        giveaways.pop(user_id, None)
    else:
        bot.send_message(message.chat.id, "⚠️ No active giveaway to end.")

# Start Polling to keep the bot running
bot.polling(none_stop=True)