/**
 * Voz de los presentadores.
 * 1) Pide al backend (/api/tts, espeak-ng) un audio con la voz del personaje.
 * 2) Si el servidor no puede, usa la voz del navegador (Web Speech API).
 * Respeta el botón de silencio (localStorage 'mute_audio').
 */
(() => {
  const TTS_URL = window.location.protocol === 'file:'
    ? 'http://127.0.0.1:5000/api/tts'
    : `${window.location.origin}/api/tts`;
  const synth = window.speechSynthesis;

  // Estilo para la voz del navegador. pitch: 0 (grave) a 2 (agudo); rate: velocidad.
  const BROWSER_STYLES = {
    clasico: { pitch: 1.0, rate: 1.0 },
    terminator: { pitch: 0.3, rate: 0.85 },
    masterchief: { pitch: 0.6, rate: 0.92 },
    james: { pitch: 1.2, rate: 1.08 },
    cr7: { pitch: 0.9, rate: 1.1 }
  };

  let voices = [];
  let pending = null;
  let currentAudio = null;
  let currentRequest = null;
  let serverAvailable = true;

  function loadVoices() {
    if (synth) voices = synth.getVoices();
  }

  function pickVoice(language) {
    const prefix = language === 'en' ? 'en' : 'es';
    const matching = voices.filter(voice => voice.lang.toLowerCase().startsWith(prefix));
    return matching.find(voice => voice.localService) || matching[0] || null;
  }

  function stop() {
    pending = null;
    if (currentRequest) currentRequest.abort();
    currentRequest = null;
    if (currentAudio) {
      currentAudio.pause();
      URL.revokeObjectURL(currentAudio.src);
      currentAudio = null;
    }
    if (synth) synth.cancel();
  }

  function speakWithBrowser(text, presenterKey, language) {
    if (!synth) return;
    if (!voices.length) loadVoices();
    const style = BROWSER_STYLES[presenterKey] || BROWSER_STYLES.clasico;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === 'en' ? 'en-US' : 'es-ES';
    const voice = pickVoice(language);
    if (voice) utterance.voice = voice;
    utterance.pitch = style.pitch;
    utterance.rate = style.rate;
    synth.speak(utterance);
  }

  async function speakWithServer(text, presenterKey, language) {
    const request = new AbortController();
    currentRequest = request;
    const response = await fetch(TTS_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, presenter: presenterKey, language }),
      signal: request.signal
    });
    if (!response.ok) throw new Error(`TTS ${response.status}`);
    const blob = await response.blob();
    if (currentRequest !== request) return; // Se pidió otra frase mientras tanto.
    currentRequest = null;

    const audio = new Audio(URL.createObjectURL(blob));
    currentAudio = audio;
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(audio.src);
      if (currentAudio === audio) currentAudio = null;
    }, { once: true });
    try {
      await audio.play();
    } catch (error) {
      // El navegador bloquea el sonido hasta el primer clic: se repite al interactuar.
      if (error.name === 'NotAllowedError') pending = { text, presenterKey, language };
    }
  }

  function speak(text, presenterKey = 'clasico', language = 'es') {
    if (!text) return;
    if (localStorage.getItem('mute_audio') === '1') return;
    stop();
    if (!serverAvailable) {
      speakWithBrowser(text, presenterKey, language);
      return;
    }
    speakWithServer(text, presenterKey, language).catch((error) => {
      if (error.name === 'AbortError') return;
      serverAvailable = false;
      speakWithBrowser(text, presenterKey, language);
    });
  }

  function speakAfterInteraction() {
    if (!pending) return;
    const { text, presenterKey, language } = pending;
    pending = null;
    speak(text, presenterKey, language);
  }

  if (synth) {
    loadVoices();
    synth.addEventListener?.('voiceschanged', loadVoices);
  }
  window.addEventListener('pointerdown', speakAfterInteraction, { once: true });
  window.addEventListener('keydown', speakAfterInteraction, { once: true });

  window.PresenterVoice = { speak, stop };
})();
