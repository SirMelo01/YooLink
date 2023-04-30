var font1 = document.createElement("link");
font1.rel = "preconnect";
font1.href = "https://fonts.googleapis.com";

var font2 = document.createElement("link");
font2.rel = "preconnect";
font2.href = "https://fonts.gstatic.com";
font2.crossOrigin = "";

var font3 = document.createElement("link");
font3.href = "https://fonts.googleapis.com/css2?family=Roboto&display=swap";
font3.rel = "stylesheet";

var analytic1 = document.createElement("script");
analytic1.async = "";
analytic1.src = "https://www.googletagmanager.com/gtag/js?id=G-ZYQPVZ3REE";

var analytic2 = document.createElement("script");
analytic2.innerHTML = "window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} gtag('js', new Date()); gtag('config', 'G-ZYQPVZ3REE');";


var cookieselect = getCookie("Cookie-Consent");
var cookiefontselect = getCookie("Cookie-Font");
var cookieanalyticselect = getCookie("Cookie-Analytic")

if(cookiefontselect === "true"){
  document.head.appendChild(font1);
  document.head.appendChild(font2);
  document.head.appendChild(font3);
}
setTimeout(function(){
  if(cookieanalyticselect === "true"){
    document.body.insertBefore(analytic1, document.body.firstChild);
    document.body.insertBefore(analytic2, document.body.firstChild);
  }
},2000)



//Cookies raussuchen per Name
function getCookie(name) {
  // Split cookie string and get all individual name=value pairs in an array
  var cookieArr = document.cookie.split(";");
  // Loop through the array elements
  for (var i = 0; i < cookieArr.length; i++) {
    var cookiePair = cookieArr[i].split("=");
    /* Removing whitespace at the beginning of the cookie name
        and compare it with the given string */
    if (name == cookiePair[0].trim()) {
      // Decode the cookie value and return
      return decodeURIComponent(cookiePair[1]);
    }
  }
  return null;
}
