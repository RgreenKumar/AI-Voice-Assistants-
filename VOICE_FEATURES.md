# Voice Features Documentation

## Overview
The AI Knowledge Assistant now includes advanced voice input and output capabilities, making it similar to ChatGPT's voice features. Users can:

- **Speak to the AI**: Use the microphone button to record voice input
- **Hear AI responses**: Automatically play voice output of AI responses
- **Customize voice settings**: Toggle voice output and auto-play preferences

## Features

### 1. Voice Input (Speech-to-Text)
The application uses the **Web Speech API** for voice recognition, which is free and built into most modern browsers.

#### How it Works:
- Click the 🎤 microphone button or press **Ctrl+Shift+V** to start recording
- Speak your question or command
- The speech is automatically converted to text and added to the input field
- The recording stops when you finish speaking (automatic silence detection)
- The text can then be sent to the AI by clicking the Send button or pressing Enter

#### Supported Browsers:
- Chrome/Chromium ✅
- Edge ✅
- Safari (iOS) ✅
- Firefox (with flags enabled) ⚠️
- Opera ✅

### 2. Voice Output (Text-to-Speech)
The application supports two methods for voice synthesis:

#### Method 1: Web Speech Synthesis API (Default, Free)
- Built into all modern browsers
- No API key required
- Enables immediate voice output functionality

#### Method 2: Google Cloud Text-to-Speech API (Optional, Premium)
- Higher quality, more natural voices
- Requires Google Cloud API key
- Better performance and multiple voice options

### 3. Voice Settings

#### Voice Output Toggle
- Located in the sidebar under "Voice Settings"
- When enabled, assistant responses can be played as audio
- Each message has a 🔊 button to manually play the voice

#### Auto-play Voice Toggle
- When enabled, assistant responses are automatically spoken aloud
- Respects the Voice Output setting
- Useful for hands-free operation

## Setup Instructions

### Basic Setup (No API Required)
The application works out-of-the-box with Web Speech Synthesis API:

1. Open the application in your browser
2. Click the 🎤 button to record a message
3. Speak your question
4. The AI will respond with text and optional voice output
5. Use the sidebar toggles to customize voice preferences

### Advanced Setup (Google Cloud TTS, Optional)

#### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Text-to-Speech API**:
   - Click "Enable APIs and Services"
   - Search for "Text-to-Speech API"
   - Click "Enable"

#### Step 2: Create an API Key
1. Go to "Credentials" in the left menu
2. Click "Create Credentials" → "API Key"
3. Copy the API key

#### Step 3: Configure Environment Variable
1. Open or create the `.env` file in the project root
2. Add the following line:
   ```
   GOOGLE_TTS_API_KEY=your_api_key_here
   ```
3. Restart the Flask application

#### Step 4: Test the Setup
1. Open the application
2. Check the browser console for confirmation: "Voice support: {googleTTS: true, ...}"
3. Send a message and the AI response will use Google TTS for audio

## How to Use

### Recording Voice Input
1. **Click the microphone button** (🎤) next to the input field
   - Or press **Ctrl+Shift+V** as a keyboard shortcut
2. **Speak clearly** into your microphone
   - You'll see "Recording..." indicator with a pulsing dot
   - Interim results appear in real-time
3. **Stop speaking** - the app automatically detects silence and stops recording
4. **Send your message** by clicking Send or pressing Enter

### Playing Voice Output
#### Manual Playback
1. Hover over any assistant message
2. Click the 🔊 button that appears in the message bubble
3. The message will be read aloud

#### Automatic Playback
1. Enable "Auto-play Voice" in the sidebar Voice Settings
2. Every assistant response will automatically be spoken aloud

### Disabling Voice Features
1. Uncheck "Voice Output" in the sidebar to disable all audio playback
2. Uncheck "Auto-play Voice" to keep voice enabled but stop auto-playing messages

## Technical Details

### Frontend Architecture
- **voice.js**: Manages all voice functionality (speech recognition and synthesis)
- **app.js**: Integrates voice with chat messages
- **Web Speech API**: Provides speech-to-text (free, browser-native)
- **Web Speech Synthesis API**: Provides text-to-speech (free, browser-native)

### Backend Services
- **voice_service.py**: Handles Google TTS API integration (optional)
- **app.py**: Exposes `/voice/synthesize` and `/voice/check` endpoints

### API Endpoints

#### Check Voice Support
```
GET /voice/check
Response: {
  "success": true,
  "googleTTSAvailable": boolean,
  "message": "Voice support check complete"
}
```

#### Synthesize Speech (Optional Google TTS)
```
POST /voice/synthesize
Content-Type: application/json

Body: {
  "text": "Your message here"
}

Response: 
- If Google TTS available: Audio stream (MP3)
- Otherwise: {"success": true, "useClientTTS": true}
```

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Speech-to-Text | ✅ | ⚠️ | ✅ | ✅ |
| Web Synthesis | ✅ | ✅ | ✅ | ✅ |
| Google TTS | ✅ | ✅ | ✅ | ✅ |
| Keyboard Shortcut | ✅ | ⚠️ | ✅ | ✅ |

*⚠️ May require browser flags or extensions*

## Troubleshooting

### Microphone Button Not Working
- **Issue**: Microphone button doesn't respond
- **Solution**: 
  - Check browser microphone permissions (check address bar)
  - Ensure your browser supports Web Speech API
  - Try a different browser (Chrome recommended)
  - Restart your browser

### Speech Recognition Not Detecting Words
- **Issue**: Spoken words not being converted to text
- **Solution**:
  - Speak clearly and at normal pace
  - Check microphone is working (test with system settings)
  - Reduce background noise
  - Ensure language is set to English (en-US)
  - Try Firefox or Safari if using Chrome

### Voice Output Not Playing
- **Issue**: Audio doesn't play or sounds distorted
- **Solution**:
  - Check browser volume and system volume
  - Ensure "Voice Output" is enabled in sidebar
  - Check browser audio permissions
  - If using Google TTS, verify API key is set correctly
  - Try browser's default Web Speech Synthesis

### Google TTS Not Working
- **Issue**: Google Text-to-Speech API errors
- **Solution**:
  - Verify API key is correct in `.env`
  - Check Google Cloud account has billing enabled
  - Ensure Text-to-Speech API is enabled in Google Cloud
  - Check API quota hasn't been exceeded
  - Fallback to Web Speech Synthesis will activate automatically

## Performance Tips

1. **Speech Recognition**: 
   - Speak in a quiet environment
   - Use a good quality microphone
   - Speak at normal pace and volume

2. **Voice Output**:
   - If using Google TTS, responses may have slight network delay
   - Web Speech Synthesis is instantaneous
   - Adjust speaking rate in browser settings for better comprehension

3. **Resource Usage**:
   - Voice features have minimal impact on performance
   - Audio playback is streamed (not pre-cached)
   - Recording is processed client-side only

## Future Enhancements

Potential features for future versions:
- [ ] Support for multiple languages
- [ ] Voice profile training for personalized responses
- [ ] Real-time transcription display
- [ ] Voice command shortcuts (e.g., "search news about X")
- [ ] Speaker identification and multi-user support
- [ ] Transcript export with audio recordings
- [ ] Custom voice rate, pitch, and volume controls

## Support

For issues or questions about voice features:
1. Check this documentation first
2. Review browser console for error messages (F12 → Console)
3. Test microphone permissions in browser settings
4. Try alternative browsers for comparison

---

**Note**: Voice features require a microphone and speaker/headphones connected to your device. Ensure you've granted the web application microphone permissions when prompted by your browser.
