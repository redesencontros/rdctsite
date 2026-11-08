const toggle = document.querySelector('.menu-toggle');
const menu = document.querySelector('.site-menu');
const backdrop = document.querySelector('.menu-backdrop');
const close = document.querySelector('.menu-close');
const slides = [...document.querySelectorAll('.slide')];
const counter = document.querySelector('.slide-counter b');

let current = 0;
let rotation;
let transitioning = false;

// Escolhe uma imagem inicial aleatória
if (slides.length > 1) {
  current = Math.floor(Math.random() * slides.length);
}

slides.forEach(slide => slide.classList.remove('is-active'));

// Carregamento progressivo
function loadSlide(index) {
  const slide = slides[index];

  if (!slide) return Promise.resolve(false);

  if (slide.dataset.loaded === 'true') {
    return Promise.resolve(true);
  }

  if (slide.dataset.loading === 'true') {
    return slide.loadPromise;
  }

  const imagePath = slide.dataset.image;
  if (!imagePath) return Promise.resolve(false);

  slide.dataset.loading = 'true';

  slide.loadPromise = new Promise(resolve => {
    const img = new Image();

    img.onload = () => {
      slide.style.backgroundImage = `url("${imagePath}")`;
      slide.dataset.loaded = 'true';
      slide.dataset.loading = 'false';
      resolve(true);
    };

    img.onerror = () => {
      slide.dataset.loading = 'false';
      resolve(false);
    };

    img.src = imagePath;
  });

  return slide.loadPromise;
}

// Inicialização sem fade a partir do preto
async function initializeSlideshow() {
  const loaded = await loadSlide(current);

  if (!loaded) return;

  const firstSlide = slides[current];

  firstSlide.classList.add('no-transition');
  firstSlide.classList.add('is-active');

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      firstSlide.classList.remove('no-transition');
    });
  });

  loadSlide((current + 1) % slides.length);

  startRotation();
}

// Troca de imagem
async function showSlide(next) {
  if (transitioning) return;

  const target = next % slides.length;

  if (target === current) return;

  transitioning = true;

  const loaded = await loadSlide(target);

  if (!loaded) {
    transitioning = false;
    return;
  }

  const previous = slides[current];
  const nextSlide = slides[target];

  // Preserva a escala da imagem que está saindo
  const currentTransform = getComputedStyle(previous).transform;

  previous.style.animation = 'none';
  previous.style.transform = currentTransform;

  // Remove os estilos temporários da próxima imagem
  nextSlide.style.animation = '';
  nextSlide.style.transform = '';

  // Reinicia a animação antes de exibir a próxima imagem
  void nextSlide.offsetWidth;

  // Transição simultânea entre as imagens
  previous.classList.remove('is-active');

  current = target;

  nextSlide.classList.add('is-active');

  // Libera a próxima troca após o fade
  setTimeout(() => {
    previous.style.animation = '';
    previous.style.transform = '';
    transitioning = false;
  }, 1900);

  // Carrega antecipadamente a próxima imagem
  loadSlide((current + 1) % slides.length);

  if (counter) {
    counter.textContent = String(current + 1).padStart(2, '0');
  }
}
// Slideshow automático
function startRotation() {
  clearInterval(rotation);

  if (
    slides.length > 1 &&
    !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ) {
    rotation = setInterval(() => {
      showSlide(current + 1);
    }, 6500);
  }
}

// Menu
function setMenu(open) {
  toggle.setAttribute('aria-expanded', String(open));
  menu.classList.toggle('open', open);
  menu.setAttribute('aria-hidden', String(!open));
  backdrop.classList.toggle('show', open);
  backdrop.tabIndex = open ? 0 : -1;
  document.body.style.overflow = open ? 'hidden' : '';

  if (open) clearInterval(rotation);
  else startRotation();
}

// Eventos do menu
toggle.addEventListener('click', () => {
  setMenu(toggle.getAttribute('aria-expanded') !== 'true');
});

close.addEventListener('click', () => setMenu(false));

backdrop.addEventListener('click', () => setMenu(false));

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') setMenu(false);
});

initializeSlideshow();
