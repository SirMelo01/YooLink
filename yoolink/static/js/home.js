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

const responsive = document.querySelector("#Responsive");

//Responsive Design


//hier noch magin ändern 
function toggleResponsive() {
  if (phone.classList.contains("hidden")) {
    responsive.classList.remove("xs:-mb-48");
    browser.classList.add("hidden");
    phone.classList.remove("hidden");
  } else {
    responsive.classList.add("xs:-mb-48");
    browser.classList.remove("hidden");
    phone.classList.add("hidden");
  }
}

//FQA
$(document).ready(function() {
  $(".faq-toggle").click(function() {
    var content = $(this).siblings(".faq-content");
    var arrow = $(this).find(".faq-arrow");
    
    if (content.hasClass("hidden")) {
      content.removeClass("hidden");
      arrow.addClass("rotate-180");
    } else {
      content.addClass("hidden");
      arrow.removeClass("rotate-180");
    }
  });
});

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
