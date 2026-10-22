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

  // Precarga todos los audios (y calienta la caché del navegador) para que suenen al instante.
  function preload() {
    try {
      Object.keys(SOUNDS).forEach(getSound);
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

  // Reproduce un audio (repetido `loops` veces) y resuelve la promesa cuando termina.
  function playAndWait(name, volume = 0.9, loops = 1) {
    if (isMuted()) return Promise.resolve();
    try {
      const audio = getSound(name);
      audio.loop = false;
      audio.volume = volume;
      audio.currentTime = 0;
      return new Promise((resolve) => {
        let settled = false;
        let remaining = Math.max(1, loops);
        const finish = () => {
          if (settled) return;
          settled = true;
          audio.removeEventListener('ended', onEnded);
          resolve();
        };
        const onEnded = () => {
          remaining -= 1;
          if (remaining <= 0) {
            finish();
          } else {
            audio.currentTime = 0;
            audio.play().catch(finish);
          }
        };
        // 'ended' es la señal real de cada reproducción; el temporizador solo evita
        // quedarse colgado si el audio falla (no corta una reproducción normal).
        audio.addEventListener('ended', onEnded);
        window.setTimeout(finish, 30000);
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

  // Detiene la música de fondo y reproduce el jingle de derrota varias veces.
  function playFail() {
    stopClockMusic();
    return playAndWait('fail', 0.9, 3);
  }

  window.GameSounds = {
    preload,
    play,
    playIntro,
    playQuestion,
    startClockMusic,
    stopClockMusic,
    playFail
  };
})();
