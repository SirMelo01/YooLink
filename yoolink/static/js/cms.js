const cmstab1 = document.querySelector("#cmstab1");
const cmstab2 = document.querySelector("#cmstab2");
const cmstab3 = document.querySelector("#cmstab3");
const cmstab4 = document.querySelector("#cmstab4");

const tabcontent1 = document.querySelector("#cmscontent1");
const tabcontent2 = document.querySelector("#cmscontent2");
const tabcontent3 = document.querySelector("#cmscontent3");
const tabcontent4 = document.querySelector("#cmscontent4");

function togtab1() {
    tabcontent1.classList.remove("hidden");
    tabcontent2.classList.add("hidden");
    tabcontent3.classList.add("hidden");
    tabcontent4.classList.add("hidden");
    cmstab1.classList.add("text-blue-700");
    cmstab1.classList.add("border-blue-700");
    cmstab2.classList.remove("text-blue-700");
    cmstab2.classList.remove("border-blue-700");
    cmstab3.classList.remove("text-blue-700");
    cmstab3.classList.remove("border-blue-700");
    cmstab4.classList.remove("text-blue-700");
    cmstab4.classList.remove("border-blue-700");
    
}

function togtab2() {
    tabcontent1.classList.add("hidden");
    tabcontent2.classList.remove("hidden");
    tabcontent3.classList.add("hidden");
    tabcontent4.classList.add("hidden");
    cmstab1.classList.remove("text-blue-700");
    cmstab1.classList.remove("border-blue-700");
    cmstab2.classList.add("text-blue-700");
    cmstab2.classList.add("border-blue-700");
    cmstab3.classList.remove("text-blue-700");
    cmstab3.classList.remove("border-blue-700");
    cmstab4.classList.remove("text-blue-700");
    cmstab4.classList.remove("border-blue-700");
}

function togtab3() {
    tabcontent1.classList.add("hidden");
    tabcontent2.classList.add("hidden");
    tabcontent3.classList.remove("hidden");
    tabcontent4.classList.add("hidden");
    cmstab1.classList.remove("text-blue-700");
    cmstab1.classList.remove("border-blue-700");
    cmstab2.classList.remove("text-blue-700");
    cmstab2.classList.remove("border-blue-700");
    cmstab3.classList.add("text-blue-700");
    cmstab3.classList.add("border-blue-700");
    cmstab4.classList.remove("text-blue-700");
    cmstab4.classList.remove("border-blue-700");
}

function togtab4() {
    tabcontent1.classList.add("hidden");
    tabcontent2.classList.add("hidden");
    tabcontent3.classList.add("hidden");
    tabcontent4.classList.remove("hidden");
    cmstab1.classList.remove("text-blue-700");
    cmstab1.classList.remove("border-blue-700");
    cmstab2.classList.remove("text-blue-700");
    cmstab2.classList.remove("border-blue-700");
    cmstab3.classList.remove("text-blue-700");
    cmstab3.classList.remove("border-blue-700");
    cmstab4.classList.add("text-blue-700");
    cmstab4.classList.add("border-blue-700");
}