// Load images from backend
$editImg = null;
$editSlider = null;
$editVideo = null;
let imageLibraryItems = [];

$(document).ready(function () {
    const $imageModal = $('#imageModal');
    const $galeryModal = $('#galeryModal');
    const $videoModal = $('#videoModal');
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

    $('.edit-img').click(function () {
        $editImg = $(this).siblings('img');
        openImageModal();
    });

    $('#closeImageModal').click(function () {
        closeImageModal();
    });

    $('#reloadImages').click(function () {
        loadImages(true);
    });

    $('#imageSearchInput').on('input', function () {
        renderImageLibrary(imageLibraryItems);
    });

    $('.image-modal-tab').click(function () {
        setImageModalTab($(this).attr('data-target'));
    });

    $('#imageUploadDropzone').click(function (event) {
        if (event.target.id === 'imageUploadInput') return;
        $('#imageUploadInput')[0].click();
    });

    $('#imageUploadInput').click(function (event) {
        event.stopPropagation();
    });

    $('#imageUploadInput').on('change', function () {
        uploadImageFiles(this.files, csrfToken);
        this.value = '';
    });

    $('#imageUploadDropzone').on('dragover', function (event) {
        event.preventDefault();
        $(this).addClass('border-blue-500 bg-blue-100');
    });

    $('#imageUploadDropzone').on('dragleave drop', function () {
        $(this).removeClass('border-blue-500 bg-blue-100');
    });

    $('#imageUploadDropzone').on('drop', function (event) {
        event.preventDefault();
        uploadImageFiles(event.originalEvent.dataTransfer.files, csrfToken);
    });

    $('#reloadGalerien').click(function () {
        loadGalerien(true);
    });

    $('#closeGaleryModal').click(function () {
        $galeryModal.addClass("hidden");
    });

    $('.edit-galery').click(function () {
        $editSlider = $(this).siblings('.carousel');
        $galeryModal.removeClass("hidden");
    });

    const $modals = [$imageModal, $galeryModal, $videoModal];
    const $modalContainers = $modals.map($m => $m.find('.modal-container'));

    $(document).mouseup(function (e) {
        if ($(e.target).closest('.swal2-container').length > 0) return;

        let clickedOutsideAll = true;
        for (const $container of $modalContainers) {
            if ($container.is(e.target) || $container.has(e.target).length > 0) {
                clickedOutsideAll = false;
                break;
            }
        }

        if (clickedOutsideAll) {
            closeImageModal();
            $galeryModal.addClass('hidden');
            $videoModal.addClass('hidden');
        }
    });

    $('.edit-video').click(function () {
        $editVideo = $(this).siblings('video');
        $videoModal.removeClass('hidden');
    });

    $('#closeVideoModal').click(function () {
        $videoModal.addClass('hidden');
    });

    $('#reloadVideos').click(function () {
        loadVideos(true);
    });
});

function openImageModal() {
    refreshSelectedImagePreview();
    setImageModalTab('imageLibraryPanel');
    $('#imageModal').removeClass("hidden").addClass("flex");
}

function closeImageModal() {
    $('#imageModal').addClass("hidden").removeClass("flex");
}

function setImageModalTab(panelId) {
    $('.image-modal-panel').addClass('hidden').removeClass('flex');
    $('#' + panelId).removeClass('hidden').addClass('flex');

    $('.image-modal-tab')
        .removeClass('bg-blue-900 text-white shadow-sm')
        .addClass('text-slate-700 hover:bg-white hover:text-slate-950');

    $('.image-modal-tab[data-target="' + panelId + '"]')
        .addClass('bg-blue-900 text-white shadow-sm')
        .removeClass('text-slate-700 hover:bg-white hover:text-slate-950');
}

function refreshSelectedImagePreview() {
    const src = $editImg ? $editImg.attr('src') : '';
    if (src) {
        $('#selectedImagePreview').attr('src', src).removeClass('hidden');
        $('#selectedImagePlaceholder').addClass('hidden');
    } else {
        $('#selectedImagePreview').attr('src', '').addClass('hidden');
        $('#selectedImagePlaceholder').removeClass('hidden');
    }
}

function selectImage($image) {
    if (!$editImg) return;

    $editImg.attr('src', $image.attr('src'));
    $editImg.attr('imgId', $image.attr('imgId'));
    closeImageModal();
    sendNotif('Neues Bild ausgewählt', 'success');
}

function renderImageLibrary(images) {
    const search = ($('#imageSearchInput').val() || '').toLowerCase().trim();
    const filteredImages = images.filter(function (image) {
        return !search || (image.title || '').toLowerCase().includes(search);
    });

    const $container = $('#possibleImages');
    $container.empty();

    filteredImages.forEach(function (image) {
        const title = escapeHtml(image.title || 'Bild');
        const $button = $(`
            <button type="button" class="group relative overflow-hidden rounded-lg bg-white text-left shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-0.5 hover:shadow-lg hover:ring-blue-300">
                <img src="${image.url}" imgId="${image.id}" alt="${title}" class="h-36 w-full object-cover">
                <span class="absolute right-2 top-2 rounded-md bg-white/90 px-2 py-1 text-xs font-semibold text-red-700 opacity-0 shadow-sm ring-1 ring-red-100 transition hover:bg-red-50 group-hover:opacity-100 image-delete-button" data-image-id="${image.id}">
                    <i class="bi bi-trash"></i>
                </span>
                <span class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/80 to-transparent px-3 pb-3 pt-8 text-xs font-semibold text-white opacity-0 transition group-hover:opacity-100">${title}</span>
            </button>
        `);
        $button.click(function () {
            selectImage($(this).find('img'));
        });
        $button.find('.image-delete-button').click(function (event) {
            event.preventDefault();
            event.stopPropagation();
            confirmDeleteImage(image.id, title);
        });
        $container.append($button);
    });

    $('#imageEmptyState').toggleClass('hidden', filteredImages.length > 0);
}

function confirmDeleteImage(imageId, title) {
    const confirmText = 'Dieses Bild wird dauerhaft gelöscht.';
    const confirmAction = function () {
        deleteImage(imageId);
    };

    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Bild löschen?',
            text: confirmText,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc2626',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Ja, löschen',
            cancelButtonText: 'Abbrechen',
            reverseButtons: true,
        }).then(function (result) {
            if (result.isConfirmed) confirmAction();
        });
        return;
    }

    if (window.confirm(title + ' löschen?\n\n' + confirmText)) {
        confirmAction();
    }
}

function deleteImage(imageId) {
    $.ajax({
        url: '/cms/images/delete/' + imageId + '/',
        type: 'POST',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', $('input[name="csrfmiddlewaretoken"]').val());
        },
        success: function (response) {
            imageLibraryItems = imageLibraryItems.filter(function (image) {
                return String(image.id) !== String(imageId);
            });
            renderImageLibrary(imageLibraryItems);

            if ($editImg && String($editImg.attr('imgId')) === String(imageId)) {
                $editImg.attr('imgId', '-1');
                refreshSelectedImagePreview();
            }

            sendNotif(response.success || 'Bild wurde gelöscht', 'success');
        },
        error: function () {
            sendNotif('Bild konnte nicht gelöscht werden', 'error');
        }
    });
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function uploadImageFiles(fileList, csrfToken) {
    const files = Array.from(fileList || []).filter(function (file) {
        return file.type && file.type.startsWith('image/');
    });

    if (!files.length) {
        sendNotif('Bitte wähle eine Bilddatei aus', 'error');
        return;
    }

    $('#imageUploadQueue').removeClass('hidden');

    files.forEach(function (file) {
        const itemId = 'upload-' + Date.now() + '-' + Math.random().toString(16).slice(2);
        addUploadItem(itemId, file.name);

        const formData = new FormData();
        formData.append('file', file);

        $.ajax({
            url: '/cms/upload/post',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
            },
            success: function (response) {
                setUploadItemStatus(itemId, 'Fertig', 'text-green-700');
                if (response.image) {
                    imageLibraryItems.unshift(response.image);
                    renderImageLibrary(imageLibraryItems);
                    setImageModalTab('imageLibraryPanel');
                } else {
                    loadImages(false);
                }
                sendNotif('Bild wurde hochgeladen', 'success');
            },
            error: function () {
                setUploadItemStatus(itemId, 'Fehlgeschlagen', 'text-red-700');
                sendNotif('Bild konnte nicht hochgeladen werden', 'error');
            }
        });
    });
}

function addUploadItem(id, name) {
    $('#imageUploadItems').prepend(`
        <div id="${id}" class="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
            <span class="truncate pr-3 text-slate-700">${name}</span>
            <span class="upload-status text-slate-500">Lädt...</span>
        </div>
    `);
}

function setUploadItemStatus(id, text, className) {
    $('#' + id).find('.upload-status')
        .removeClass('text-slate-500 text-green-700 text-red-700')
        .addClass(className)
        .text(text);
}

function loadImages(sendLoadMsg) {
    $.ajax({
        url: '/cms/images/all/',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            imageLibraryItems = response.image_urls || [];
            renderImageLibrary(imageLibraryItems);
            if (sendLoadMsg) {
                const message = imageLibraryItems.length ? 'Alle Bilder wurden geladen' : 'Keine Bilder wurden gefunden';
                sendNotif(message, imageLibraryItems.length ? 'success' : 'error');
            }
        },
        error: function () {
            if (sendLoadMsg) sendNotif('Es kam zu einem unerwarteten Fehler, versuche es später nochmal', 'error');
        }
    });
}

function loadGalerien(sendLoadMsg) {
    $.ajax({
        url: '/cms/galerien/all/',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            if (response.galerien && response.galerien.length !== 0) {
                $('#possibleGalerien').empty();
                response.galerien.forEach(function (gallery) {
                    const $galleryItem = addTitleAndDescription(gallery.title, gallery.description, gallery.id);
                    $galleryItem.click(function () {
                        const galeryId = $(this).attr("galeryId");
                        sendNotif("Diese Galerie wird geladen...", "notice");
                        selectGalery(galeryId);
                    });
                    $('#possibleGalerien').append($galleryItem);
                });
                if (sendLoadMsg) sendNotif("Alle Galerien wurden geladen", "success");
            } else {
                if (sendLoadMsg) sendNotif("Es wurden keine Galerien gefunden", "error");
            }
        },
        error: function () {
            if (sendLoadMsg) sendNotif("Es kam zu einem unerwarteten Fehler, versuche es später nochmal", "error");
        }
    });
}

function loadVideos(sendLoadMsg) {
    $.ajax({
        url: '/cms/videos/all/',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            if (response.video_urls && response.video_urls.length !== 0) {
                $('#possibleVideos').empty();
                response.video_urls.forEach(function (v) {
                    const $elem = $(`
                        <video
                            src="${v.url}"
                            poster="${v.poster}"
                            videoId="${v.id}"
                            class="h-40 w-full rounded-xl hover:shadow-2xl hover:cursor-pointer hover:scale-105"
                            preload="metadata">
                        </video>`
                    );

                    $elem.click(function () {
                        if ($editVideo) {
                            $editVideo.attr('src', $(this).attr('src'));
                            $editVideo.attr('poster', $(this).attr('poster'));
                            $editVideo.attr('videoId', $(this).attr('videoId'));
                            $('#videoModal').addClass('hidden');
                            sendNotif('Neues Video ausgewählt', 'success');
                        }
                    });

                    $('#possibleVideos').append($elem);
                });
                if (sendLoadMsg) sendNotif('Alle Videos wurden geladen', 'success');
            } else {
                if (sendLoadMsg) sendNotif('Keine Videos gefunden', 'error');
            }
        },
        error: function () {
            if (sendLoadMsg) sendNotif('Unerwarteter Fehler beim Laden der Videos', 'error');
        }
    });
}

function addTitleAndDescription(title, description, id) {
    const $div = $('<div>').addClass('border border-gray-200 shadow-xl rounded-2xl h-full w-full p-4 hover:cursor-pointer hover:shadow-blue-300');
    $div.attr('galeryId', id);
    const $title = $('<h1>').addClass('text-xl font-semibold mb-2').text(title);
    const $description = $('<p>').addClass('max-h-[8rem] overflow-auto').text(description);

    $div.append($title);
    $div.append($description);

    return $div;
}

function selectGalery(id) {
    $.ajax({
        url: "/cms/galery/getImages/",
        type: "GET",
        data: { "galeryId": id },
        dataType: "json",
        success: function (data) {
            if (data.images.length > 0) {
                const c = $editSlider.find('.slick-slide:not(.slick-cloned)');
                for (let i = c.length - 1; i >= 0; i--) {
                    $editSlider.slick("slickRemove", i);
                }
                const height = $('#galeryHeight').val();
                const width = $('#galeryWidth').val();
                data.images.forEach(function (image) {
                    const img = '<img src="' + image.upload_url + '" class="w-full rounded-xl" style="height: ' + height + '; width: ' + width + '">';
                    $editSlider.slick('slickAdd', '<div>' + img + '</div>');
                });
                $editSlider.closest(".relative").attr('galery-id', id);
                $('#galeryModal').addClass("hidden");
                sendNotif("Galerie wurde erfolgreich geladen", "success");
            } else {
                sendNotif("Diese Galerie ist leer. Bitte befülle sie erst!", "error");
            }
        },
        error: function (xhr, status, error) {
            console.error("Error:", error);
            sendNotif("Etwas hat nicht funktioniert. Versuche es später erneut", "error");
        }
    });
}
