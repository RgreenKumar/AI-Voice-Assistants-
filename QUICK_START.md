# 🎤 Voice Features - Quick Start Guide

## What's New? 
Your AI Voice Assistant now has **voice input and voice output** features, just like ChatGPT!

### ✨ New Features:

1. **🎤 Voice Input** - Speak to the AI instead of typing
   - Click the microphone button next to the input field
   - Or press `Ctrl+Shift+V` 
   - Speak your question naturally
   - Your speech is automatically converted to text

2. **🔊 Voice Output** - Hear the AI's responses
   - Enable "Voice Output" in the sidebar
   - Either click the speaker icon on messages to play them
   - Or enable "Auto-play Voice" to hear responses automatically

3. **⚙️ Voice Settings** (in sidebar)
   - Toggle "Voice Output" on/off
   - Toggle "Auto-play Voice" for hands-free operation

---

## Getting Started (2 minutes)

### 1. Start the app as usual:
```bash
python app.py
```

### 2. Open in your browser:
```
http://localhost:5000
```

### 3. Try voice input:
- Click the 🎤 button
- Say: "What is Python?"
- The text will appear and you can press Enter or click Send

### 4. Try voice output:
- Enable "Voice Output" in the left sidebar
- Get a response from the AI
- Click the 🔊 button in the message, or enable "Auto-play Voice"
- You'll hear the response read aloud!

---

## Optional: Google Cloud Text-to-Speech (Higher Quality Voices)

For higher quality voice output, you can set up Google Cloud TTS:

### 1. Get Google API Key:
- Visit: https://console.cloud.google.com/
- Create a new project
- Enable "Text-to-Speech API"
- Create an API Key in Credentials section
- Copy the key

### 2. Add to `.env` file:
```
GOOGLE_TTS_API_KEY=your_key_here
```

### 3. Restart the app:
```bash
python app.py
```

That's it! The app will now use Google's natural voices instead of the browser's default.

---

## Browser Compatibility

| Browser | Voice Input | Voice Output |
|---------|------------|-------------|
| Chrome  | ✅ Works   | ✅ Works     |
| Edge    | ✅ Works   | ✅ Works     |
| Firefox | ✅ Works   | ✅ Works     |
| Safari  | ✅ Works   | ✅ Works     |

---

## Keyboard Shortcut
- **Ctrl+Shift+V** = Toggle voice input recording

---

## Troubleshooting

**"Microphone not working"**
- Check browser's microphone permissions (usually in address bar)
- Ensure microphone is connected and not muted
- Try Chrome if using another browser

**"Voice not playing"**
- Check volume (system & browser)
- Ensure "Voice Output" is enabled in sidebar
- Try clicking the 🔊 button manually first

**"Text not converting to speech"**
- This is normal - fallback works automatically
- Google TTS API is optional, browser voice always works

---

## Architecture

```
Voice Input Flow:
User speaks → Browser records → Web Speech API → Text added to input

Voice Output Flow:
AI responds → Message added → Auto-play checks setting → Synthesized to audio → Played
```

---

## Files Changed/Added

### New Files:
- `services/voice_service.py` - Backend voice service
- `static/js/voice.js` - Frontend voice manager
- `VOICE_FEATURES.md` - Detailed documentation
- `QUICK_START.md` - This file

### Modified Files:
- `app.py` - Added voice endpoints
- `config.py` - Added Google TTS API key config
- `templates/index.html` - Added voice UI elements
- `static/js/app.js` - Integrated voice with messages
- `static/css/style.css` - Added voice styling

---

## Next Steps

1. ✅ Run the app
2. ✅ Test voice input (click 🎤)
3. ✅ Test voice output (enable in sidebar)
4. ✅ (Optional) Set up Google TTS for better quality

---

**Enjoy your new voice-enabled AI assistant! 🎉**

For more details, see `VOICE_FEATURES.md`
