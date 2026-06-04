// Dropzone


/*const myDropzone = new Dropzone("#my-dropzone", {
    url: ""
})*/
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

// A $( document ).ready() block.
$(document).ready(function () {
    $('#mobile-menu-button')
        .off('click.yoolinkMobileMenu')
        .on('click.yoolinkMobileMenu', function (event) {
            event.preventDefault();
            const $menu = $('#mobile-menu');
            const isOpening = $menu.hasClass('hidden');

            $menu.toggleClass('hidden', !isOpening);
            $('#mobile-menu-open-icon').toggleClass('hidden', isOpening);
            $('#mobile-menu-close-icon').toggleClass('hidden', !isOpening);
            $(this).attr('aria-expanded', String(isOpening));
        });

    $('#user-menu-button')
        .off('click.yoolinkUserMenu')
        .on('click.yoolinkUserMenu', function (event) {
            event.preventDefault();
            event.stopPropagation();

            var userDropDown = $('#userDropDown');
            var isOpening = userDropDown.hasClass('hidden');
            userDropDown.toggleClass('hidden');
            $(this).attr('aria-expanded', String(isOpening));
        });

    $(document).off('click.yoolinkUserMenu').on('click.yoolinkUserMenu', function (event) {
        var target = event.target;
        var userDropDown = $('#userDropDown');
        var userMenuButton = $('#user-menu-button');

        if (
            !userDropDown.is(target) &&
            !userMenuButton.is(target) &&
            userDropDown.has(target).length === 0 &&
            userMenuButton.has(target).length === 0
        ) {
            userDropDown.addClass('hidden');
            userMenuButton.attr('aria-expanded', 'false');
        }
    });
});
