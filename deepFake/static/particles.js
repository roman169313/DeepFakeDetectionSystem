/**
 * Background particles — visible, non-interactive (no hover/click).
 * Loaded after particles.min.js on DOM ready.
 */
(function () {
  function initParticles() {
    if (typeof particlesJS === 'undefined') {
      console.warn('particles.min.js not loaded');
      return;
    }
    var el = document.getElementById('particles-js');
    if (!el) return;

    particlesJS('particles-js', {
      particles: {
        number: { value: 100, density: { enable: true, value_area: 900 } },
        color: { value: '#a5b4fc' },
        shape: { type: 'circle' },
        opacity: { value: 0.55, random: true, anim: { enable: false } },
        size: { value: 3, random: true, anim: { enable: false } },
        line_linked: {
          enable: true,
          distance: 150,
          color: '#6366f1',
          opacity: 0.35,
          width: 1,
        },
        move: {
          enable: true,
          speed: 1.5,
          direction: 'none',
          random: true,
          out_mode: 'out',
        },
      },
      interactivity: {
        detect_on: 'canvas',
        events: {
          onhover: { enable: false },
          onclick: { enable: false },
          resize: true,
        },
      },
      retina_detect: true,
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initParticles);
  } else {
    initParticles();
  }
})();
