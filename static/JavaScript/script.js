/*  Manual slide
let slideIndex = 0;

function showSlides(index) {
    const slides = document.querySelectorAll('.slide');
    if (index >= slides.length) {
        slideIndex = 0;
    }
    if (index < 0) {
        slideIndex = slides.length - 1;
    }
    slides.forEach((slide, i) => {
        slide.style.transform = `translateX(${-slideIndex * 100}%)`;
    });
}

function moveSlide(n) {
    showSlides(slideIndex += n);
}

function autoSlide() {
    slideIndex++; 
    showSlides(slideIndex); 
    setTimeout(autoSlide, 3000); // Change slide every 3 seconds 
}

document.addEventListener('DOMContentLoaded', () => {
    showSlides(slideIndex);
});*/

/* Auto Slide 
let slideIndex = 0;

function showSlides(index) {
  const slides = document.querySelectorAll('.slide');
  if (index >= slides.length) {
    slideIndex = 0;
  }
  if (index < 0) {
    slideIndex = slides.length - 1;
  }
  slides.forEach((slide, i) => {
    slide.style.transform = `translateX(${-slideIndex * 100}%)`;
  });
}

function moveSlide(n) {
  showSlides(slideIndex += n);
}

function autoSlide() {
  slideIndex++;
  showSlides(slideIndex);
  setTimeout(autoSlide, 3000); // Change slide every 3 seconds
}

document.addEventListener('DOMContentLoaded', () => {
  showSlides(slideIndex);
  autoSlide();
});
*/

/* Auto Scroll
let slideIndex = 0;
function showSlides() {
  const slides = document.querySelectorAll('.slide');
  const slidesContainer = document.querySelector('.slides');
  slideIndex++;
  if (slideIndex >= slides.length) {
    slideIndex = 0;
  }
  slidesContainer.style.transform = `translateX(${-slideIndex * 100}%)`;
  setTimeout(showSlides, 5000); // Change slide every 5 seconds
}

document.addEventListener('DOMContentLoaded', () => {
  showSlides();
});*/

let slideIndex = 0;
let autoSlideTimeout;

function showSlides(index) {
  const slides = document.querySelectorAll('.slide');
  const slidesContainer = document.querySelector('.slides');
  if (!slides.length || !slidesContainer) return;

  if (index >= slides.length) {
    slideIndex = 0;
  }
  if (index < 0) {
    slideIndex = slides.length - 1;
  }
  slidesContainer.style.transform = `translateX(${-slideIndex * 100}%)`;
}

function moveSlide(n) {
  clearTimeout(autoSlideTimeout);
  slideIndex += n;
  showSlides(slideIndex);
  autoSlideTimeout = setTimeout(autoSlide, 5000);
}

function autoSlide() {
  const slides = document.querySelectorAll('.slide');
  if (!slides.length) return;
  slideIndex++;
  showSlides(slideIndex);
  autoSlideTimeout = setTimeout(autoSlide, 5000);
}

document.addEventListener('DOMContentLoaded', () => {
  showSlides(slideIndex);
  autoSlide();

  const prevSlideBtn = document.querySelector('.prev');
  const nextSlideBtn = document.querySelector('.next');
  if (prevSlideBtn) prevSlideBtn.addEventListener('click', () => moveSlide(-1));
  if (nextSlideBtn) nextSlideBtn.addEventListener('click', () => moveSlide(1));

  initPostModal();
});

function initPostModal() {
  // Remove any existing post-modal to ensure absolute consistency and clean layout
  const oldModal = document.getElementById('post-modal');
  if (oldModal) {
    oldModal.remove();
  }

  // Create and inject new premium post-modal
  const modalHtml = `
    <div id="post-modal" class="modal" aria-hidden="true">
      <div class="modal-overlay"></div>
      <div class="modal-content">
        <button class="modal-close" aria-label="Close modal">&times;</button>
        
        <div class="modal-carousel-container" id="modal-carousel">
          <div class="modal-slides-track" id="modal-slides"></div>
          <button class="modal-carousel-prev" id="modal-prev" aria-label="Previous image">&#10094;</button>
          <button class="modal-carousel-next" id="modal-next" aria-label="Next image">&#10095;</button>
          <div class="modal-carousel-counter" id="modal-counter"></div>
          <div class="modal-carousel-dots" id="modal-dots"></div>
        </div>

        <div class="modal-metadata">
          <span class="modal-category" id="modal-category"></span>
          <span class="modal-date" id="modal-date"></span>
        </div>

        <h2 id="modal-title"></h2>
        <div id="modal-text"></div>
        
        <div class="modal-footer" id="modal-footer"></div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);

  const modal = document.getElementById('post-modal');
  const overlay = modal.querySelector('.modal-overlay');
  const closeButton = modal.querySelector('.modal-close');
  const carouselContainer = document.getElementById('modal-carousel');
  const slidesTrack = document.getElementById('modal-slides');
  const prevBtn = document.getElementById('modal-prev');
  const nextBtn = document.getElementById('modal-next');
  const counter = document.getElementById('modal-counter');
  const dotsContainer = document.getElementById('modal-dots');
  const categoryEl = document.getElementById('modal-category');
  const dateEl = document.getElementById('modal-date');
  const titleEl = document.getElementById('modal-title');
  const textEl = document.getElementById('modal-text');
  const footerEl = document.getElementById('modal-footer');

  let currentImgIndex = 0;
  let postImages = [];

  function closeModal() {
    modal.classList.remove('visible');
    modal.setAttribute('aria-hidden', 'true');
  }

  function updateSlider() {
    if (postImages.length === 0) return;
    slidesTrack.style.transform = `translateX(-${currentImgIndex * 100}%)`;
    counter.textContent = `${currentImgIndex + 1} / ${postImages.length}`;

    const activeImgId = postImages[currentImgIndex];

    const dots = dotsContainer.querySelectorAll('.modal-carousel-dot');
    dots.forEach((dot, idx) => {
      if (idx === currentImgIndex) {
        dot.classList.add('active');
      } else {
        dot.classList.remove('active');
      }
    });
  }

  function openModal(title, content, category, date, imagesStr, directLink, fallbackImgSrc) {
    titleEl.textContent = title || '';
    textEl.textContent = content || '';
    categoryEl.textContent = category || 'បណ្ណសារ / Archive';

    if (date) {
      dateEl.innerHTML = `📅 <span style="margin-left: 4px;">Posted on: ${date}</span>`;
      dateEl.style.display = 'flex';
    } else {
      dateEl.style.display = 'none';
    }

    postImages = [];
    if (imagesStr && imagesStr.trim().length > 0) {
      postImages = imagesStr.split(',').map(id => id.trim()).filter(id => id !== '');
    }

    slidesTrack.innerHTML = '';
    dotsContainer.innerHTML = '';
    currentImgIndex = 0;

    if (postImages.length > 0) {
      carouselContainer.style.display = 'flex';

      postImages.forEach(imgId => {
        const slide = document.createElement('div');
        slide.className = 'modal-slide-img-wrapper';
        const img = document.createElement('img');
        img.className = 'modal-slide-img';
        img.src = `/image/${imgId}`;
        img.alt = title;
        img.onerror = () => {
          img.src = '/static/images/default.jpg';
        };
        slide.appendChild(img);
        slidesTrack.appendChild(slide);
      });

      if (postImages.length > 1) {
        prevBtn.style.display = 'flex';
        nextBtn.style.display = 'flex';
        dotsContainer.style.display = 'flex';
        counter.style.display = 'block';
        for (let i = 0; i < postImages.length; i++) {
          const dot = document.createElement('div');
          dot.className = 'modal-carousel-dot';
          if (i === 0) dot.classList.add('active');
          dot.addEventListener('click', () => {
            currentImgIndex = i;
            updateSlider();
          });
          dotsContainer.appendChild(dot);
        }
      } else {
        prevBtn.style.display = 'none';
        nextBtn.style.display = 'none';
        dotsContainer.style.display = 'none';
        counter.style.display = 'none';
      }

      updateSlider();
    } else {
      if (fallbackImgSrc) {
        carouselContainer.style.display = 'flex';
        prevBtn.style.display = 'none';
        nextBtn.style.display = 'none';
        counter.style.display = 'none';
        dotsContainer.style.display = 'none';

        const slide = document.createElement('div');
        slide.className = 'modal-slide-img-wrapper';
        const img = document.createElement('img');
        img.className = 'modal-slide-img';
        img.src = fallbackImgSrc;
        img.alt = title;
        slide.appendChild(img);
        slidesTrack.appendChild(slide);
      } else {
        carouselContainer.style.display = 'none';
      }
    }

    footerEl.innerHTML = '';
    if (directLink && directLink.trim().length > 0) {
      const dwnBtn = document.createElement('a');
      dwnBtn.href = directLink.trim();
      dwnBtn.target = '_blank';
      dwnBtn.className = 'modal-btn-download';
      dwnBtn.innerHTML = `📂 <span>ទាញយករូបភាព / Download Pictures</span>`;
      footerEl.appendChild(dwnBtn);
      footerEl.style.display = 'flex';
    } else {
      footerEl.style.display = 'none';
    }

    modal.classList.add('visible');
    modal.setAttribute('aria-hidden', 'false');
  }

  document.querySelectorAll('.post-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('a')) {
        return; // Don't trigger popup if they clicked a direct anchor link inside card
      }

      const titleNode = card.querySelector('.htitle, #titles');
      const contentNode = card.querySelector('.ellipsis-text, #text');
      const imageNode = card.querySelector('img');
      const categoryNode = card.querySelector('span[style*="background"]');

      const title = titleNode ? titleNode.textContent.trim() : '';
      const content = contentNode ? contentNode.textContent.trim() : '';
      const category = categoryNode ? categoryNode.textContent.trim() : '';
      const fallbackImgSrc = imageNode ? imageNode.src : '';

      const imagesStr = card.getAttribute('data-images') || '';
      const dateStr = card.getAttribute('data-date') || '';
      const linkStr = card.getAttribute('data-link') || '';

      openModal(title, content, category, dateStr, imagesStr, linkStr, fallbackImgSrc);
    });
  });

  prevBtn.addEventListener('click', () => {
    if (postImages.length <= 1) return;
    currentImgIndex = (currentImgIndex - 1 + postImages.length) % postImages.length;
    updateSlider();
  });

  nextBtn.addEventListener('click', () => {
    if (postImages.length <= 1) return;
    currentImgIndex = (currentImgIndex + 1) % postImages.length;
    updateSlider();
  });

  closeButton.addEventListener('click', closeModal);
  overlay.addEventListener('click', closeModal);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      closeModal();
    }
  });
}

