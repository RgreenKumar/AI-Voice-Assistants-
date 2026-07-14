/**
 * Voice Module - Handles speech recognition and text-to-speech
 * Uses Web Speech API for speech recognition (free, browser-native)
 * Uses Web Speech Synthesis API as fallback or Google TTS API if available
 */

class VoiceManager {
  constructor() {
    // Speech Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = SpeechRecognition ? new SpeechRecognition() : null;
    this.isListening = false;
    this.transcript = '';
    this.interimTranscript = '';

    // Text-to-Speech Setup
    this.synth = window.speechSynthesis;
    this.isSpeaking = false;
    this.voiceOutputEnabled = localStorage.getItem('voiceOutputEnabled') !== 'false';
    this.autoPlayVoice = localStorage.getItem('autoPlayVoice') === 'true';
    this.useGoogleTTS = false;

    this.initSpeechRecognition();
    this.checkVoiceSupport();
    this.setupEventListeners();
  }

  /**
   * Initialize speech recognition engine
   */
  initSpeechRecognition() {
    if (!this.recognition) {
      console.warn('Speech Recognition not supported in this browser');
      return;
    }

    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onstart = () => {
      this.isListening = true;
      this.showRecordingIndicator();
      console.log('Speech recognition started');
    };

    this.recognition.onresult = (event) => {
      this.interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          this.transcript += transcript + ' ';
        } else {
          this.interimTranscript += transcript;
        }
      }

      // Update UI with interim results
      if (this.interimTranscript) {
        document.getElementById('messageInput').value = this.transcript + this.interimTranscript;
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      this.hideRecordingIndicator();
      showToast(`Voice error: ${event.error}`);
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.hideRecordingIndicator();
      
      // Set the final transcript to input field
      if (this.transcript) {
        document.getElementById('messageInput').value = this.transcript;
        this.transcript = '';
        console.log('Speech recognition ended');
      }
    };
  }

  /**
   * Check voice API support and availability
   */
  async checkVoiceSupport() {
    try {
      const response = await fetch('/voice/check');
      const data = await response.json();
      this.useGoogleTTS = data.googleTTSAvailable;
      console.log('Voice support:', { 
        googleTTS: this.useGoogleTTS,
        webSpeechAPI: !!this.recognition,
        webSynthAPI: !!this.synth 
      });
    } catch (error) {
      console.error('Failed to check voice support:', error);
    }
  }

  /**
   * Setup UI event listeners
   */
  setupEventListeners() {
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    const voiceOutputToggle = document.getElementById('voiceOutputToggle');
    const autoPlayVoiceToggle = document.getElementById('autoPlayVoiceToggle');

    if (voiceInputBtn) {
      voiceInputBtn.addEventListener('click', () => this.toggleVoiceInput());
    }

    if (voiceOutputToggle) {
      voiceOutputToggle.checked = this.voiceOutputEnabled;
      voiceOutputToggle.addEventListener('change', (e) => {
        this.voiceOutputEnabled = e.target.checked;
        localStorage.setItem('voiceOutputEnabled', this.voiceOutputEnabled);
        showToast(this.voiceOutputEnabled ? 'Voice output enabled' : 'Voice output disabled');
      });
    }

    if (autoPlayVoiceToggle) {
      autoPlayVoiceToggle.checked = this.autoPlayVoice;
      autoPlayVoiceToggle.addEventListener('change', (e) => {
        this.autoPlayVoice = e.target.checked;
        localStorage.setItem('autoPlayVoice', this.autoPlayVoice);
        showToast(this.autoPlayVoice ? 'Auto-play enabled' : 'Auto-play disabled');
      });
    }

    // Keyboard shortcut: Ctrl+Shift+V for voice input
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'V') {
        e.preventDefault();
        this.toggleVoiceInput();
      }
    });
  }

  /**
   * Toggle voice input on/off
   */
  toggleVoiceInput() {
    if (!this.recognition) {
      showToast('Speech recognition not supported in your browser');
      return;
    }

    if (this.isListening) {
      this.recognition.stop();
    } else {
      this.transcript = '';
      this.interimTranscript = '';
      document.getElementById('messageInput').value = '';
      this.recognition.start();
    }
  }

  /**
   * Show recording indicator UI
   */
  showRecordingIndicator() {
    const indicator = document.getElementById('recordingIndicator');
    const btn = document.getElementById('voiceInputBtn');
    if (indicator) indicator.style.display = 'inline-flex';
    if (btn) btn.classList.add('active');
  }

  /**
   * Hide recording indicator UI
   */
  hideRecordingIndicator() {
    const indicator = document.getElementById('recordingIndicator');
    const btn = document.getElementById('voiceInputBtn');
    if (indicator) indicator.style.display = 'none';
    if (btn) btn.classList.remove('active');
  }

  /**
   * Synthesize speech from text using available APIs
   * @param {string} text - Text to convert to speech
   */
  async synthesizeAndPlay(text) {
    if (!this.voiceOutputEnabled) {
      return;
    }

    if (this.isSpeaking) {
      this.stopSpeech();
      return;
    }

    try {
      // Try Google TTS API first if available
      if (this.useGoogleTTS) {
        await this.playGoogleTTS(text);
      } else {
        // Fall back to Web Speech Synthesis API
        this.playWebSynthesis(text);
      }
    } catch (error) {
      console.error('Speech synthesis error:', error);
      // Fall back to Web Synthesis if Google TTS fails
      this.playWebSynthesis(text);
    }
  }

  /**
   * Play speech using Google Text-to-Speech API
   * @param {string} text - Text to synthesize
   */
  async playGoogleTTS(text) {
    try {
      const response = await fetch('/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        const data = await response.json();
        if (data.useClientTTS) {
          // API not configured, use client-side
          this.playWebSynthesis(text);
          return;
        }
        throw new Error(data.error || 'TTS failed');
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audioElement = new Audio(audioUrl);
      
      this.isSpeaking = true;
      this.updateSpeakingUI(true);

      audioElement.onended = () => {
        this.isSpeaking = false;
        this.updateSpeakingUI(false);
        URL.revokeObjectURL(audioUrl);
      };

      audioElement.onerror = () => {
        console.error('Audio playback error');
        this.isSpeaking = false;
        this.updateSpeakingUI(false);
      };

      audioElement.play().catch((error) => {
        console.error('Failed to play audio:', error);
        this.playWebSynthesis(text);
      });
    } catch (error) {
      console.error('Google TTS error:', error);
      this.playWebSynthesis(text);
    }
  }

  /**
   * Play speech using Web Speech Synthesis API
   * @param {string} text - Text to synthesize
   */
  playWebSynthesis(text) {
    // Cancel any ongoing speech
    this.synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try to use a natural voice
    const voices = this.synth.getVoices();
    if (voices.length > 0) {
      const preferredVoice = voices.find(v => v.lang.includes('en')) || voices[0];
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      this.updateSpeakingUI(true);
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      this.updateSpeakingUI(false);
    };

    utterance.onerror = (error) => {
      console.error('Speech synthesis error:', error);
      this.isSpeaking = false;
      this.updateSpeakingUI(false);
    };

    this.synth.speak(utterance);
  }

  /**
   * Stop speech playback
   */
  stopSpeech() {
    if (this.synth.speaking) {
      this.synth.cancel();
    }
    this.isSpeaking = false;
    this.updateSpeakingUI(false);
  }

  /**
   * Update UI to reflect speaking state
   * @param {boolean} speaking - Whether currently speaking
   */
  updateSpeakingUI(speaking) {
    const audioElement = document.getElementById('voiceOutput');
    if (audioElement) {
      audioElement.parentElement.style.opacity = speaking ? '1' : '0.5';
    }
  }

  /**
   * Auto-play voice output for assistant message
   * @param {string} text - Text to play
   */
  autoPlayMessage(text) {
    if (this.autoPlayVoice && this.voiceOutputEnabled) {
      // Small delay to ensure message is rendered first
      setTimeout(() => this.synthesizeAndPlay(text), 500);
    }
  }
}

// Initialize voice manager when DOM is ready
let voiceManager;

document.addEventListener('DOMContentLoaded', () => {
  voiceManager = new VoiceManager();
});

// Function to play voice from outside this module
function playVoiceOutput(text) {
  if (voiceManager) {
    voiceManager.synthesizeAndPlay(text);
  }
}

// Ensure voices are loaded for Web Speech Synthesis
if ('onvoiceschanged' in window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {
    console.log('Voices loaded:', window.speechSynthesis.getVoices().length);
  };
}
