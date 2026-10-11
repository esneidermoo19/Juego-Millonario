/**
 * Controlador de la Pantalla de Resultados (results.html)
 */

document.addEventListener('DOMContentLoaded', () => {
  const resultDataStr = sessionStorage.getItem('game_result');
  const resultIcon = document.getElementById('result-icon');
  const resultTitle = document.getElementById('result-title');
  const resultMessage = document.getElementById('result-message');
  const finalPrizeEl = document.getElementById('final-prize');
  const resultPlayerEl = document.getElementById('result-player');

  const prizeAfterCorrectAnswers = (count) => {
    const ladder = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 125000, 250000, 500000, 1000000];
    return count > 0 ? ladder[Math.min(count, ladder.length) - 1] : 0;
  };

  const resolveFinalPrize = (result) => {
    const rawPrize = result.prize ?? '$0';
    const numericPrize = typeof rawPrize === 'number'
      ? rawPrize
      : Number(String(rawPrize).replace(/[^0-9]/g, '')) || 0;
    if (result.type !== 'loss' || numericPrize > 0) return rawPrize;

    // Sesiones antiguas guardaban $0 antes de alcanzar el primer nivel seguro.
    let correctCount = Number.isInteger(result.correctlyAnswered)
      ? result.correctlyAnswered
      : Number(result.cleared) || 0;
    if (result.reason === 'timeout' && !Number.isInteger(result.correctlyAnswered)) {
      correctCount = Math.max(0, correctCount - 1);
    }
    return formatCurrency(prizeAfterCorrectAnswers(correctCount));
  };

  if (!resultDataStr) {
    // Si entran sin partida previa, mostrar estado por defecto
    if (resultPlayerEl) resultPlayerEl.textContent = 'Invitado';
    if (finalPrizeEl) finalPrizeEl.textContent = '$0';
    return;
  }

  try {
    const result = JSON.parse(resultDataStr);

    if (resultPlayerEl) {
      resultPlayerEl.textContent = result.player || 'Jugador';
    }

    if (finalPrizeEl) {
      finalPrizeEl.textContent = resolveFinalPrize(result);
    }

    // Configuración según el desenlace (Victoria, Derrota, Retirada)
    if (result.type === 'win') {
      if (resultIcon) resultIcon.textContent = '👑';
      if (resultTitle) {
        resultTitle.innerHTML = '<span class="logo-gold">¡ERES MILLONARIO!</span>';
      }
      if (resultMessage) {
        resultMessage.textContent = `¡Felicitaciones! Respondiste correctamente las 15 preguntas y conquistaste el juego.`;
      }
    } else if (result.type === 'quit') {
      if (resultIcon) resultIcon.textContent = '💰';
      if (resultTitle) {
        resultTitle.innerHTML = '<span class="logo-pink">TE HAS RETIRADO</span>';
      }
      if (resultMessage) {
        resultMessage.textContent = `Tomaste una sabia decisión y aseguraste tu dinero acumulado.`;
      }
    } else {
      // Pérdida / Derrota
      if (resultIcon) resultIcon.textContent = '💥';
      if (resultTitle) {
        resultTitle.textContent = 'FIN DEL JUEGO';
      }
      if (resultMessage) {
        const questionReached = Number.isInteger(result.correctlyAnswered)
          ? (Number(result.cleared) || result.correctlyAnswered + 1)
          : result.reason === 'timeout'
            ? (Number(result.cleared) || 0)
            : (Number(result.cleared) || 0) + 1;
        resultMessage.textContent = result.reason === 'timeout'
          ? `Se agotó el tiempo. Llegaste hasta la pregunta ${questionReached}. ¡Inténtalo de nuevo!`
          : `Respuesta incorrecta. Llegaste hasta la pregunta ${questionReached}. ¡Inténtalo de nuevo!`;
      }
    }

  } catch (err) {
    console.error('Error al procesar resultados:', err);
  }
});
