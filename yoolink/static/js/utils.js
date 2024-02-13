/* Alerts
* @Aziz (https://codepen.io/EL_Aziz/pen/qBEyvMR) - MIT
*/
function sendNotif(content = '', status = 'notice', position = 'bottom-right') {
    if ($('#notify').length) $('#notify').remove();
    $('body').append('<div id="notify" data-notification-status="' + status + '" class="do-show ' + position + '">' + content + '</div>');
}