import stripe
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Replace with your Stripe test API key
stripe.api_key = 'sk_test_51RmqVa2Ki2lOqBdBRY3iAuJBjAUgGTZu3JHnEgeaK360eDHKggYlFXh1xjpEKiscaVQht2CiDVKc8pmO3R8BUspI00EYD8gVJL'

# Replace with your Telegram bot token
TELEGRAM_BOT_TOKEN = '7971051467:AAEgFdgmEcmfYmIWfSqQ_sCv0MNNzcrl49Y'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Use /cc <card_number> <exp_month> <exp_year> <cvc> to check a card (test mode only).')

async def check_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Parse command: /cc card_number exp_month exp_year cvc
        args = context.args
        if len(args) != 4:
            await update.message.reply_text('Usage: /cc <card_number> <exp_month> <exp_year> <cvc>')
            return

        card_number, exp_month, exp_year, cvc = args
        exp_month = int(exp_month)
        exp_year = int(exp_year)

        # Create a PaymentIntent for $1
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
            capture_method='manual',  # Pre-authorization
            confirm=True,
        )

        if payment_intent.status == 'requires_capture':
            await update.message.reply_text('Approved')
            # Cancel the PaymentIntent to avoid holding funds
            stripe.PaymentIntent.cancel(payment_intent.id)
        else:
            await update.message.reply_text('Declined')

    except stripe.error.CardError as e:
        await update.message.reply_text(f'Declined: {e.error.message}')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

def main():
    # Initialize the bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cc', check_card))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
