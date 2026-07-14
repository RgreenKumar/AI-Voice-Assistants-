import os
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, send_file
from config import Config
from services.chatbot_service import ChatbotService
from services.voice_service import VoiceService
from io import BytesIO

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
voice_service = VoiceService()


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


@app.route('/voice/synthesize', methods=['POST'])
def synthesize_voice():
    """
    Convert text to speech using Google Text-to-Speech API.
    Falls back to client-side Web Speech Synthesis if API not configured.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    
    try:
        # Attempt to use Google TTS API if configured
        audio_bytes = voice_service.text_to_speech(text)
        
        if audio_bytes:
            return send_file(
                BytesIO(audio_bytes),
                mimetype='audio/mpeg',
                as_attachment=False
            )
        else:
            # Return a flag to use client-side Web Speech Synthesis
            return jsonify({
                'success': True,
                'useClientTTS': True,
                'message': 'Using browser text-to-speech'
            })
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/voice/check', methods=['GET'])
def check_voice_support():
    """
    Check if voice synthesis APIs are available.
    """
    has_google_tts = bool(os.getenv('GOOGLE_TTS_API_KEY', ''))
    return jsonify({
        'success': True,
        'googleTTSAvailable': has_google_tts,
        'message': 'Voice support check complete'
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)