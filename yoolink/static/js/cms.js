// Dropzone


/*const myDropzone = new Dropzone("#my-dropzone", {
    url: ""
})*/
/* Alerts
* @Aziz (https://codepen.io/EL_Aziz/pen/qBEyvMR) - MIT
*/
function sendNotif(content = '', status = 'notice', position = 'bottom-right') {
    if ($('#notify').length) $('#notify').remove();
    $('body').append('<div id="notify" data-notification-status="' + status + '" class="do-show ' + position + '">' + content + '</div>');
}

// A $( document ).ready() block.
$(document).ready(function () {
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
