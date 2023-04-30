var form = document.querySelector("form");
var cookieslider = document.getElementById("cookie");
var analyticslider = document.getElementById("analytics");
var fontslider = document.getElementById("font");

function cookiereload2() {
  if (cookieslider.checked === true) {
    document.cookie =
      "Cookie-Consent=true; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  } else {
    document.cookie =
      "Cookie-Consent=false; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  }

  if (analyticslider.checked === true) {
    document.cookie =
      "Cookie-Analytic=true; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  } else {
    document.cookie =
      "Cookie-Analytic=false; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  }

  if (fontslider.checked === true) {
    document.cookie =
      "Cookie-Font=true; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  } else {
    document.cookie =
      "Cookie-Font=false; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  }
}

onload = function () {
  if (cookieselect === "true") {
    cookieslider.checked = true;
  }

  if (cookieanalyticselect === "true") {
    analyticslider.checked = true;
  }

  if (cookiefontselect === "true") {
    fontslider.checked = true;
  }
};

cookieslider.addEventListener("change", (e) => {
  if (cookieslider.checked === true) {
    analyticslider.checked = true;
    fontslider.checked = true;
  } else {
    analyticslider.checked = false;
    fontslider.checked = false;
  }
  cookiereload2();
});

analyticslider.addEventListener("change", (e) => {
  if (analyticslider.checked === true) {
    if (fontslider.checked === true) {
      cookieslider.checked = true;
    }
  } else {
    cookieslider.checked = false;
  }
  cookiereload2();
});

fontslider.addEventListener("change", (e) => {
  if (fontslider.checked === true) {
    if (analyticslider.checked === true) {
      cookieslider.checked = true;
    }
  } else {
    cookieslider.checked = false;
  }
  cookiereload2();
});