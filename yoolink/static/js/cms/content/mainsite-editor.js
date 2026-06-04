/**
 * Mainsite combined editor
 * -------------------------
 * Tracks unsaved changes on the single "Hauptseite" editor and warns the user
 * before they navigate away (e.g. clicking "FAQ verwalten"). Offers to save
 * first, discard and continue, or open the target in a new tab so the current
 * (unsaved) edits stay untouched.
 *
 * Saving itself is handled by save-text.js. We only listen to its
 * "textContentSaved" / "textContentSaveError" events.
 */
(function () {
    "use strict";

    var isDirty = false;
    var bypassUnloadGuard = false;

    function markDirty() {
        if (isDirty) return;
        isDirty = true;
        $("#dirtyBadge").removeClass("hidden").addClass("inline-flex");
    }

    function markClean() {
        isDirty = false;
        $("#dirtyBadge").addClass("hidden").removeClass("inline-flex");
    }

    function navigateTo(url) {
        bypassUnloadGuard = true;
        markClean();
        window.location.href = url;
    }

    function saveThenNavigate(url) {
        // Navigate as soon as the save succeeds; stay put if it fails.
        // Named handlers so we only ever detach *these* listeners (never the
        // global markClean listener bound on document).
        function onSaved() {
            $(document).off("textContentSaveError", onError);
            navigateTo(url);
        }
        function onError() {
            $(document).off("textContentSaved", onSaved);
        }
        $(document).one("textContentSaved", onSaved);
        $(document).one("textContentSaveError", onError);
        $("#saveTextData").trigger("click");
    }

    function confirmLeave(url) {
        if (typeof Swal === "undefined") {
            if (window.confirm("Du hast ungespeicherte Änderungen. Seite wirklich verlassen? Nicht gespeicherte Änderungen gehen verloren.")) {
                navigateTo(url);
            }
            return;
        }

        Swal.fire({
            title: "Ungespeicherte Änderungen",
            html: "Du hast Änderungen vorgenommen, die noch <strong>nicht gespeichert</strong> sind.<br>" +
                  "Wenn du fortfährst, gehen diese verloren.",
            icon: "warning",
            showDenyButton: true,
            showCancelButton: true,
            reverseButtons: true,
            focusConfirm: true,
            confirmButtonText: '<i class="bi bi-save2 mr-1"></i> Speichern & fortfahren',
            denyButtonText: '<i class="bi bi-trash mr-1"></i> Verwerfen & fortfahren',
            cancelButtonText: "Abbrechen",
            confirmButtonColor: "#16a34a",
            denyButtonColor: "#dc2626",
            cancelButtonColor: "#64748b",
            footer: '<a href="' + encodeURI(url) + '" id="guardOpenNewTab" class="text-blue-600 hover:text-blue-800">' +
                    '<i class="bi bi-box-arrow-up-right mr-1"></i>Stattdessen in neuem Tab öffnen (Änderungen behalten)</a>',
            didOpen: function () {
                var link = document.getElementById("guardOpenNewTab");
                if (!link) return;
                link.addEventListener("click", function (ev) {
                    ev.preventDefault();
                    window.open(url, "_blank", "noopener");
                    Swal.close();
                });
            }
        }).then(function (result) {
            if (result.isConfirmed) {
                saveThenNavigate(url);
            } else if (result.isDenied) {
                navigateTo(url);
            }
            // Cancel / dismiss: stay on the page, keep the changes.
        });
    }

    $(document).ready(function () {
        var $scope = $("#mainsiteEditor");
        if (!$scope.length) return;

        // 1) Text edits mark the page dirty.
        $scope.on("input change", "input, textarea", function () {
            markDirty();
        });

        // 2) Galery / video swaps happen via modals that only change attributes,
        //    so watch those attributes directly.
        var watched = $scope.find(".galery-container, .content-video, .content-image").toArray();
        if (window.MutationObserver && watched.length) {
            var observer = new MutationObserver(function (mutations) {
                for (var i = 0; i < mutations.length; i++) {
                    if (mutations[i].type === "attributes") {
                        markDirty();
                        return;
                    }
                }
            });
            watched.forEach(function (el) {
                observer.observe(el, {
                    attributes: true,
                    attributeFilter: ["galery-id", "videoid", "imgid", "src"]
                });
            });
        }

        // 3) A successful save clears the dirty state.
        $(document).on("textContentSaved", function () {
            markClean();
        });

        // 4) Intercept in-page navigation links so we can warn cleanly.
        $scope.on("click", ".js-guard-nav", function (e) {
            var url = $(this).attr("href") || $(this).data("href");
            if (!url || url === "#") return;
            if (!isDirty) return; // nothing to lose -> let the browser navigate
            e.preventDefault();
            confirmLeave(url);
        });

        // 5) Safety net for everything else (navbar, refresh, tab close, back).
        window.addEventListener("beforeunload", function (e) {
            if (isDirty && !bypassUnloadGuard) {
                e.preventDefault();
                e.returnValue = "";
                return "";
            }
        });
    });
})();
