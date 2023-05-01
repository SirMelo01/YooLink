$(document).ready(function () {
    // Create Sortable FAQ List
    Sortable.create(simpleList, {
        animation: 150,
        ghostClass: 'blue-background-class',
        handle: '.handle', // handle's class
    });
    var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
    // Delete FAQ
    $(document).on("click", ".delete", function () {
        // Code for handling the click event on the "delete" button
        var $listItem = $(this).closest('.list-group-item')
        var id = $listItem.attr('data-id')
        $.ajax({
            url: 'delete/' + id + "/",
            type: 'POST',
            data: {
                csrfmiddlewaretoken: csrftoken,
            },
            dataType: 'json',
            success: function (response) {
                console.log(response);
                sendNotif("Das ausgewählte FAQ wurde erfolgreich gelöscht!", "success")
                if (response.success) { $listItem.remove() }
            },
            error: function (xhr, status, error) {
                sendNotif("Fehler beim Löschen des FAQ's", "error")
            }
        });
    });
    // Update FAQ
    $(document).on("click", ".update", function () {
        // Code for handling the click event on the "update" button
        var $listItem = $(this).closest('.list-group-item')
        var question = $listItem.find('.question').val()
        var answer = $listItem.find('.answer').val()
        var id = $listItem.attr('data-id')
        $.ajax({
            url: 'update/',
            type: 'POST',
            data: {
                'answer': answer,
                'question': question,
                'faq_id': id,
                csrfmiddlewaretoken: csrftoken,
            },
            dataType: 'json',
            success: function (response) {
                console.log(response);
                sendNotif("Das ausgewählte FAQ wurde erfolgreich gespeichert!", "success")
            },
            error: function (xhr, status, error) {
                sendNotif("Fehler beim Speichern des FAQ's", "error")
            }
        });
    });
    // Save order
    $('#save-btn').click(function () {
        var faq_ids = [];
        $('#simpleList .list-group-item').each(function () {
            faq_ids.push($(this).attr('data-id'));
        });
        console.log(faq_ids)
        $.ajax({
            url: 'sort/',
            type: 'POST',
            data: { 'faq_ids[]': faq_ids, csrfmiddlewaretoken: csrftoken, },
            dataType: 'json',
            success: function (response) {
                console.log(response);
                sendNotif("Die Sortierung des FAQ's wurde erfolgreich gespeichert!", "success")
            },
            error: function (xhr, status, error) {
                sendNotif("Fehler beim Speichern der Sortierung", "error")
            }
        });
    });

    // Create faq
    $('#add-btn').click(function () {
        $.ajax({
            url: 'update/',
            type: 'GET',
            data: { "question": "Frage", "answer": "Antwort" },
            success: function (response) {
                if (response.success) {
                    createFaq(response.id, response.answer, response.question)
                    sendNotif("Ein FAQ wurde erfolgreich hinzugefügt!", "success")
                }
            },
            error: function (xhr, status, error) {
                sendNotif("Fehler beim Hinzufügen eines neuen FAQ's", "error")
            }
        });
    });
});
function createFaq(id, answer, question) {
    // create the element
    var faqElement = $('<div>').addClass('list-group-item mb-4').attr('data-id', id);
    var innerElement = $('<div>').addClass('flex items-center w-full justify-between bg-slate-600 p-4 text-white rounded-lg');
    innerElement.append($('<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 handle mr-5 hover:cursor-pointer"><path stroke-linecap="round" stroke-linejoin="round" d="M15.042 21.672L13.684 16.6m0 0l-2.51 2.225.569-9.47 5.227 7.917-3.286-.672zm-7.518-.267A8.25 8.25 0 1120.25 10.5M8.288 14.212A5.25 5.25 0 1117.25 10.5" /></svg>'))
    var questionElement = $('<div>').addClass('w-2/5 mr-4');
    var questionInput = $('<input>').attr({
        'type': 'text',
        'value': question,
        'placeholder': "Deine Frage",
        'class': 'appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline question'
    });
    questionElement.append(questionInput);
    var answerElement = $('<div>').addClass('w-2/5 mr-4');
    var answerInput = $('<input>').attr({
        'type': 'text',
        'value': answer,
        'placeholder': "Deine Antwort",
        'class': 'appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline answer'
    });
    answerElement.append(answerInput);
    var buttonElement = $('<div>').addClass('w-1/5');
    var updateButton = $('<button>').addClass('bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline update').attr('type', 'button').text('Sichere');
    var deleteButton = $('<button>').addClass('bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ml-4 delete').attr('type', 'button').text('Lösche');
    buttonElement.append(updateButton, deleteButton);
    innerElement.append(questionElement, answerElement, buttonElement);
    faqElement.append(innerElement);
    $('#simpleList').append(faqElement)
}