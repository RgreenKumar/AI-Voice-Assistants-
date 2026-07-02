import os
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from config import Config
from services.chatbot_service import ChatbotService

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / 'templates'),
    static_folder=str(BASE_DIR / 'static'),
)
app.secret_key = Config.SECRET_KEY
app.config['NEWS_API_KEY'] = Config.NEWS_API_KEY
chatbot_service = ChatbotService()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()

    if not message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400

    try:
        result = chatbot_service.handle_message(message)
        return jsonify({'success': True, **result})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/clear', methods=['POST'])
def clear_chat():
    chatbot_service.clear_history()
    return jsonify({'success': True, 'history': []})


@app.route('/history')
def history():
    return jsonify({'success': True, 'history': chatbot_service.get_history()})


@app.route('/export/txt', methods=['POST'])
def export_txt():
    history = chatbot_service.get_history()
    text = '\n\n'.join(f"{item['role']}: {item['content']}" for item in history)
    export_dir = BASE_DIR / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    path = export_dir / 'chat.txt'
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)
    return jsonify({'success': True, 'path': str(path)})


@app.route('/export/json', methods=['POST'])
def export_json():
    export_dir = BASE_DIR / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    path = export_dir / 'chat.json'
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(chatbot_service.get_history(), fh, indent=2)
    return jsonify({'success': True, 'path': str(path)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)