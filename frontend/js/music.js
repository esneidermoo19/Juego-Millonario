/**
 * Fondo musical del concurso.
 * Reproduce assets/audio/tema-principal.mp3 si existe (debe ser libre de derechos);
 * si no está disponible, genera un fondo original con Web Audio API.
 */
(() => {
  const TRACK_URL = 'assets/audio/tema-principal.mp3';
  const TRACK_VOLUME = 0.5;
  const MEASURE_SECONDS = 4;
  const chords = [
    { pad: [110, 164.81, 220], notes: [659.25, 783.99, 880, 783.99, 659.25, 587.33, 659.25, 783.99] },
    { pad: [87.31, 130.81, 174.61], notes: [698.46, 880, 1046.5, 880, 783.99, 698.46, 783.99, 880] },
    { pad: [65.41, 130.81, 196], notes: [659.25, 783.99, 987.77, 783.99, 659.25, 587.33, 659.25, 783.99] },
    { pad: [98, 146.83, 196], notes: [587.33, 783.99, 880, 783.99, 587.33, 523.25, 587.33, 783.99] }
  ];

  let context = null;
  let master = null;
  let measureTimer = null;
  let measureIndex = 0;
  let requested = false;
  let muted = localStorage.getItem('mute_audio') === '1';
  let track = null;
  let trackFailed = false;

  function ensureContext() {
    if (context) return context;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return null;

    context = new AudioContext();
    master = context.createGain();
    master.gain.value = 0;
    master.connect(context.destination);
    return context;
  }

  function prepareFromGesture() {
    try {
      const audioContext = ensureContext();
      if (audioContext?.state === 'suspended') audioContext.resume().catch(() => {});
    } catch (_) {}
  }

  function scheduleTone(frequency, startAt, duration, amplitude, type) {
    const oscillator = context.createOscillator();
    const envelope = context.createGain();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, startAt);
    envelope.gain.setValueAtTime(0.0001, startAt);
    envelope.gain.exponentialRampToValueAtTime(amplitude, startAt + 0.04);
    envelope.gain.setValueAtTime(amplitude, Math.max(startAt + 0.05, startAt + duration - 0.12));
    envelope.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);
    oscillator.connect(envelope);
    envelope.connect(master);
    oscillator.start(startAt);
    oscillator.stop(startAt + duration + 0.02);
    oscillator.addEventListener('ended', () => {
      oscillator.disconnect();
      envelope.disconnect();
    }, { once: true });
  }

  function playMeasure() {
    if (!context || !master || muted || !requested) return;
    const measure = chords[measureIndex % chords.length];
    const startAt = context.currentTime + 0.03;
    measure.pad.forEach((frequency, index) => {
      scheduleTone(frequency, startAt, MEASURE_SECONDS, index === 0 ? 0.055 : 0.035, 'sine');
    });
    measure.notes.forEach((frequency, index) => {
      scheduleTone(frequency, startAt + index * 0.5, 0.38, 0.10, 'triangle');
    });
    measureIndex += 1;
  }

  // Intenta usar el archivo de audio; devuelve false si no hay archivo disponible.
  function startTrack() {
    if (trackFailed) return false;
    if (!track) {
      track = new Audio(TRACK_URL);
      track.loop = true;
      track.volume = TRACK_VOLUME;
      track.addEventListener('error', () => {
        trackFailed = true;
        track = null;
        if (requested && !muted) startSynth();
      }, { once: true });
    }
    track.play().catch(() => {});
    return true;
  }

  function start() {
    if (muted) return;
    requested = true;
    if (startTrack()) return;
    startSynth();
  }

  function startSynth() {
    try {
      if (!ensureContext()) return;
      if (context.state === 'suspended') context.resume().catch(() => {});
      master.gain.cancelScheduledValues(context.currentTime);
      master.gain.setTargetAtTime(0.32, context.currentTime, 0.35);
      if (measureTimer !== null) return;
      playMeasure();
      measureTimer = window.setInterval(playMeasure, MEASURE_SECONDS * 1000);
    } catch (_) {}
  }

  function setMuted(nextMuted) {
    muted = Boolean(nextMuted);
    if (muted) {
      if (track) track.pause();
      if (master && context) {
        master.gain.cancelScheduledValues(context.currentTime);
        master.gain.setTargetAtTime(0.0001, context.currentTime, 0.08);
      }
      return;
    }
    if (requested) start();
  }

  window.ContestMusic = { prepareFromGesture, start, setMuted };
})();
