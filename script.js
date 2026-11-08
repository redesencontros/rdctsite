const toggle = document.querySelector('.menu-toggle');
const menu = document.querySelector('.site-menu');
const backdrop = document.querySelector('.menu-backdrop');
const close = document.querySelector('.menu-close');
const slides = [...document.querySelectorAll('.slide')];
const counter = document.querySelector('.slide-counter b');
let current = 0;
let rotation;

function setMenu(open){
  toggle.setAttribute('aria-expanded', String(open));
  menu.classList.toggle('open', open);
  menu.setAttribute('aria-hidden', String(!open));
  backdrop.classList.toggle('show', open);
  backdrop.tabIndex = open ? 0 : -1;
  document.body.style.overflow = open ? 'hidden' : '';
  if(open) clearInterval(rotation);
  else startRotation();
}
function showSlide(next){
  slides[current].classList.remove('is-active');
  current = next % slides.length;
  slides[current].classList.add('is-active');
  if(counter) counter.textContent = String(current + 1).padStart(2, '0');
}
function startRotation(){
  clearInterval(rotation);
  if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    rotation = setInterval(() => showSlide(current + 1), 6500);
  }
}
toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
close.addEventListener('click', () => setMenu(false));
backdrop.addEventListener('click', () => setMenu(false));
document.addEventListener('keydown', event => { if(event.key === 'Escape') setMenu(false); });
startRotation();

/*
Para usar vídeos, adicione um elemento <video class="slide"> com autoplay muted loop playsinline
e substitua a lógica de fundo correspondente. A versão inicial usa fotografias para manter
o carregamento leve e demonstrar a troca automática.
*/
