let teamImageLibraryItems = [];

$(document).ready(function () {
    let memberIdToDelete = null;
    const $imageModal = $('#imageModal');
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

    $('#closeImageModal').click(function () {
        closeTeamImageModal();
    });

    $('#reloadImages').click(function () {
        loadImages(true);
    });

    $('#bImageSelect').click(function () {
        refreshTeamSelectedImagePreview();
        setTeamImageModalTab('imageLibraryPanel');
        $imageModal.removeClass("hidden").addClass("flex");
    });

    $('#imageSearchInput').on('input', function () {
        renderTeamImageLibrary(teamImageLibraryItems);
    });

    $('.image-modal-tab').click(function () {
        setTeamImageModalTab($(this).attr('data-target'));
    });

    $('#imageUploadDropzone').click(function (event) {
        if (event.target.id === 'imageUploadInput') return;
        $('#imageUploadInput')[0].click();
    });

    $('#imageUploadInput').click(function (event) {
        event.stopPropagation();
    });

    $('#imageUploadInput').on('change', function () {
        uploadTeamImageFiles(this.files, csrfToken);
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
        uploadTeamImageFiles(event.originalEvent.dataTransfer.files, csrfToken);
    });

    const $imageModalContainer = $imageModal.find('.modal-container');

    $(document).mouseup(function (e) {
        if ($(e.target).closest('.swal2-container').length > 0) return;

        if (
            !$imageModalContainer.is(e.target) &&
            $imageModalContainer.has(e.target).length === 0
        ) {
            closeTeamImageModal();
        }
    });

    // Funktion zum Erstellen eines neuen Teammitglieds
    $('#bCreateNewMember').click(function () {
        $('#teamMemberForm')[0].reset();  // Formular zurücksetzen
        $('#memberId').val('');  // Member ID löschen
        $('#modalTitle').text('Neues Teammitglied erstellen');
        $('#teamMemberModal').find('button[type="submit"]').text('Erstellen');
        $('#imagePreview').attr('src', '').addClass('hidden');  // Bildvorschau zurücksetzen
        $('#teamMemberModal').removeClass('hidden');  // Modal anzeigen
    });

    // Funktion zum Bearbeiten eines bestehenden Teammitglieds
    $('.edit-member').click(function () {
        const memberId = $(this).siblings('.member-id').text().trim();

        openEditModal(memberId);
    });

    // AJAX-Request zum Erstellen oder Aktualisieren eines Teammitglieds
    $('#teamMemberForm').submit(function (event) {
        event.preventDefault();

        const memberId = $('#memberId').val();
        const isNewMember = !memberId;
        const url = isNewMember ? 'create/' : `${memberId}/update/`;
        const method = isNewMember ? 'POST' : 'PUT';

        const formData = {
            'full_name': $('#full_name').val(),
            'position': $('#position').val(),
            'years_with_team': $('#years_with_team').val(),
            'age': $('#age').val(),
            'email': $('#email').val(),
            'note': $('#notes').val(),
            'active': $('#activeSwitch').is(':checked'),
            'image': $('#imagePreview').attr('src'),
            'csrfmiddlewaretoken': csrfToken
        };

        $.ajax({
            url: url,
            type: method,
            data: formData,
            beforeSend: function (xhr) {
                // Add the CSRF token to the request headers
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (response) {
                sendNotif(response.success || 'Daten erfolgreich verarbeitet', "success");
                $('#teamMemberModal').addClass('hidden');

                if (isNewMember) {
                    const newId = response.member_id;

                    const statusText = formData.active ? 'Aktiv' : 'Inaktiv';
                    const statusClass = formData.active ? 'bg-green-600' : 'bg-orange-600';

                    const newMemberHtml = `
                        <div class="relative text-center flex flex-col justify-center items-center w-fit team-card"
                            data-member-id="${newId}">

                            <!-- Drag Handle -->
                            <div class="absolute top-2 left-2 z-10 cursor-move drag-handle bg-white/90 rounded px-2 py-1 shadow text-sm">
                            ⇅
                            </div>

                            <!-- Hidden ID Element -->
                            <span class="member-id hidden">${newId}</span>

                            <div class="relative">
                            <span class="member-status absolute top-2 left-10 ${statusClass} text-white rounded-full px-2 py-0.5 cursor-pointer">
                                ${statusText}
                            </span>

                            <span class="absolute top-2 right-2 bg-red-600 text-white rounded-full px-2 py-0.5 cursor-pointer delete-member">
                                X
                            </span>

                            <img src="${formData.image || ''}" alt="${formData.full_name}" class="rounded-tl-2xl rounded-br-2xl h-80" />
                            </div>

                            <h3 class="mt-4 text-xl font-semibold text-gray-800">${formData.full_name}</h3>
                            <p class="text-blue-600">${formData.position || ''}</p>
                            <p class="text-gray-500 mt-2">Dabei seit ${formData.years_with_team || 0}</p>

                            <button class="mt-4 bg-blue-500 text-white px-4 py-2 rounded edit-member">
                            Verwalten
                            </button>
                        </div>
                        `;

                    // ✅ an die richtige Grid-ID anhängen
                    $('#teamSortableGrid').append(newMemberHtml);

                    // ✅ Events für den neu hinzugefügten Member binden
                    const $newCard = $(`#teamSortableGrid .team-card[data-member-id="${newId}"]`);

                    $newCard.find('.edit-member').on('click', function () {
                        openEditModal(newId);
                    });

                    $newCard.find('.delete-member').on('click', function () {
                        memberIdToDelete = newId;
                        $('#confirmDeleteModal').removeClass('hidden');
                    });
                } else {
                    // Aktualisiere die vorhandenen Daten ohne Neuladen
                    const $card = $(`.team-card[data-member-id="${memberId}"]`);

                    $card.find('img').attr('src', formData.image);
                    $card.find('h3').text(formData.full_name);
                    $card.find('.text-blue-600').text(formData.position);
                    $card.find('.text-gray-500').text(`Dabei seit ${formData.years_with_team}`);

                    $card.find('.member-status')
                        .text(formData.active ? 'Aktiv' : 'Inaktiv')
                        .removeClass('bg-green-600 bg-orange-600')
                        .addClass(formData.active ? 'bg-green-600' : 'bg-orange-600');
                }
            },
            error: function (error) {
                sendNotif(error.responseJSON.error || 'Fehler beim Speichern der Daten.', "error");
            }
        });
    });

    // Klick-Event für das Löschen-Symbol (X)
    $('.delete-member').click(function () {
        memberIdToDelete = $(this).closest('div').siblings('.member-id').text().trim();
        $('#confirmDeleteModal').removeClass('hidden');  // Bestätigungs-Modal anzeigen
    });

    // Klick-Event für Bestätigungs-Button im Bestätigungs-Modal
    $('#bConfirmDelete').click(function () {
        if (memberIdToDelete) {
            $.ajax({
                url: `${memberIdToDelete}/delete/`,
                type: 'DELETE',
                headers: { 'X-CSRFToken': csrfToken },
                success: function (response) {
                    sendNotif(response.success || 'Teammitglied erfolgreich gelöscht', "success");
                    $('#confirmDeleteModal').addClass('hidden');

                    // Entferne das gelöschte Teammitglied aus der Ansicht
                    const $memberDiv = $(`.member-id:contains(${memberIdToDelete})`).closest('.relative');
                    $memberDiv.remove();
                },
                error: function () {
                    sendNotif('Fehler beim Löschen des Teammitglieds', "error");
                    $('#confirmDeleteModal').addClass('hidden');
                }
            });
        }
    });

    // Funktion, um das Create-Modal zu schließen, wenn außerhalb geklickt wird und Image-Modal nicht sichtbar ist
    function closeModalOnClickOutside(event) {
        const teamMemberModal = document.getElementById('teamMemberModal');
        const imageModal = document.getElementById('imageModal');

        // Überprüfen, ob der Klick außerhalb des Modals und das Image-Select-Modal nicht sichtbar ist
        if (event.target === teamMemberModal && imageModal.classList.contains('hidden')) {
            closeModal();
        }
    }

    function closeModal() {
        document.getElementById('teamMemberModal').classList.add('hidden');
    }

    // Klick-Event für den Abbrechen-Button im Bestätigungs-Modal
    $('#bDeclineDelete').click(function () {
        $('#confirmDeleteModal').addClass('hidden');  // Bestätigungs-Modal schließen
        memberIdToDelete = null;  // memberId zurücksetzen
    });


    // SORTABLE
    let pendingTeamOrder = null; // merkt sich neue Reihenfolge, bis gespeichert
    const $saveOrderBtn = $('#bSaveTeamOrder');

    const grid = document.getElementById('teamSortableGrid');

    if (grid) {
        new Sortable(grid, {
            animation: 150,
            handle: '.drag-handle',
            draggable: '.team-card',
            onEnd: function () {
                // nur merken, NICHT speichern
                pendingTeamOrder = Array.from(grid.querySelectorAll('.team-card'))
                    .map(el => el.getAttribute('data-member-id'));

                // Save-Button aktivieren
                $saveOrderBtn.prop('disabled', false);
            }
        });
    }

    // Save per Klick
    $saveOrderBtn.on('click', function (e) {
        e.preventDefault();

        if (!pendingTeamOrder || pendingTeamOrder.length === 0) {
            sendNotif('Keine Änderungen zum Speichern', 'error');
            return;
        }

        $saveOrderBtn.prop('disabled', true);

        $.ajax({
            url: '/cms/team/reorder/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ order: pendingTeamOrder }),
            beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function () {
                sendNotif('Sortierung gespeichert', 'success');
                pendingTeamOrder = null; // Änderungen „verbraucht“
            },
            error: function (xhr) {
                console.error(xhr.responseText);
                sendNotif('Fehler beim Speichern der Sortierung', 'error');
                // Button wieder aktiv lassen, damit man nochmal speichern kann
                $saveOrderBtn.prop('disabled', false);
            }
        });
    });

    loadImages(false);
});

// Modal schließen
function closeModal() {
    $('#teamMemberModal').addClass('hidden');
}

/**
 * Loads images into <possibleImages> div
 * and on click to placeId
 * @param {string} placeId 
 * @param {boolean} sendLoadMsg 
 */
function loadImages(sendLoadMsg) {
    $.ajax({
        url: '/cms/images/all/',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            // Erfolgreiche Anfrage
            if (response.image_urls && response.image_urls.length != 0) {
                const $imagePreview = $('#imagePreview')
                $('#possibleImages').empty()
                response.image_urls.forEach(function (url) {
                    const $elem = $('<img src="' + url.url + '" imgId="' + url.id + '" class="h-28 w-full rounded-2xl col-span-1 mb-4 hover:shadow-2xl hover:cursor-pointer hover:scale-105">')
                    // Add Event Handler for selection
                    $elem.click(function () {
                        if ($imagePreview) {
                            $imagePreview.attr('src', $(this).attr('src'));
                            $imagePreview.attr('imgId', $(this).attr('imgId'))
                            $('#imageModal').toggleClass("hidden");
                            $($imagePreview).removeClass("hidden");
                            sendNotif('Neues Bild ausgewählt', 'success');
                        }
                    });
                    $('#possibleImages').append($elem)
                    if (sendLoadMsg) sendNotif("Alle Bilder wurden geladen", "success");
                });
            } else {
                if (sendLoadMsg) sendNotif("Keine Bilder wurden gefunden", "error");
            }
        },
        error: function (xhr, status, error) {
            // Fehler bei der Anfrage
            if (sendLoadMsg) sendNotif("Es kam zu einem unerwarteten Fehler, versuche es später nochmal", "error");
        }
    });
}

function closeTeamImageModal() {
    $('#imageModal').addClass("hidden").removeClass("flex");
}

function setTeamImageModalTab(panelId) {
    $('.image-modal-panel').addClass('hidden').removeClass('flex');
    $('#' + panelId).removeClass('hidden').addClass('flex');

    $('.image-modal-tab')
        .removeClass('bg-blue-900 text-white shadow-sm')
        .addClass('text-slate-700 hover:bg-white hover:text-slate-950');

    $('.image-modal-tab[data-target="' + panelId + '"]')
        .addClass('bg-blue-900 text-white shadow-sm')
        .removeClass('text-slate-700 hover:bg-white hover:text-slate-950');
}

function refreshTeamSelectedImagePreview() {
    const src = $('#imagePreview').attr('src');
    if (src) {
        $('#selectedImagePreview').attr('src', src).removeClass('hidden');
        $('#selectedImagePlaceholder').addClass('hidden');
    } else {
        $('#selectedImagePreview').attr('src', '').addClass('hidden');
        $('#selectedImagePlaceholder').removeClass('hidden');
    }
}

function selectTeamImage($image) {
    const $imagePreview = $('#imagePreview');
    $imagePreview.attr('src', $image.attr('src'));
    $imagePreview.attr('imgId', $image.attr('imgId'));
    $imagePreview.removeClass("hidden");
    closeTeamImageModal();
    sendNotif('Neues Bild ausgewählt', 'success');
}

function renderTeamImageLibrary(images) {
    const search = ($('#imageSearchInput').val() || '').toLowerCase().trim();
    const filteredImages = images.filter(function (image) {
        return !search || (image.title || '').toLowerCase().includes(search);
    });

    const $container = $('#possibleImages');
    $container.empty();

    filteredImages.forEach(function (image) {
        const title = escapeTeamImageHtml(image.title || 'Bild');
        const $button = $(`
            <button type="button" class="group relative overflow-hidden rounded-lg bg-white text-left shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-0.5 hover:shadow-lg hover:ring-blue-300">
                <img src="${image.url}" imgId="${image.id}" alt="${title}" class="h-36 w-full object-cover">
                <span class="absolute left-2 top-2 rounded-md bg-white/90 px-2 py-1 text-[11px] font-semibold text-slate-700 shadow-sm ring-1 ring-slate-200">
                    ${(image.format || 'IMG')}${image.has_mobile ? ' + Mobil' : ''}
                </span>
                <span class="absolute right-2 top-2 rounded-md bg-white/90 px-2 py-1 text-xs font-semibold text-red-700 opacity-0 shadow-sm ring-1 ring-red-100 transition hover:bg-red-50 group-hover:opacity-100 image-delete-button" data-image-id="${image.id}">
                    <i class="bi bi-trash"></i>
                </span>
                <span class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/80 to-transparent px-3 pb-3 pt-8 text-xs font-semibold text-white opacity-0 transition group-hover:opacity-100">${title}</span>
            </button>
        `);
        $button.click(function () {
            selectTeamImage($(this).find('img'));
        });
        $button.find('.image-delete-button').click(function (event) {
            event.preventDefault();
            event.stopPropagation();
            confirmDeleteTeamImage(image.id, title);
        });
        $container.append($button);
    });

    $('#imageEmptyState').toggleClass('hidden', filteredImages.length > 0);
}

function confirmDeleteTeamImage(imageId, title) {
    const confirmText = 'Dieses Bild wird dauerhaft gelöscht.';
    const confirmAction = function () {
        deleteTeamImage(imageId);
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

function deleteTeamImage(imageId) {
    $.ajax({
        url: '/cms/images/delete/' + imageId + '/',
        type: 'POST',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', $('input[name="csrfmiddlewaretoken"]').val());
        },
        success: function (response) {
            teamImageLibraryItems = teamImageLibraryItems.filter(function (image) {
                return String(image.id) !== String(imageId);
            });
            renderTeamImageLibrary(teamImageLibraryItems);

            if (String($('#imagePreview').attr('imgId')) === String(imageId)) {
                $('#imagePreview').attr('imgId', '-1');
                refreshTeamSelectedImagePreview();
            }

            sendNotif(response.success || 'Bild wurde gelöscht', 'success');
        },
        error: function () {
            sendNotif('Bild konnte nicht gelöscht werden', 'error');
        }
    });
}

function uploadTeamImageFiles(fileList, csrfToken) {
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
        addTeamUploadItem(itemId, file.name);

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
                setTeamUploadItemStatus(itemId, 'Fertig', 'text-green-700', teamUploadOptimizationText(response.image));
                if (response.image) {
                    teamImageLibraryItems.unshift(response.image);
                    renderTeamImageLibrary(teamImageLibraryItems);
                    setTeamImageModalTab('imageLibraryPanel');
                } else {
                    loadImages(false);
                }
                sendNotif('Bild wurde hochgeladen', 'success');
            },
            error: function () {
                setTeamUploadItemStatus(itemId, 'Fehlgeschlagen', 'text-red-700');
                sendNotif('Bild konnte nicht hochgeladen werden', 'error');
            }
        });
    });
}

function addTeamUploadItem(id, name) {
    $('#imageUploadItems').prepend(`
        <div id="${id}" class="rounded-md bg-slate-50 px-3 py-2 text-sm">
            <div class="flex items-center justify-between gap-3">
                <span class="truncate text-slate-700">${escapeTeamImageHtml(name)}</span>
                <span class="upload-status shrink-0 text-slate-500">Lädt...</span>
            </div>
            <p class="upload-detail mt-1 hidden text-xs leading-snug text-slate-500"></p>
        </div>
    `);
    $('#' + id).children('.upload-status').remove();
}

function setTeamUploadItemStatus(id, text, className, detail) {
    const $item = $('#' + id);
    $item.children('.upload-status').remove();
    $item.find('.upload-status')
        .removeClass('text-slate-500 text-green-700 text-red-700')
        .addClass(className)
        .text(text);

    if (detail) {
        $item.find('.upload-detail').text(detail).removeClass('hidden');
    }
}

function teamUploadOptimizationText(image) {
    if (!image || !image.optimization) return '';
    const optimization = image.optimization;
    const desktop = optimization.desktop || {};
    const mobile = optimization.mobile || {};
    const desktopSaved = optimization.desktop_saved_percent > 0 ? ` / -${optimization.desktop_saved_percent}%` : '';
    const mobileSaved = optimization.mobile_saved_percent > 0 ? ` / -${optimization.mobile_saved_percent}%` : '';
    return `Original ${optimization.original_size_kb || 0} KB | Desktop ${desktop.size_kb || 0} KB${desktopSaved} | Mobil ${mobile.size_kb || 0} KB${mobileSaved}`;
}

function escapeTeamImageHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function loadImages(sendLoadMsg) {
    $.ajax({
        url: '/cms/images/all/',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            teamImageLibraryItems = response.image_urls || [];
            renderTeamImageLibrary(teamImageLibraryItems);
            if (sendLoadMsg) {
                const message = teamImageLibraryItems.length ? "Alle Bilder wurden geladen" : "Keine Bilder wurden gefunden";
                sendNotif(message, teamImageLibraryItems.length ? "success" : "error");
            }
        },
        error: function () {
            if (sendLoadMsg) sendNotif("Es kam zu einem unerwarteten Fehler, versuche es später nochmal", "error");
        }
    });
}
// Öffnet das Bearbeiten-Modal für ein Teammitglied und füllt es mit den vorhandenen Daten
function openEditModal(memberId) {
    // AJAX-Request, um die Daten des Teammitglieds zu laden
    $.ajax({
        url: `${memberId}/`,  // Endpoint, der die Daten des Teammitglieds bereitstellt
        type: 'GET',
        success: function (data) {
            // Fülle das Formular mit den vorhandenen Daten
            $('#memberId').val(memberId);
            $('#full_name').val(data.full_name);
            $('#position').val(data.position);
            $('#years_with_team').val(data.years_with_team);
            $('#age').val(data.age);
            $('#email').val(data.email);
            $('#notes').val(data.note);
            $('#activeSwitch').prop('checked', data.active);
            $('#imagePreview').attr('src', data.image).removeClass('hidden'); // Setze Bildvorschau

            // Passe die Modalüberschrift und den Button an
            $('#modalTitle').text('Teammitglied bearbeiten');
            $('#teamMemberModal').find('button[type="submit"]').text('Speichern');

            // Zeige das Modal an
            $('#teamMemberModal').removeClass('hidden');
        },
        error: function () {
            sendNotif('Fehler beim Laden der Teammitglied-Daten.', 'error');
        }
    });
}
