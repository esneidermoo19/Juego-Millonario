/**
 * Reproductor de efectos de sonido con archivos de audio (.mp3).
 * Respeta la preferencia de silencio guardada en localStorage (mute_audio).
 */
(() => {
  const SOUNDS = {
    intro: 'assets/sounds/intro.mp3',
    question: 'assets/sounds/question.mp3',
    fail: 'assets/sounds/fail.mp3'
  };
  const CLOCK_MUSIC_SRC = 'assets/sounds/clock-music.mp3';

  let clockAudio = null;

  function isMuted() {
    return localStorage.getItem('mute_audio') === '1';
  }

  function play(name) {
    if (isMuted()) return;
    const src = SOUNDS[name];
    if (!src) return;
    try {
      const audio = new Audio(src);
      audio.volume = 0.9;
      audio.play().catch(() => {});
    } catch (_) {}
  }

  function ensureClockAudio() {
    if (clockAudio) return clockAudio;
    clockAudio = new Audio(CLOCK_MUSIC_SRC);
    clockAudio.loop = true;
    clockAudio.volume = 0.5;
    clockAudio.preload = 'auto';
    return clockAudio;
  }

  function preloadClockMusic() {
    try {
      ensureClockAudio();
    } catch (_) {}
  }

  // Reproduce el jingle de la pregunta y, al terminar, arranca la música de fondo.
  function playQuestion() {
    if (isMuted()) return;
    try {
      const audio = new Audio(SOUNDS.question);
      audio.volume = 0.9;
      audio.addEventListener('ended', () => startClockMusic(), { once: true });
      audio.play().catch(() => {});
    } catch (_) {}
  }

  function startClockMusic() {
    if (isMuted()) return;
    try {
      const audio = ensureClockAudio();
      audio.currentTime = 0;
      audio.play().catch(() => {});
    } catch (_) {}
  }

  function stopClockMusic() {
    if (clockAudio) {
      try {
        clockAudio.pause();
        clockAudio.currentTime = 0;
      } catch (_) {}
    }
  }

  // Detiene la música de fondo y reproduce el jingle de derrota.
  function playFail() {
    stopClockMusic();
    play('fail');
  }

  window.GameSounds = { play, playQuestion, startClockMusic, stopClockMusic, preloadClockMusic, playFail };
})();
