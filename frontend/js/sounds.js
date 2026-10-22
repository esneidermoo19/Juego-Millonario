/**
 * Reproductor de efectos de sonido con archivos de audio (.mp3).
 * Respeta la preferencia de silencio guardada en localStorage (mute_audio).
 *
 * - Precarga y reutiliza los elementos de audio para evitar latencia y tirones.
 * - Transición jingle -> música de fondo robusta (evento 'ended' + temporizador).
 */
(() => {
  const SOUNDS = {
    intro: 'assets/sounds/intro.mp3',
    question: 'assets/sounds/question.mp3',
    fail: 'assets/sounds/fail.mp3'
  };
  const CLOCK_MUSIC_SRC = 'assets/sounds/clock-music.mp3';

  const pool = {};      // Elementos de audio reutilizables (precargados)
  let clockAudio = null;
  let clockTimer = null;

  function isMuted() {
    return localStorage.getItem('mute_audio') === '1';
  }

  function getSound(name) {
    if (!pool[name]) {
      const audio = new Audio(SOUNDS[name]);
      audio.preload = 'auto';
      pool[name] = audio;
    }
    return pool[name];
  }

  function ensureClockAudio() {
    if (!clockAudio) {
      clockAudio = new Audio(CLOCK_MUSIC_SRC);
      clockAudio.loop = true;
      clockAudio.volume = 0.5;
      clockAudio.preload = 'auto';
    }
    return clockAudio;
  }

  // Precarga solo el intro (pantalla de inicio) para no descargar audio innecesario.
  function preloadIntro() {
    try {
      getSound('intro');
    } catch (_) {}
  }

  // Precarga los audios de la partida (pregunta, derrota y música de fondo).
  function preloadGame() {
    try {
      getSound('question');
      getSound('fail');
      ensureClockAudio();
    } catch (_) {}
  }

  function play(name, volume = 0.9) {
    if (isMuted()) return;
    const src = SOUNDS[name];
    if (!src) return;
    try {
      const audio = getSound(name);
      audio.volume = volume;
      audio.currentTime = 0;
      audio.play().catch(() => {});
    } catch (_) {}
  }

  // Reproduce un audio y resuelve la promesa cuando termina de sonar (con respaldo).
  function playAndWait(name, volume = 0.9) {
    if (isMuted()) return Promise.resolve();
    try {
      const audio = getSound(name);
      audio.volume = volume;
      audio.currentTime = 0;
      return new Promise((resolve) => {
        let settled = false;
        const finish = () => {
          if (settled) return;
          settled = true;
          audio.removeEventListener('ended', finish);
          resolve();
        };
        audio.addEventListener('ended', finish);
        window.setTimeout(finish, 20000);
        audio.play().catch(finish);
      });
    } catch (_) {
      return Promise.resolve();
    }
  }

  // Reproduce el intro y resuelve la promesa cuando termina (para no cortarlo al navegar).
  function playIntro() {
    return playAndWait('intro');
  }

  function clearClockTimer() {
    if (clockTimer) {
      window.clearTimeout(clockTimer);
      clockTimer = null;
    }
  }

  function startClockMusic() {
    clearClockTimer();
    if (isMuted()) return;
    try {
      const audio = ensureClockAudio();
      audio.currentTime = 0;
      audio.play().catch(() => {});
    } catch (_) {}
  }

  function stopClockMusic() {
    clearClockTimer();
    if (clockAudio) {
      try {
        clockAudio.pause();
        clockAudio.currentTime = 0;
      } catch (_) {}
    }
  }

  // Reproduce el jingle de la pregunta y arranca la música de fondo al terminar.
  function playQuestion() {
    if (isMuted()) return;
    try {
      const audio = getSound('question');
      audio.volume = 0.9;
      audio.currentTime = 0;
      clearClockTimer();

      let started = false;
      const start = () => {
        if (started) return;
        started = true;
        clearClockTimer();
        audio.removeEventListener('ended', start);
        startClockMusic();
      };
      audio.addEventListener('ended', start);

      // Fallback por si el evento 'ended' no llega (interrupción o fallo de carga).
      if (isFinite(audio.duration) && audio.duration > 0) {
        clockTimer = window.setTimeout(start, audio.duration * 1000 + 150);
      }
      audio.play().catch(() => {});
    } catch (_) {}
  }

  // Detiene la música de fondo y reproduce el jingle de derrota una sola vez.
  function playFail() {
    stopClockMusic();
    play('fail');
  }

  window.GameSounds = {
    preloadIntro,
    preloadGame,
    play,
    playIntro,
    playQuestion,
    startClockMusic,
    stopClockMusic,
    playFail
  };
})();
