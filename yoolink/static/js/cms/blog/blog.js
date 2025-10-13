var myNicEditor;
var imageData = null;
// Editable Fields
var $editSlider = null;
var $editImg = null;
var $editYoutube = null;
var selectedVideoData = null;
let selectedVideoElement = null;
let selectedAnyfile = null; // {id,url,title,ext}
function loadSlick() {
    $('.carousel').slick({
        dots: true,  // Display navigation dots
        arrows: true,  // Display navigation arrows
        infinite: true,  // Enable infinite looping
        slidesToShow: 1,  // Number of slides to show at once
        slidesToScroll: 1,  // Number of slides to scroll at a time
        autoplay: true,
        autoplaySpeed: 3000,
        // Add any other configuration options as needed
    });

    // Bind Next function to the Next button
    // Bind Next function to the Next button of each carousel
    $('.next-button').on('click', function () {
        var carousel = $(this).closest('.carousel-container').find('.carousel');
        carousel.slick('slickNext');
    });

    // Bind Previous function to the Previous button of each carousel
    $('.prev-button').on('click', function () {
        var carousel = $(this).closest('.carousel-container').find('.carousel');
        carousel.slick('slickPrev');
    });
}

function loadNicEditors() {
    $('.textArea').each(function () {
        if ($(this).attr("id")) {
            myNicEditor.panelInstance($(this).attr("id"), { hasPanel: true })
        }
    })
}

function fileIconForExt(ext) {
    switch (ext) {
        case '.jpg': case '.jpeg': case '.png': case '.gif': case '.webp':
            return 'bi-card-image text-yellow-600';
        case '.pdf': return 'bi-file-earmark-pdf-fill text-red-600';
        case '.zip': case '.rar': return 'bi-file-earmark-zip-fill text-gray-600';
        case '.doc': case '.docx': return 'bi-file-earmark-word-fill text-blue-700';
        case '.xls': case '.xlsx': return 'bi-file-earmark-excel-fill text-green-600';
        case '.mp4': case '.mov': case '.webm': return 'bi-file-earmark-play-fill text-purple-600';
        case '.txt': return 'bi-file-earmark-text-fill text-gray-600';
        default: return 'bi-file-earmark-fill text-gray-500';
    }
}

$(document).ready(function () {

    // Inside myscript.js
    var imageUrl = "{% static 'js/cms/blog/nicEditorIcons.gif' %}";

    // Now you can use `imageUrl` in your JavaScript code

    // NicEditor (TextFields)
    myNicEditor = new nicEditor({
        buttonList: ['bold', 'italic', 'underline', 'left', 'center', 'right', 'justify', 'ol', 'ul', 'subscript', 'superscript', 'strikethrough', 'removeformat', 'indent', 'outdent', 'hr', 'fontSize', 'fontFamily', 'fontFormat', 'forecolor', 'bgcolor', 'link', 'unlink']
    })

    loadSlick();
    loadNicEditors();
    loadImages();

    function initializeSimpleSortable() {
        new Sortable(document.getElementById('blogContent'), {
            handle: '.handle', // handle's class
            animation: 150,
            forceFallback: true
        })
    }


    // Initialize sortable for existing elements
    initializeSimpleSortable();

    // Handle the keydown event on the textarea
    $('textarea').on('keydown', function (event) {
        // Check if the pressed key is Tab (key code 9)
        if (event.keyCode === 9) {
            event.preventDefault(); // Prevent the default behavior (jumping to the next element)
            // Insert a tab character at the current cursor position
            const start = this.selectionStart;
            const end = this.selectionEnd;
            const value = this.value;
            this.value = value.substring(0, start) + '\t' + value.substring(end);
            this.selectionStart = this.selectionEnd = start + 1;
        }
    });

    $('.del-elem').click(function () {
        $(this).parent().remove()
    })

    // scroll bottom
    function scrollToBottom() {
        // Scroll to the bottom of the page
        $('html, body').animate({
            scrollTop: $(document).height() - $(window).height()
        }, 800); // 800 milliseconds for animation duration
    }

    /**
     * Add Überschrift I to Blog
     */
    $('#addTitle').click(function () {
        // Create Container
        const $container = $('<div class="relative" element-type="title-1">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))
        $('<input/>', {
            type: "text",
            class: "title-1 my-3 text-2xl font-bold text-gray-900 w-full px-4 py-2 border border-gray-300 rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent relative",
            placeholder: "Überschrift I"
        }).appendTo($container)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);
        sendNotif("Eine Überschrift I wurde hinzugefügt", "success")
        scrollToBottom()
    });

    /**
      * Add Überschrift II to Blog
      */
    $('#addTitle2').click(function () {
        // Create Container
        const $container = $('<div class="relative" element-type="title-2">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))
        $('<input/>', {
            type: "text",
            class: "title-2 text-xl font-semibold w-full px-4 py-2 my-3 border border-gray-300 rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent relative",
            placeholder: "Überschrift II"
        }).appendTo($container)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);
        sendNotif("Eine Überschrift II wurde hinzugefügt", "success")
        scrollToBottom()
    });

    /**
      * Add Überschrift III to Blog
      */
    $('#addTitle3').click(function () {
        // Create Container
        const $container = $('<div class="relative" element-type="title-3">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))
        $('<input/>', {
            type: "text",
            class: "title-3 text-lg font-medium w-full px-4 py-2 my-3 border border-gray-300 rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent relative",
            placeholder: "Überschrift III"
        }).appendTo($container)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);
        sendNotif("Eine Überschrift III wurde hinzugefügt", "success")
        scrollToBottom()
    });

    /**
      * Add Text to Blog
      */
    $('#addText').click(function () {
        // Create Container
        const $container = $('<div class="relative my-2" element-type="textArea">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))
        const textAreaId = "textArea" + ($('.textArea').length + 1);
        $('<textarea/>', {
            id: textAreaId,
            rows: "4",
            class: "textArea w-full px-4 py-2 my-3 rounded-2xl border border-gray-300 focus:outline-none focus:border-blue-500 min-h-[5rem]",
            placeholder: "Text"
        }).appendTo($container)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);
        myNicEditor.panelInstance(textAreaId, { hasPanel: true })
        sendNotif("Eine Text-Box wurde hinzugefügt", "success")
        scrollToBottom()
    });

    /**
      * Add Image to Blog
      */
    $('#addImage').click(function () {
        // Create Container
        const $container = $('<div class="relative w-fit my-3" element-type="image">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))
        $container.append($('<span class="absolute top-0 left-0 inline-block px-2 py-1 text-sm font-semibold text-white bg-orange-500 rounded-full not-sortable z-40 hover:cursor-pointer edit-img"><i class="bi bi-pencil-square"></i></span>'))

        $('<img>', {
            title: "Bildtitel",
            src: "https://placehold.co/600x400",
            class: "rounded-2xl w-auto h-129",
        }).appendTo($container)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        $container.find('.edit-img').click(function () {
            $editImg = $(this).siblings('img');
            height = typeof $editImg[0].style !== 'undefined' && $editImg[0].style.height ? $editImg[0].style.height : $editImg.height();
            width = typeof $editImg[0].style !== 'undefined' && $editImg[0].style.width ? $editImg[0].style.width : $editImg.width();
            if (width == 0 || width == "0") { width = "100%" }
            $('#imgHeight').val(height)
            $('#imgWidth').val(width)
            $('#imgText').val($editImg.attr('title'))
            if ($("#myDiv").is(":empty")) {
                loadImages()
            }
            $('#imageModal').toggleClass("hidden");
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);
        sendNotif("Ein Bild wurde hinzugefügt. Bitte konfigurieren.", "success")
        scrollToBottom()
        $container.find('.edit-img').click()
    });

    /**
      * Add Image to Blog
      */
    $('#addVideo').click(function () {
        // Create Container
        const $container = $('<div class="relative w-fit py-4 my-3" element-type="yt-video">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))
        $container.append($('<span class="absolute top-0 left-0 inline-block px-2 py-1 text-sm font-semibold text-white bg-orange-500 rounded-full not-sortable z-40 hover:cursor-pointer edit-youtube"><i class="bi bi-pencil-square"></i></span>'))

        $('<iframe/>', {
            title: "YouTube video player",
            frameborder: "0",
            src: "https://www.youtube.com/embed/eEzD-Y97ges",
            allow: "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
            class: "rounded-2xl",
            width: "560",
            height: "315",
            allowfullscreen: "True"
        }).appendTo($container)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        $container.find('.edit-youtube').click(function () {
            $editYoutube = $(this).siblings('iframe');

            height = $editYoutube[0].style.height ? $editYoutube[0].style.height : $editYoutube.height();
            width = $editYoutube[0].style.width ? $editYoutube[0].style.width : $editYoutube.width();

            $('#youtubeHeight').val(height)
            $('#youtubeWidth').val(width)

            $('#youtubeURL').val($editYoutube.attr('src'))
            $('#youtubeText').val($editYoutube.attr('title'))
            $('#youtubeModal').toggleClass("hidden");
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);
        sendNotif("Ein Youtube Video wurde hinzugefügt. Bitte konfigurieren.", "success")
        scrollToBottom()
        $container.find('.edit-youtube').click()
    });

    /**
     * Add Real Video
     */
    $('#addVideoCMS').click(function () {
        $.get("/cms/videos/all/", function (response) {
            if (!response.video_urls || response.video_urls.length === 0) {
                sendNotif("Keine Videos verfügbar", "error");
                return;
            }

            const video = response.video_urls[0]; // z.B. erstes Video einfügen
            const $container = $('<div class="relative py-4 my-3" element-type="video">');
            $container.append($('<span class="absolute top-0 right-0 px-2 py-1 text-sm text-white bg-red-500 rounded-full z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'));
            $container.append($('<span class="absolute top-0 right-1/2 px-2 py-1 text-sm text-white bg-blue-500 rounded-full z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'));
            $container.append($('<span class="absolute top-0 left-0 px-2 py-1 text-sm font-semibold text-white bg-orange-500 rounded-full z-40 hover:cursor-pointer edit-cmsvideo"><i class="bi bi-pencil-square"></i></span>'));

            const $videoElem = $('<video>', {
                title: video.title,
                src: video.url,
                poster: video.poster,
                class: "rounded-2xl",
                width: 560,
                height: 315,
                autoplay: video.autoplay,
                muted: video.muted,
                loop: video.loop,
                playsinline: video.playsinline,
                controls: video.show_controls,
                preload: video.preload
            });

            // SEO relevante Daten als Data-Attributes
            $videoElem.data({
                description: video.description,
                alt_text: video.alt_text,
                tags: video.tags,
                duration: video.duration
            });

            $container.append($videoElem);

            $container.find('.del-elem').click(function () {
                $(this).parent().remove();
            });

            // Edit-Handler
            $container.find('.edit-cmsvideo').click(function () {
                const $modal = $('#videoModal');
                const $video = $(this).siblings('video');

                // Setze das Ziel-Element für später
                $modal.data('target', $(this).parent());
                selectedVideoData = {
                    url: $video.attr('src'),
                    poster: $video.attr('poster'),
                    title: $video.attr('title') || '',
                    autoplay: $video.prop('autoplay'),
                    muted: $video.prop('muted'),
                    loop: $video.prop('loop'),
                    playsinline: $video.prop('playsinline'),
                    preload: $video.attr('preload') || 'metadata',
                    width: $video.css('width') || $video.attr('width') || '',
                    height: $video.css('height') || $video.attr('height') || ''
                };

                $('#videoTitle').val(selectedVideoData.title);
                $('#videoAlt').val($video.data('alt_text') || '');
                $('#videoAutoplay').prop('checked', selectedVideoData.autoplay);
                $('#videoMuted').prop('checked', selectedVideoData.muted);
                $('#videoLoop').prop('checked', selectedVideoData.loop);
                $('#videoPlaysinline').prop('checked', selectedVideoData.playsinline);
                $('#videoPreload').val(selectedVideoData.preload);

                $('#videoWidth').val(selectedVideoData.width);
                $('#videoHeight').val(selectedVideoData.height);

                $('.cms-video-preview').removeClass('!border-blue-500');
                $('#videoProperties').removeClass('hidden');
                $('#videoModal').removeClass('hidden');
                loadCMSVideos(); // Funktion zum Laden der Auswahl
            });

            $("#blogContent").append($container);
            sendNotif("Ein Video wurde eingefügt", "success");
            scrollToBottom();
            $container.find('.edit-cmsvideo').click();
        });
    });

    // Open File modal
    $('#addFile').click(function () {
        $('#anyfileModal').removeClass('hidden');
        selectedAnyfile = null;
        $('#selectAnyfile').prop('disabled', true);
        loadAnyfiles();
    });

    $('.cms-video-preview').click(function () {
        const videoId = $(this).data("video-id");
        const $target = $('#videoModal').data('target');

        if ($target) {
            updateBlogVideoFromCMS(videoId, $target);
            $('#videoModal').addClass('hidden');
        }
    });

    /**
     * Add Galerie to Blog
     */
    $('#addGalerie').click(function () {
        // Create Container
        const $container = $('<div class="relative w-full my-4" element-type="galery" galery-id="0">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))
        $container.append($('<span class="absolute top-0 left-0 inline-block px-2 py-1 text-sm font-semibold text-white bg-orange-500 rounded-full not-sortable z-40 hover:cursor-pointer edit-slider"><i class="bi bi-pencil-square"></i></span>'))

        const $carousel = $('<div class="carousel rounded-lg">')
        for (let i = 0; i < 2; i++) {
            const $cDiv = $('<div>')
            $('<img>', {
                title: "Carousel Placeholder",
                src: "https://placehold.co/800x400",
                class: "w-full rounded-xl h-96",
            }).appendTo($cDiv)
            $carousel.append($cDiv)
        }
        $carousel.slick({
            dots: true,  // Display navigation dots
            arrows: true,  // Display navigation arrows
            infinite: true,  // Enable infinite looping
            slidesToShow: 1,  // Number of slides to show at once
            slidesToScroll: 1,  // Number of slides to scroll at a time
            autoplay: true,
            autoplaySpeed: 3000,
            // Add any other configuration options as needed
        });
        $container.append($carousel)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        $container.find('.edit-slider').click(function () {
            $editSlider = $(this).siblings('.carousel');
            const $editSliderImg = $editSlider.find("img");

            height = typeof $editSliderImg[0].style !== 'undefined' && $editSliderImg[0].style.height ? $editSliderImg[0].style.height : $editSliderImg.height();
            width = typeof $editSliderImg[0].style !== 'undefined' && $editSliderImg[0].style.width ? $editSliderImg[0].style.width : $editSliderImg.width();

            if (width == 0 || width == "0") { width = "100%" }

            $('#galeryHeight').val(height)
            $('#galeryWidth').val(width)
            $('#galleryModal').toggleClass("hidden");
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);

        sendNotif("Eine Galerie wurde hinzugefügt. Bitte konfigurieren.", "success")
        scrollToBottom()
        $container.find('.edit-slider').click()

    });

    /**
      * Add Text to Blog
      */
    $('#addCode').click(function () {
        // Create Container
        const $container = $('<div class="relative my-3" element-type="code">')
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'))
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'))

        const $codeContainer = $('<div class="code border-2 border-dotted border-gray-600 rounded-xl p-2 mb-3">')

        $('<input/>', {
            type: "text",
            class: "code-language title-3 text-lg w-full px-4 py-2 my-3 border border-gray-300 rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent relative",
            placeholder: "Sprache (z.B. python)"
        }).appendTo($codeContainer)
        $('<textarea/>', {
            rows: "4",
            class: "code-source w-full text-black px-4 py-2 my-3 rounded-2xl border border-gray-300 focus:outline-none focus:border-blue-500 min-h-[5rem]",
            placeholder: "Deinen Source-Code hier rein kopieren"
        }).appendTo($codeContainer)
        $container.append($codeContainer)
        // Click event handler for the span with class del-elem
        $container.find('.del-elem').click(function () {
            $(this).parent().remove()
        });
        // Append Container to Blog Builder
        $("#blogContent").append($container);
        sendNotif("Ein Code-Editor wurde hinzugefügt", "success")
        scrollToBottom()
    });



    /****************** Titelbild *******************/

    $('#titleImgUpload').change(function () {
        // Get the uploaded file
        var file = this.files[0];

        // Check if a file is selected
        if (file) {
            // Create a FileReader
            var reader = new FileReader();

            // Set up the FileReader onload event
            reader.onload = function (e) {
                // Set the source of the preview image to the FileReader result
                $('#fileUpload').css('background-image', "url('" + e.target.result + "')");
                // Show the preview image
                imageData = e.target.result
            };

            // Read the uploaded file as a data URL
            reader.readAsDataURL(file);
        } else {
            // Hide the preview image if no file is selected
            $('#fileUpload').css('background-image', "none");

        }
    });

    /****************** Blog Action Logic *******************/
    $('#closeModal').click(function () {
        $('#previewModal').toggleClass("hidden")
    });
    $('#closeGaleryModal').click(function () {
        $('#galleryModal').toggleClass("hidden")
    });
    $('#closeImageModal').click(function () {
        $('#imageModal').toggleClass("hidden")
    })
    $('#closeYoutubeModal').click(function () {
        $('#youtubeModal').toggleClass("hidden")
    })
    $('#closeAnyfileModal').click(function () {
        $('#anyfileModal').addClass('hidden');
    });

    /****************** AnyFile Logic *******************/
    $('#reloadAnyfiles').click(function () {
        loadAnyfiles($('#anyfileSearch').val().trim());
    });
    // Live-Filter (client-seitig)
    $('#anyfileSearch').on('input', function () {
        const q = $(this).val().toLowerCase();
        $('#availableAnyfiles .anyfile-tile').each(function () {
            const hay = ($(this).data('title') + ' ' + $(this).data('ext')).toLowerCase();
            $(this).toggle(hay.includes(q));
        });
    });
    // Laden
    function loadAnyfiles() {
        const $grid = $('#availableAnyfiles');
        const $empty = $('#anyfileEmpty');
        $grid.empty(); $empty.addClass('hidden');

        $.get('/cms/anyfiles/all/', function (resp) {
            if (!resp.files || resp.files.length === 0) {
                $empty.removeClass('hidden'); return;
            }
            resp.files.forEach(f => {
                const $tile = $(`
            <div class="anyfile-tile border rounded p-3 hover:shadow cursor-pointer transition group"
                data-id="${f.id}" data-url="${f.url}" data-title="${$('<div>').text(f.title).html()}" data-ext="${f.ext}">
            <div class="flex items-center gap-2">
                <i class="bi ${fileIconForExt(f.ext)} text-xl"></i>
                <div class="truncate">
                <div class="font-medium truncate" title="${f.title}">${f.title}</div>
                <div class="text-xs text-gray-500">${f.ext}</div>
                </div>
            </div>
            </div>
        `);
                $tile.on('click', function () {
                    $('#availableAnyfiles .anyfile-tile').removeClass('border-2 border-blue-500');
                    $(this).addClass('border-2 border-blue-500');
                    selectedAnyfile = {
                        id: $(this).data('id'),
                        url: $(this).data('url'),
                        title: $(this).data('title'),
                        ext: $(this).data('ext'),
                    };
                    $('#selectAnyfile').prop('disabled', false);
                });
                $grid.append($tile);
            });
        });
    }
    // UI-Block erzeugen
    function addAnyfileToContent(file) {
        const $container = $('<div class="relative my-3" element-type="file">');
        $container.append($('<span class="absolute top-0 right-0 inline-block px-2 py-1 text-sm text-white bg-red-500 rounded-full not-sortable z-40 hover:cursor-pointer del-elem"><i class="bi bi-trash"></i></span>'));
        $container.append($('<span class="absolute top-0 right-1/2 inline-block px-2 py-1 text-sm text-white bg-blue-500 rounded-full not-sortable z-40 hover:cursor-pointer handle"><i class="bi bi-arrows-move"></i></span>'));

        const icon = fileIconForExt(file.ext);
        const $a = $(`
    <a class="file-attachment flex items-center gap-2 p-3 border rounded hover:bg-gray-50"
       href="${file.url}" target="_blank" rel="noopener"
       data-id="${file.id}" data-ext="${file.ext}" title="${file.title}">
      <i class="bi ${icon} text-xl"></i>
      <span class="file-title truncate">${file.title}</span>
    </a>
  `);

        $container.append($a);

        // delete des Blocks
        $container.find('.del-elem').click(function () {
            $(this).parent().remove();
        });

        $('#blogContent').append($container);
    }

    $('#selectAnyfile').click(function () {
        if (!selectedAnyfile) return;
        addAnyfileToContent(selectedAnyfile);
        $('#anyfileModal').addClass('hidden');
        sendNotif('Datei hinzugefügt', 'success');
        // Scroll nach unten (du hast schon scrollToBottom())
        if (typeof scrollToBottom === 'function') scrollToBottom();
    });

    // Save Blog
    $('#createBlog').click(function () {
        enableSpinner($(this))
        // Get the CSRF token from the hidden input field

        // Check for errors
        const title = $('#blogTitle').val()
        var files = $('#titleImgUpload').prop("files");

        if (title === "" || title === undefined) {
            sendNotif("Bitte gebe einen Titel für den Blog (rechts) ein.", "error")
            disableSpinner($(this))
            return;
        }

        if (files.length == 0) {
            sendNotif("Bitte wähle ein Titelbild aus!", "error")
            disableSpinner($(this))
            return;
        }

        var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

        // Get Code
        const $blockContent = $('#blogContent')
        // Select the first element with attr("element-type") = 'textArea' within elements with class 'relative' in 'blockContent'
        var $firstTextArea = $blockContent.children('.relative').find('.textArea').first();
        if ($firstTextArea.length == 0) {
            sendNotif("Es muss mindestens ein gefüllter Text hinzugefügt werden!", "error")
            disableSpinner($(this))
            return;
        }
        var firstTextAreaId = $firstTextArea.attr('id')
        var firstTextAreaContent = myNicEditor.instanceById(firstTextAreaId).getContent()
        var tempDiv = document.createElement("div");
        tempDiv.innerHTML = firstTextAreaContent;
        var plainText = tempDiv.textContent || tempDiv.innerText || ""
        // Überprüfen, ob ein Element gefunden wurde
        if (plainText.trim() === '') {
            // Ein Element wurde gefunden
            // Du kannst hier weiter mit 'firstTextArea' arbeiten
            sendNotif("Es muss mindestens ein gefüllter Text hinzugefügt werden!", "error")
            disableSpinner($(this))
            return;
        }
        const content = receiveContent($blockContent)
        // Load to previewBody
        const $directCodeContainer = $('<div>')
        const $modalBody = $('<div class"space-y-6">')
        const blogLayout = $('#blogLayout').val()
        if (blogLayout.includes('center')) {
            $modalBody.addClass('flex flex-col items-center')
        } else if (blogLayout.includes('right')) {
            $modalBody.removeClass('items-center').addClass('flex flex-col items-end')
        } else {
            $modalBody.removeClass('flex flex-col items-center items-end')
        }
        $modalBody.append($('<h1 id="previewTitle" class="text-3xl mb-6 font-extrabold leading-tight text-gray-900 lg:text-4xl">').text($('#blogTitle').val()))
        //$modalBody.append($copy)
        content.forEach(function (element) {
            // Führe eine Aktion für jedes Element aus
            const $elem = (element.name !== "galery") ? getWebElement(element) : getGaleryElement(element)
            $modalBody.append($elem);
        });
        $directCodeContainer.append($modalBody)

        const title_image = files[0]

        // Create a new FormData object
        var formData = new FormData();
        formData.append('title', $('#blogTitle').val());
        formData.append('body', $directCodeContainer.html());
        formData.append('code', JSON.stringify(content));
        formData.append('active', $('#activeSwitch').is(':checked'));
        formData.append('title_image', title_image, "blogTitleImage");
        formData.append('description', plainText);

        // Send the Ajax POST request //
        $.ajax({
            type: "POST",
            url: "/cms/blog/create/",
            data: formData,
            processData: false, // Prevent jQuery from processing the data
            contentType: false, // Prevent jQuery from setting the content type
            dataType: "json",
            beforeSend: function (xhr) {
                // Add the CSRF token to the request headers
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (response) {
                // Handle the success response here
                if (response.error) {
                    sendNotif(response.error, "error")
                    return;
                }
                window.location.href = '/cms/blog/' + response.blogId + "/";
            },
            error: function (xhr, status, error) {
                // Handle the error response here
                console.error("Request failed:", error);
                sendNotif("Es kam zu einem unerwarteten Fehler. Versuche es später nochmal")
                $('#createBlog').prop("disabled", false);
                $(this).find('svg').addClass('hidden');
            },
            complete: function (result, status) {
                disableSpinner($('#createBlog'))
            }
        });
    })


    // Click on preview Button (Test)
    $('#preview').click(function () {

        // receive block content
        const $blockContent = $('#blogContent')
        const content = receiveContent($blockContent)

        const $modalBody = $('#previewBody')

        const blogLayout = $('#blogLayout').val()

        if (blogLayout.includes('center')) {
            $modalBody.addClass('flex flex-col items-center')
        } else if (blogLayout.includes('right')) {
            $modalBody.removeClass('items-center').addClass('flex flex-col items-end')
        } else {
            $modalBody.removeClass('flex flex-col items-center items-end')
        }

        //const $copy = $modalBody.find('address').clone()
        $modalBody.empty()
        // Add Title
        $modalBody.append($('<h1 class="text-3xl mb-6 font-extrabold leading-tight text-gray-900 lg:text-4xl">').text($('#blogTitle').val()))
        //$modalBody.append($copy)
        content.forEach(function (element) {
            // Führe eine Aktion für jedes Element aus
            const $elem = (element.name !== "galery") ? getWebElement(element) : getGaleryElement(element)
            $modalBody.append($elem);
        });

        $('#previewModal').toggleClass("hidden")

        // Load Carousels
        setTimeout(function () {
            Prism.highlightAll();
            loadCarousels()
        }, 1000)


    });

    // Open Image Modal
    $('.edit-img').click(function () {
        // Send ajax to get all images
        $editImg = $(this).siblings('img');

        height = typeof $editImg[0].style !== 'undefined' && $editImg[0].style.height ? $editImg[0].style.height : $editImg.height();
        width = typeof $editImg[0].style !== 'undefined' && $editImg[0].style.width ? $editImg[0].style.width : $editImg.width();

        $('#imgHeight').val(height)
        $('#imgWidth').val(width)

        $('#imgText').val($editImg.attr('title'))

        if ($("#possibleImages").is(":empty")) {
            loadImages()
        }
        $('#imageModal').toggleClass("hidden");
    });

    /** -------- BEGIN - Youtube-Video -------- */

    // Open Youtube Modal
    $('.edit-youtube').click(function () {

        $editYoutube = $(this).siblings('iframe');

        height = $editYoutube[0].style.height ? $editYoutube[0].style.height : $editYoutube.height();
        width = $editYoutube[0].style.width ? $editYoutube[0].style.width : $editYoutube.width();

        $('#youtubeHeight').val(height)
        $('#youtubeWidth').val(width)

        $('#youtubeURL').val($editYoutube.attr('src'))
        $('#youtubeText').val($editYoutube.attr('title'))
        $('#youtubeModal').toggleClass("hidden");

    });

    // Use external image
    $('#useYoutubeURL').click(function () {
        if ($editYoutube && $('#youtubeURL').val()) {
            // Extrahiere den Code hinter "v="
            const vidTitle = $('#youtubeURL').val()
            const videoCode = vidTitle.split("v=")[1];

            // Erstelle den eingebetteten Link
            const embeddedLink = vidTitle.includes('embed') ? vidTitle : `https://www.youtube.com/embed/${videoCode}`;
            $editYoutube.attr('src', embeddedLink);
            sendNotif('Youtube Video ausgewählt', 'success')
        }
    })

    // Resize Youtube Iframe (click on "Übernehmen")
    $('#selectYoutube').click(function () {
        var imgHeight = $('#youtubeHeight').val();
        var imgWidth = $('#youtubeWidth').val();
        const $imgDiv = $editYoutube.closest('.relative')
        // Set height of edited image and parent container
        $editYoutube.css("height", imgHeight)
        $imgDiv.css("height", parseInt(imgHeight) + 20)
        // Set width of edited image and parent container
        $editYoutube.css("width", imgWidth)
        $imgDiv.css("width", imgWidth)
        // Set title of edited image
        $editYoutube.attr('title', $('#youtubeText').val())

        sendNotif('Youtube Video wurde erfolgreich angepasst', 'success')
    })

    /** -------- END - Youtube-Video -------- */

    // Open gallery Modal
    $('.edit-slider').click(function () {
        $editSlider = $(this).siblings('.carousel');
        const $editSliderImg = $editSlider.find("img");

        height = typeof $editSliderImg[0].style !== 'undefined' && $editSliderImg[0].style.height ? $editSliderImg[0].style.height : $editSliderImg.height();
        width = typeof $editSliderImg[0].style !== 'undefined' && $editSliderImg[0].style.width ? $editSliderImg[0].style.width : $editSliderImg.width();

        $('#galeryHeight').val(height)
        $('#galeryWidth').val(width)
        $('#galleryModal').toggleClass("hidden");

    })

    // Reload Images
    $('#reloadImages').click(function () {
        loadImages();
    })

    // Reload Galerien
    $('#reloadGalerien').click(function () {
        loadGalerien();
    })

    // Text Field - Toggle Editor
    $('.toggle-text-editor').click(function () {

        $textSibling = $(this).siblings("textarea")
        if (myNicEditor.nicInstances)
            myNicEditor.panelInstance($textSibling.attr('id'), { hasPanel: true })
    })

    /*---- IMAGES SECTION -----*/

    // Select new image
    $('#possibleImages img').click(function () {
        if ($editImg) {
            $editImg.attr('src', $(this).attr('src'));
            //$editImg.attr('imgId', )
            //$('#imageModal').toggleClass("hidden");
            sendNotif('Neues Bild ausgewählt', 'success')
        }
    });

    $('#possibleGalerien div').click(function () {
        // Get Galery Id and then get Galery Details
        const galeryId = $(this).attr("galeryId")
        // Ajax Call To get Galery Details and add to slick
        sendNotif("Diese Galerie wird geladen...", "notice")
        selectGalery(galeryId);

    })

    // Modal schließen
    $('#closeVideoModal').click(function () {
        $('#videoModal').addClass('hidden');
    });

    // Modal öffnen und Videos laden
    function openVideoModal(targetElement) {
        $('#videoModal').removeClass('hidden');
        $('#videoModal').data('target', targetElement);
        loadCMSVideos();
    }

    // Modal-Videos neu laden
    $('#reloadCMSVideos').click(function () {
        loadCMSVideos();
    });


    function loadCMSVideos(preselectId = null) {
        const $container = $('#availableVideos');
        $container.empty();

        $.get("/cms/videos/all/", function (response) {
            if (!response.video_urls || response.video_urls.length === 0) {
                $container.append('<p class="text-gray-600">Keine Videos verfügbar.</p>');
                return;
            }

            response.video_urls.forEach(video => {
                const $preview = $(`
                <div class="relative cursor-pointer cms-video-preview group border-2 border-transparent rounded" data-video-id="${video.id}">
                <video src="${video.url}" poster="${video.poster}" preload="metadata" muted
                    class="w-full rounded shadow group-hover:shadow-lg transition">
                </video>
                </div>
            `);

                if (preselectId && video.id === preselectId) {
                    $preview.addClass('!border-blue-500');
                    selectVideoAndLoadProps(video.id);
                }

                $preview.click(function () {
                    $('.cms-video-preview').removeClass('!border-blue-500');
                    $(this).addClass('!border-blue-500');
                    selectedVideoElement = $(this);
                    selectVideoAndLoadProps(video.id);
                });

                $container.append($preview);
            });
        });
    }

    function selectVideoAndLoadProps(videoId) {
        $.get(`/cms/videos/get/${videoId}/`, function (data) {
            selectedVideoData = data;
            $('#selectedVideoId').val(data.id);
            $('#videoTitle').val(data.title || '');
            $('#videoAlt').val(data.alt_text || '');
            $('#videoAutoplay').prop('checked', data.autoplay);
            $('#videoMuted').prop('checked', data.muted);
            $('#videoLoop').prop('checked', data.loop);
            $('#videoPlaysinline').prop('checked', data.playsinline);
            $('#videoPreload').val(data.preload || 'metadata');
        });
    }

    $('#selectVideo').click(function () {
        const $target = $('#videoModal').data('target');
        if (!$target) return;
        const $video = $target.find('video');
        if (selectedVideoData) {
            $video.attr('src', selectedVideoData.url);
            $video.attr('poster', selectedVideoData.poster);
        }
        $video.attr('title', $('#videoTitle').val() || '');

        $video.prop('autoplay', $('#videoAutoplay').is(':checked'));
        $video.prop('muted', $('#videoMuted').is(':checked'));
        $video.prop('loop', $('#videoLoop').is(':checked'));
        $video.prop('playsinline', $('#videoPlaysinline').is(':checked'));
        $video.attr('preload', $('#videoPreload').val());

        // Neu: Breite & Höhe setzen
        const widthVal = $('#videoWidth').val();
        const heightVal = $('#videoHeight').val();
        if (widthVal) $video.css('width', widthVal);
        if (heightVal) $video.css('height', heightVal);

        $('#videoModal').addClass('hidden');
        sendNotif("Video übernommen", "success");
    });

    function updateBlogVideoFromCMS(videoId, $targetContainer) {
        $.get(`/cms/videos/get/${videoId}/`, function (data) {
            const $video = $targetContainer.find('video');

            $video.attr('src', data.url);
            $video.attr('poster', data.poster);
            $video.attr('title', data.title || '');

            // Optional: Optionen setzen
            $video.prop('autoplay', data.autoplay);
            $video.prop('muted', data.muted);
            $video.prop('loop', data.loop);
            $video.prop('playsinline', data.playsinline);
            $video.prop('controls', data.show_controls);
            $video.attr('preload', data.preload);

            sendNotif("Video aktualisiert", "success");
        });
    }

    function selectGalery(id) {
        $.ajax({
            url: "/cms/galery/getImages/", // Replace this with your API endpoint
            type: "GET",
            data: { "galeryId": id },
            dataType: "json", // The data type you expect to receive from the server
            success: function (data) {
                // This function will be executed if the request is successful
                if (data.images.length > 0) {
                    const c = $editSlider.find('.slick-slide:not(.slick-cloned)')
                    for (let i = c.length - 1; i >= 0; i--) {
                        $editSlider.slick("slickRemove", i)
                    }
                    const height = $('#galeryHeight').val()
                    const width = $('#galeryWidth').val()
                    data.images.forEach(function (image) {
                        const img = '<img src="' + image.upload_url + '" class="w-full rounded-xl" style="height: ' + height + '; width: ' + width + '">'
                        $editSlider.slick('slickAdd', '<div>' + img + '</div>');
                    })
                    $editSlider.closest(".relative").attr('galery-id', id)
                    sendNotif("Galerie wurde erfolgreich geladen", "success")
                } else {
                    sendNotif("Diese Galerie ist leer. Bitte befülle sie erst!", "error")
                }

                // You can now process the received data
            },
            error: function (xhr, status, error) {
                // This function will be executed if the request fails
                console.error("Error:", error);
                sendNotif("Etwas hat nicht funktioniert. Versuche es später erneut", "error")
            }
        });
    }

    // Use external image
    $('#useExternImageURL').click(function () {
        if ($editImg && $('#imgURL').val()) {
            $editImg.attr('src', $('#imgURL').val());
            sendNotif('Externes Bild ausgewählt', 'success')
        }
    })

    // Resize Image (click on "Übernehmen")
    $('#selectImg').click(function () {
        var imgHeight = $('#imgHeight').val();
        var imgWidth = $('#imgWidth').val();
        const $imgDiv = $editImg.closest('.relative')
        // Set height of edited image and parent container
        $editImg.css("height", imgHeight)
        $imgDiv.css("height", imgHeight)
        // Set width of edited image and parent container
        $editImg.css("width", imgWidth)
        $imgDiv.css("width", imgWidth)
        // Set title of edited image
        $editImg.attr('title', $('#imgText').val())

        sendNotif('Bild wurde erfolgreich angepasst', 'success')
    })

    // Resize Galery (click on "Übernehmen")
    $('#selectGalery').click(function () {
        var galeryHeight = $('#galeryHeight').val();
        var galeryWidth = $('#galeryWidth').val();
        const $galeryContainer = $editSlider.closest('.relative')
        $galeryContainer.css("height", galeryHeight).css("width", galeryWidth)
        $editSlider.find('img').each(function () {
            $(this).css("height", galeryHeight)
            $(this).css("width", galeryWidth)
        })
        sendNotif('Galerie wurde erfolgreich angepasst', 'success')
    })

    // Load images from backend
    function loadImages() {
        $.ajax({
            url: '/cms/images/all/',
            type: 'GET',
            dataType: 'json',
            success: function (response) {
                // Erfolgreiche Anfrage
                if (response.image_urls && response.image_urls.length != 0) {
                    $('#possibleImages').empty()
                    response.image_urls.forEach(function (url) {
                        const $elem = $('<img src="' + url.url + '" class="h-28 w-full rounded-2xl col-span-1 my-4 hover:shadow-2xl hover:cursor-pointer hover:scale-105">')
                        // Add Event Handler for selection
                        $elem.click(function () {
                            if ($editImg) {
                                $editImg.attr('src', $(this).attr('src'));
                                //$('#imageModal').toggleClass("hidden");
                                sendNotif('Neues Bild ausgewählt', 'success');
                            }
                        });
                        $('#possibleImages').append($elem)
                        sendNotif("Alle Bilder wurden geladen", "success");
                    });
                } else {
                    sendNotif("Keine Bilder wurden gefunden", "error");
                }
            },
            error: function (xhr, status, error) {
                // Fehler bei der Anfrage
                sendNotif("Es kam zu einem unerwarteten Fehler, versuche es später nochmal", "error");
            }
        });
    }

    // For loadGalerien()
    function addTitleAndDescription(title, description, id) {
        var $div = $('<div>').addClass('border border-gray-200 shadow-xl rounded-2xl h-full w-full p-4 hover:cursor-pointer hover:shadow-blue-300');
        $div.attr('galeryId', id)
        var $title = $('<h1>').addClass('text-xl font-semibold mb-2').text(title);
        var $description = $('<p>').addClass('max-h-[8rem] overflow-auto').text(description);

        $div.append($title);
        $div.append($description);

        return $div;
    }

    // Load galerien from backend
    function loadGalerien() {
        sendNotif("Alle Galerien werden geladen...", "notice");
        $.ajax({
            url: '/cms/galerien/all/',
            type: 'GET',
            dataType: 'json',
            success: function (response) {
                // Erfolgreiche Anfrage
                if (response.galerien && response.galerien.length != 0) {
                    $('#possibleGalerien').empty()
                    response.galerien.forEach(function (gallery) {
                        const $galleryItem = addTitleAndDescription(gallery.title, gallery.description, gallery.id);
                        $galleryItem.click(function () {
                            const galeryId = $(this).attr("galeryId")
                            // Ajax Call To get Galery Details and add to slick
                            sendNotif("Diese Galerie wird geladen...", "notice")
                            selectGalery(galeryId);
                        })
                        $('#possibleGalerien').append($galleryItem)
                        sendNotif("Alle Galerien wurden geladen", "success");
                    });
                } else {
                    sendNotif("Es wurden keine Galerien gefunden", "error");
                }
            },
            error: function (xhr, status, error) {
                // Fehler bei der Anfrage
                sendNotif("Es kam zu einem unerwarteten Fehler, versuche es später nochmal", "error");
            }
        });
    }

    $('.pgallery').click(function () {
        // TODO: Select new gallery
        // ...
    })

    $('.modal').each(function () {
        const modal = $(this);
        const modalContainer = modal.find('.modal-container');

        // Close the modal when clicking outside of it (by targeting the parent modal)
        $(document).mouseup(function (e) {
            if (!modalContainer.is(e.target) && modalContainer.has(e.target).length === 0) {
                modal.addClass('hidden');
            }
        });
    });

});

/**
 * Receive content from blog edit div
 * @param {*} blockContent 
 * @returns 
 */
function receiveContent(blockContent) {
    // Loop through all divs
    var content = []
    blockContent.children('.relative').each(function () {
        // Check for type of div
        const elementType = $(this).attr("element-type");

        switch (elementType) {
            case "title-1":
                const title1Input = $(this).find('.title-1').val()
                content.push({
                    "name": "title-1",
                    "type": "h2",
                    "attributes": {
                        "class": "text-2xl mb-6 font-bold text-gray-900 lg:text-3xl",
                    },
                    "value": title1Input
                })
                break;
            case "title-2":
                const title2Input = $(this).find('.title-2').val()
                content.push({
                    "name": "title-2",
                    "type": "h3",
                    "attributes": {
                        "class": "text-xl font-semibold my-4 lg:text-2xl",
                    },
                    "value": title2Input
                })
                break;
            case "title-3":
                const title3Input = $(this).find('.title-3').val()
                content.push({
                    "name": "title-3",
                    "type": "h4",
                    "attributes": {
                        "class": "text-lg font-medium my-4 lg:text-xl",
                    },
                    "value": title3Input
                })
                break;
            case "textArea":
                const $textArea = $(this).find('.textArea')
                textId = $textArea.attr('id')
                if (textId) {
                    content.push({
                        "name": "textArea",
                        "type": "p",
                        "attributes": {
                            "class": "text-base my-4",
                        },
                        "value": myNicEditor.instanceById(textId).getContent()
                    })
                }
                break;
            case "image":
                const $img = $(this).find('img')
                cssHeight = $img.css('height');
                cssWidth = $img.css('width');

                height = typeof $img[0].style !== 'undefined' && $img[0].style.height ? $img[0].style.height : cssHeight;
                width = typeof $img[0].style !== 'undefined' && $img[0].style.width ? $img[0].style.width : cssWidth;

                content.push({
                    "name": "image",
                    "type": "img",
                    "attributes": {
                        "src": $img.attr('src'),
                        "title": $img.attr('title'),
                        "class": "rounded-2xl my-4",
                    },
                    "css": {
                        "height": height,
                        "width": width
                    }
                });
                break;
            case "code":
                const lang = "language-" + $(this).find('.code-language').val()
                const $code = $(this).find('.code')
                if (lang) {
                    content.push({
                        "name": "code",
                        "type": "code",
                        "attributes": {
                            "class": "rounded-2xl my-4 " + lang,
                            "data-prismjs-copy": "Copy"
                        },
                        "value": $(this).find('.code-source').val(),
                        "css": {
                            "height": $code.css('height'),
                            "width": $code.css('width')
                        }

                    })
                }
                break;
            case "yt-video":
                const $video = $(this).find('iframe')
                cssHeight = $video.css('height');
                cssWidth = $video.css('width');

                height = typeof $video[0].style !== 'undefined' && $video[0].style.height ? $video[0].style.height : cssHeight;
                width = typeof $video[0].style !== 'undefined' && $video[0].style.width ? $video[0].style.width : cssWidth;
                content.push({
                    "name": "yt-video",
                    "type": "iframe",
                    "attributes": {
                        "width": width,
                        "height": height,
                        "src": $video.attr('src'),
                        "title": $video.attr('title'),
                        "frameborder": "0",
                        "allow": "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
                        "allowfullscreen": "True",
                        "class": "my-8 rounded-2xl"

                    },

                })
                break;
            case "galery":
                $carousel = $(this).find('.carousel');
                cssHeight = $carousel.css('height');
                cssWidth = $carousel.css('width');

                //height = $carousel[0].style.height ? $carousel[0].style.height : cssHeight;
                //width = $carousel[0].style.width ? $carousel[0].style.width : cssWidth;
                var urlList = []

                var height;
                var width;

                $carousel.find('img').each(function () {
                    var imageUrl = $(this).attr('src');

                    if (typeof height === 'undefined' || typeof width === 'undefined') {
                        height = typeof $(this).style !== 'undefined' && $(this).style.height ? $(this).style.height : $(this).css("height");
                        width = typeof $(this).style !== 'undefined' && $(this).style.width ? $(this).style.width : $(this).css("width");
                    }

                    if (!urlList.includes(imageUrl)) urlList.push(imageUrl);
                });
                content.push({
                    "name": "galery",
                    "type": "div",
                    "attributes": {
                        "id": $(this).attr("galery-id"),
                        "class": "carousel rounded-lg !w-full",
                    },
                    "css": {
                        "height": height,
                        "width": width
                    },
                    "images": urlList,
                    "imageClass": "w-full rounded-xl",
                })
                break;
            case "video":
                // 1) Bevorzugt echtes <video>
                const $videoEl = $(this).find('video');
                if ($videoEl.length) {
                    // Größen ermitteln
                    const cssH = $videoEl.css('height');
                    const cssW = $videoEl.css('width');
                    const height = ($videoEl[0].style && $videoEl[0].style.height) ? $videoEl[0].style.height : cssH;
                    const width = ($videoEl[0].style && $videoEl[0].style.width) ? $videoEl[0].style.width : cssW;
                    // Attribute/Props einsammeln
                    const src = $videoEl.attr('src') || '';
                    const poster = $videoEl.attr('poster') || '';
                    const title = $videoEl.attr('title') || '';
                    const preload = $videoEl.attr('preload') || 'metadata';
                    const autoplay = !!$videoEl.prop('autoplay');
                    const muted = !!$videoEl.prop('muted');
                    const loop = !!$videoEl.prop('loop');
                    const playsinline = !!$videoEl.prop('playsinline');
                    const controls = !!$videoEl.prop('controls');
                    // SEO/Model Felder (data-Attribute)
                    const dataAlt = $videoEl.data('alt_text') || '';
                    const dataDesc = $videoEl.data('description') || '';
                    const dataTags = $videoEl.data('tags') || '';
                    const dataDuration = $videoEl.data('duration') || '';
                    const dataVideoId = $videoEl.data('video_id') || '';
                    // Klassen zusammenführen
                    const klass = ($videoEl.attr('class') || '').trim();
                    const mergedClass = (klass ? klass + " " : "") + "my-8 rounded-2xl";
                    // Attribute setzen (Booleans nur wenn true)
                    const attrs = {
                        "src": src,
                        "poster": poster,
                        "title": title,
                        "preload": preload,
                        "class": mergedClass,
                        "data-alt_text": dataAlt,
                        "data-description": dataDesc,
                        "data-tags": dataTags,
                        "data-duration": dataDuration,
                        "data-video_id": dataVideoId,
                    };
                    if (autoplay) attrs.autoplay = "autoplay";
                    if (muted) attrs.muted = "muted";
                    if (loop) attrs.loop = "loop";
                    if (playsinline) attrs.playsinline = "playsinline";
                    if (controls) attrs.controls = "controls";
                    content.push({
                        "name": "video",
                        "type": "video",
                        "attributes": attrs,
                        "css": {
                            "height": height,
                            "width": width
                        }
                    });
                }
                break;
            case "file":
                const $a = $(this).find('a.file-attachment');
                content.push({
                    "name": "file",
                    "type": "a",
                    "attributes": {
                        "href": $a.attr('href'),
                        "target": "_blank",
                        "rel": "noopener",
                        "title": $a.attr('title') || $a.find('.file-title').text(),
                        "data-id": $a.data('id'),
                        "data-ext": $a.data('ext'),
                        "class": "file-attachment flex items-center gap-2 p-3 border rounded my-3"
                    },
                    // Text im Anchor (nutzen wir als sichtbaren Titel)
                    "value": $a.find('.file-title').text()
                });
                break;

        }
    });
    return content;
}


function getGaleryElement(gallery) {
    var elem = $('<' + gallery.type + ">");
    // Füge die Attribute dem Element hinzu
    $.each(gallery.attributes, function (key, value) {
        elem.attr(key, value);
    });

    $.each(gallery.css, function (key, value) {
        elem.css(key, value);
    });

    gallery.images.forEach(function (url, index) {
        const $div = $('<div>')
        const $img = $('<img>');
        $img.addClass(gallery.imageClass);
        $img.attr('src', url);
        $.each(gallery.css, function (key, value) {
            $img.css(key, value);
        });
        $div.append($img);
        elem.append($div);
    })
    return elem;
}

function loadCarousels() {
    $('.carousel').slick({
        dots: true,  // Display navigation dots
        arrows: true,  // Display navigation arrows
        infinite: true,  // Enable infinite looping
        slidesToShow: 1,  // Number of slides to show at once
        slidesToScroll: 1,  // Number of slides to scroll at a time
        autoplay: true,
        autoplaySpeed: 3000,
        // Add any other configuration options as needed
    });


}

function replaceLinks(text) {
    const linkRegex = /link\("([^"]+)", "([^"]+)"\)/g;
    let replacedText = text;

    let match;
    while ((match = linkRegex.exec(text)) !== null) {
        const link = `<a class="text-blue-500 hover:text-blue-600" href="${match[2]}">${match[1]}</a>`;
        replacedText = replacedText.replace(match[0], link);
    }

    return replacedText;
}

/**
 * Baut aus einem JSON-Baustein ein DOM-Element.
 * Unterstützt speziell: <video> (Boolean-Props, CSS width/height)
 * und "code" (in <pre> wrap).
 *
 * @param {*} jsonElem
 * @returns jQuery-Element
 */
function getWebElement(jsonElem) {
    const type = jsonElem.type || 'div';
    let elem;

    // 1) Spezialfall: echtes Video
    if (jsonElem.name === 'video' && type === 'video') {
        elem = $('<video>');

        // Attribute setzen (string-Attribute)
        if (jsonElem.attributes) {
            // zuerst Standard-String-Attribute
            const strAttrs = ['src', 'poster', 'title', 'preload', 'class', 'id'];
            strAttrs.forEach(k => {
                if (jsonElem.attributes[k] != null && jsonElem.attributes[k] !== false) {
                    elem.attr(k, jsonElem.attributes[k]);
                }
            });

            // SEO/Model-Daten als data-*
            Object.keys(jsonElem.attributes).forEach(k => {
                if (k.startsWith('data-')) {
                    elem.attr(k, jsonElem.attributes[k]);
                }
            });

            // Boolean-Props korrekt anwenden
            const boolMap = ['autoplay', 'muted', 'loop', 'playsinline', 'controls'];
            boolMap.forEach(k => {
                // im JSON steht meist "autoplay": "autoplay" (oder true)
                const v = jsonElem.attributes[k];
                if (v === true || v === 'true' || v === k || v === '1' || v === 'autoplay' || v === 'muted' || v === 'loop' || v === 'playsinline' || v === 'controls') {
                    elem.prop(k, true).attr(k, k); // prop + Präsenz-Attribut
                }
            });
        }

        // Größe immer per CSS setzen (unterstützt px/%)
        if (jsonElem.css) {
            if (jsonElem.css.width) elem.css('width', jsonElem.css.width);
            if (jsonElem.css.height) elem.css('height', jsonElem.css.height);
            // weitere CSS übernehmen
            Object.keys(jsonElem.css).forEach(k => {
                if (k !== 'width' && k !== 'height') elem.css(k, jsonElem.css[k]);
            });
        }

        return elem;
    }

    // Spezialfall: Datei-Link mit Icon
    if (jsonElem.name === 'file' && (jsonElem.type === 'a' || !jsonElem.type)) {
        const ext = (jsonElem.attributes && (jsonElem.attributes['data-ext'] || jsonElem.attributes['data- ext'])) || '';
        const iconCls = fileIconForExt(ext);
        const $wrap = $('<div class="my-3">');
        const $a = $('<a>');
        if (jsonElem.attributes) {
            Object.keys(jsonElem.attributes).forEach(k => $a.attr(k, jsonElem.attributes[k]));
        }
        $a.addClass('file-attachment');
        if (jsonElem.value) $a.append($('<span class="file-title truncate">').text(jsonElem.value));
        // Icon vorn einsetzen
        $a.prepend($('<i>').addClass('bi ' + iconCls + ' text-xl mr-2'));
        return $wrap.append($a);
    }

    // 2) Standard-Rendering (inkl. iframe, img, h*, p*, etc.)
    elem = $('<' + type + '>');
    if (jsonElem.value) {
        if (jsonElem.name === 'code') {
            elem.text(jsonElem.value);
        } else {
            elem.html(replaceLinks(jsonElem.value));
        }
    }

    // Attribute setzen
    if (jsonElem.attributes) {
        $.each(jsonElem.attributes, function (key, value) {
            // Für iframes darf alles wie gehabt als Attribut bleiben
            elem.attr(key, value);
        });
    }

    // CSS anwenden
    if (jsonElem.css) {
        $.each(jsonElem.css, function (key, value) {
            elem.css(key, value);
        });
    }

    // Code in <pre> wrappen
    if (jsonElem.name === 'code') {
        elem = $('<pre>').append(elem);
    }

    return elem;
}

/**
 * Disable Button Spinner
 * @param {*} $elem 
 */
function disableSpinner($elem) {
    $elem.prop("disabled", false);
    $elem.find('svg').addClass('hidden');
    $elem.find('.bi').removeClass('hidden');
}

/**
 * Enable Button Spinner
 * @param {*} $elem 
 */
function enableSpinner($elem) {
    $elem.prop("disabled", true);
    $elem.find('svg').removeClass('hidden');
    $elem.find('.bi').addClass('hidden');
}
