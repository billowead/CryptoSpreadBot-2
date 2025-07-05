from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = '<YOUR_TOKEN>'
CHAT_ID = None  # Будем брать из сообщений
WEBHOOK_PATH = '/webhook'

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, data=data)
    print('Send message response:', r.text)

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    print('Webhook data:', data)
    
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        
        if text == '/start':
            send_message(chat_id, 'Привет! Бот работает.')
        else:
            send_message(chat_id, f'Вы написали: {text}')
    
    return 'OK'

if __name__ == '__main__':
    print('Starting Flask server...')
    app.run(host='0.0.0.0', port=10000)
