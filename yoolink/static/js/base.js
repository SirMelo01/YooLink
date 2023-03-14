const cookie = document.querySelector("#menu-cookie");
const menu = document.querySelector("#navbar-cta");

function toggleMenu() {
  if (menu.classList.contains("hidden")) {
    menu.classList.remove("hidden");
  } else {
    menu.classList.add("hidden");
  }
}

function cookieRefresh() {
  if (
    window.location.pathname !== "/impressum.html" &&
    window.location.pathname !== "/datenschutz.html"
  ) {
    if (cookieselect == null) {
      cookie.classList.add("block");
      cookie.classList.remove("hidden");
    } else {
      cookie.classList.add("hidden");
    }
  }
}

function acceptCookie() {
  // Dauer der Cookies noch einstellen (Johannes 29.01 meint 1 Jahr)
  document.cookie =
    "Cookie-Consent=true; expires=" + new Date(9999, 0, 1).toUTCString();
  document.cookie =
    "Cookie-Map=true; expires=" + new Date(9999, 0, 1).toUTCString();
  document.cookie =
    "Cookie-Fond=true; expires=" + new Date(9999, 0, 1).toUTCString();
  location.reload();
  cookieRefresh();
}

function refuseCookie() {
  // Dauer der Cookies noch einstellen (Johannes 29.01 meint 1 Jahr)
  document.cookie =
    "Cookie-Consent=false; expires=" + new Date(9999, 0, 1).toUTCString();
  document.cookie =
    "Cookie-Map=false; expires=" + new Date(9999, 0, 1).toUTCString();
  document.cookie =
    "Cookie-Fond=false; expires=" + new Date(9999, 0, 1).toUTCString();
  location.reload();
  cookieRefresh();
}

cookieRefresh();
