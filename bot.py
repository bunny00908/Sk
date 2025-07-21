import os
from dotenv import load_dotenv
import stripe
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()
stripe.api_key = os.getenv('STRIPE_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text('Use /cc card_number|exp_month|exp_year|cvc to check a card (test mode only, e.g., /cc 4242424242424242|12|26|123).')

async def check_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /cc command to check a credit card using Stripe."""
    try:
        args = context.args
        if len(args) != 1 or '|' not in args[0]:
            await update.message.reply_text('Usage: /cc card_number|exp_month|exp_year|cvc')
            return
        # Parse the card details
        card_number, exp_month, exp_year, cvc = args[0].split('|')
        # Validate inputs
        if not (card_number.isdigit() and exp_month.isdigit() and exp_year.isdigit() and cvc.isdigit()):
            await update.message.reply_text('Error: All fields must be numeric.')
            return
        exp_month = int(exp_month)
        exp_year = int(exp_year)
        if exp_month < 1 or exp_month > 12:
            await update.message.reply_text('Error: Invalid expiration month.')
            return
        if exp_year < 2025 or exp_year > 2030:
            await update.message.reply_text('Error: Invalid expiration year.')
            return
        payment_intent = stripe.PaymentIntent.create(
            amount=100,  # $1 in cents
            currency='usd',
            payment_method_data={
                'type': 'card',
                'card': {
                    'number': card_number,
                    'exp_month': exp_month,
                    'exp_year': exp_year,
                    'cvc': cvc,
                },
            },
            capture_method='manual',  # Pre-authorization, no charge
            confirm=True,
        )
        if payment_intent.status == 'requires_capture':
            await update.message.reply_text('Approved')
            stripe.PaymentIntent.cancel(payment_intent.id)  # Cancel to avoid holding funds
        else:
            await update.message.reply_text('Declined')
    except stripe.error.CardError as e:
        await update.message.reply_text(f'Declined: {e.error.message}')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

def main():
    """Initialize and run the Telegram bot with explicit timezone."""
    if not TELEGRAM_BOT_TOKEN or not stripe.api_key:
        print("Error: TELEGRAM_BOT_TOKEN or STRIPE_API_KEY not set in .env")
        return
    # Build the application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    # Set the JobQueue timezone explicitly
    if application.job_queue:
        application.job_queue.scheduler.configure(timezone=pytz.timezone('Asia/Kolkata'))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cc', check_card))
    application.run_polling()

if __name__ == '__main__':
    main()
