/* Alerts
* @Aziz (https://codepen.io/EL_Aziz/pen/qBEyvMR) - MIT
*/
function sendNotif(content = '', status = 'notice', position = 'bottom-right') {
    const allowedStatuses = ['notice', 'info', 'error', 'warning', 'success'];
    const allowedPositions = ['top-left', 'top-right', 'bottom-left', 'bottom-right'];
    const normalizedStatus = allowedStatuses.includes(status) ? status : 'notice';
    const normalizedPosition = allowedPositions.includes(position) ? position : 'bottom-right';

    if ($('#notify').length) $('#notify').remove();
    $('<div>', {
        id: 'notify',
        class: 'do-show ' + normalizedPosition,
        'data-notification-status': normalizedStatus,
        text: content,
    }).appendTo('body');
}
