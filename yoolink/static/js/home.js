var currentSlideId = 1;
var sliderElement = document.getElementById("slider");
var totalSlides = sliderElement.childElementCount;
let myInterval = setInterval(next, 7000);

const browser = document.querySelector("#browser");
const phone = document.querySelector("#phone");

const content1 = document.querySelector("#content1");
const arrow1 = document.querySelector("#arrow1");
const content2 = document.querySelector("#content2");
const arrow2 = document.querySelector("#arrow2");
const content3 = document.querySelector("#content3");
const arrow3 = document.querySelector("#arrow3");
const content4 = document.querySelector("#content4");
const arrow4 = document.querySelector("#arrow4");

//Responsive Design

function toggleResponsive() {
  if (phone.classList.contains("hidden")) {
    browser.classList.add("hidden");
    phone.classList.remove("hidden");
  } else {
    browser.classList.remove("hidden");
    phone.classList.add("hidden");
  }
}

//FQA
function toggleFaq1() {
  if (content1.classList.contains("hidden")) {
    content1.classList.remove("hidden");
    arrow1.classList.add("rotate-180");
  } else {
    content1.classList.add("hidden");
    arrow1.classList.remove("rotate-180");
  }
}
function toggleFaq2() {
  if (content2.classList.contains("hidden")) {
    content2.classList.remove("hidden");
    arrow2.classList.add("rotate-180");
  } else {
    content2.classList.add("hidden");
    arrow2.classList.remove("rotate-180");
  }
}

function toggleFaq3() {
  if (content3.classList.contains("hidden")) {
    content3.classList.remove("hidden");
    arrow3.classList.add("rotate-180");
  } else {
    content3.classList.add("hidden");
    arrow3.classList.remove("rotate-180");
  }
}

function toggleFaq4() {
  if (content4.classList.contains("hidden")) {
    content4.classList.remove("hidden");
    arrow4.classList.add("rotate-180");
  } else {
    content4.classList.add("hidden");
    arrow4.classList.remove("rotate-180");
  }
}
// Image slider
function next() {
  if (currentSlideId < totalSlides) {
    currentSlideId++;
    showSlide();
  } else {
    currentSlideId = 1;
    showSlide();
  }
  clearInterval(myInterval);
  myInterval = setInterval(next, 7000);
}

function prev() {
  if (currentSlideId > 1) {
    currentSlideId--;
    showSlide();
  } else {
    currentSlideId = totalSlides;
    showSlide();
  }
  clearInterval(myInterval);
  myInterval = setInterval(next, 7000);
}

function showSlide() {
  slides = document.getElementById("slider").getElementsByTagName("img");
  for (let index = 0; index < totalSlides; index++) {
    const element = slides[index];
    if (currentSlideId == index + 1) {
      element.classList.add("animate-fade-in-down");
      element.classList.remove("hidden");
    } else {
      element.classList.add("hidden");
      element.classList.remove("animate-fade-in-down");
    }
  }
}
