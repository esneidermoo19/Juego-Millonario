/**
 * Reproductor de efectos de sonido con archivos de audio (.mp3).
 * Respeta la preferencia de silencio guardada en localStorage (mute_audio).
 */
(() => {
  const SOUNDS = {
    intro: 'assets/sounds/intro.mp3',
    question: 'assets/sounds/question.mp3'
  };

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

  window.GameSounds = { play };
})();
