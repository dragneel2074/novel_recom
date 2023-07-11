$(function () {
    $("#selected_novel_name").autocomplete({
        source: '/autocomplete',
        minLength: 2,
        select: function (event, ui) {
            $("#selected_novel_name").val(ui.item.value);
        }
    });
});
$("#randomButton").onclick = function () {
    //  document.getElementById("loadMoreButton").style.display = "none";
    $('#loadMoreButton').hide();

}



$(document).ready(function () {


    $("#novelmateaiButton").click(function (event) {
        event.preventDefault();

        var selectedNovelName = $('#selected_novel_name').val();
        $.ajax({
            url: '/novelmateai',
            type: 'POST',
            dataType: 'json',  // Expect a JSON response

            data: { selected_novel_name: selectedNovelName },
            success: function (response) {
                $("#loader").show();
                // Display the response message
                if (response.hasOwnProperty('error')) {
                    var message = "An Error Occured! Try sometime later"
                    $('#botOutput').html(formattedMessage);
                    //  $('#botOutput').html(response.message);
                    $('#novelmateaiResponse').show();

                    $("#loader").hide();
                    return
                }

                // var lines = response.message.split('\n');
                // // Format the response message
                // var formattedMessage = '<p>' + lines.join('</p><p>') + '</p>';

                var lines = response.message.split('\n');
                var formattedMessage = '<p>' + lines.join('</p><p>') + '</p>';

                // Append the link at the end
                formattedMessage += '<p>You can read these here: <a href="https://nobleradar.com/go/webnovel" target="_blank">www.nobleradar.com/go/webnovel</a></p>';

                // Display the formatted message
                $('#botOutput').html(formattedMessage);
                //  $('#botOutput').html(response.message);
                $('#novelmateaiResponse').show();

                $("#loader").hide();  // Hide the loader after the response is displayed

            },
            error: function (jqXHR, textStatus, errorThrown) {
                // Log the error to the console
                console.error(
                    "The following error occurred: " +
                    textStatus, errorThrown
                );
                $("#loader").hide();

                // Alert the user
                alert('Something went wrong, please try again');
            }
        });
    });

    $("#imagegenButton").click(function (event) {
        event.preventDefault();

        var selectedNovelName = $('#selected_novel_name').val();
        $.ajax({
            url: '/ai-anime-image-generator',
            type: 'POST',
            dataType: 'json', // Expect a JSON response
            data: { selected_novel_name: selectedNovelName },
            success: function (response) {
                $("#loader").show();
                var img = $('<img id="generatedImage">');

                // Set the src attribute of the img tag to the URL of the generated image
                img.attr('src', response.image_url);

                // Append the img tag to the container
                $('#imageContainer').html(img);
                // Set the src attribute of the img tag to the URL of the generated image
                //   $('#generatedImage').attr('src', response.image_url);

                $("#loader").hide();
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $("#loader").hide();
                // Log the error to the console
                console.error(
                    "The following error occurred: " +
                    textStatus, errorThrown
                );
            }
        });
    });



    $(".submitBtn").click(function () {

        var action = $(this).attr('name');
        var selectedNovelName = $('#selected_novel_name').val();
        var url = action == 'action2' ? '/random' : '/';
        var type = 'POST'; // always use POST

        $("#loader").show();

        $.ajax({
            url: url,
            type: type,
            data: { action: action, selected_novel_name: selectedNovelName },
            success: function (response) {
                // Clear the recommendations container
                $('#recommendations-row').empty();
                $('#selected_novel_name').val(selectedNovelName);
                console.log('response is:')
                console.log(response)
                if (response.hasOwnProperty('recommendations')) {
                    // Populate the recommendations container
                    for (var i = 0; i < response.recommendations.length; i++) {
                        var novel = response.recommendations[i];
                        var html = '<div class="col-md-4 mb-4">' +
                            '<div class="card">' +
                            '<img src="' + novel.image_url + '" onerror="imgError(this);" alt="' + novel.name + '" class="card-img-top">' +
                            '<div class="card-body">' +
                            '<h5 class="card-title"><a href="/?selected_novel_name=' + novel.name + '">' + novel.name + '</a></h5>' +
                            '<a href="https://your_website.com/review_page" class="btn btn-primary">📖 Read This Novel</a>' +
                            '</div></div></div>';
                        $('#recommendations-row').append(html);
                    }

                    $('.novel-name-link').on('click', function (event) {
                        // Prevent the default link click action
                        event.preventDefault();

                        // Get the selected novel name from the link text
                        var selectedNovelName = $(this).text();

                        // Set the search box to the selected novel name
                        $('#selected_novel_name').val(selectedNovelName);

                        // Trigger the recommendation request
                        $(".submitBtn").click();
                    });
                } else {
                    console.log("No recommendations in response");
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                // Log the error to the console
                console.error(
                    "The following error occurred: " +
                    textStatus, errorThrown
                );

                // Hide the loader
                $("#loader").hide();

                // Alert the user
                alert('Something went wrong, please try again');
            }
        });
    });

});


function imgError(image) {
    image.onerror = "";
    image.src = "/static/images/no_image.png";
    return true;



}

//nav bar
$(document).ready(function () {
    $('.navbar-nav .nav-link').on('click', function () {
        $('.navbar-nav .nav-link.active').removeClass('active');
        $(this).addClass('active');
    });
});


// top picks

// $(document).ready(function () {
//     $('.btn-link').on('click', function () {
//         var current = $(this).attr('data-target');
//         if($(current).hasClass('show')){
//             $(current).collapse('hide');
//         } else {
//             $('.collapse').collapse('hide');
//             $(current).collapse('show');
//         }
//     });
// });

var apiKey = localStorage.getItem('apiKey');
if (apiKey != null) {
    window.onload = validateApiKey;



}
function removeApiKey() {

    localStorage.removeItem('apiKey');

    // Update the connection status to disconnected
    var apiKeyStatus = document.getElementById('apiKeyStatus');
    apiKeyStatus.textContent = 'Disconnected';
    apiKeyStatus.className = 'disconnected';
    // Hide the Remove API Key button
    // var removeApiKeyButton = document.getElementById('removeApiKeyButton');
    var removeApiKeyButton = document.querySelector('.remove-api-button');

    removeApiKeyButton.style.display = 'none';
}



function validateApiKey() {
    var apiKey = localStorage.getItem('apiKey');

    // If the API key is not stored, get it from the input field
    if (apiKey === null) {
        apiKey = document.getElementById('apiKey').value;
    }
    var apiKeyStatus = document.getElementById('apiKeyStatus');
    var translateStatus = document.getElementById('translateStatus');
    translateStatus.style.display = 'block';


    // Check if the API key is not empty
    if (!apiKey.trim()) {
        alert('Please enter your OpenAI API key.');
        return;
    }

    //  Call the API key validation API


    fetch('/validate-api-key', {

        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'apiKey=' + encodeURIComponent(apiKey)
    })
        .then(response => response.json())
        .then(data => {
            translateStatus.style.display = 'none';
            // Update the connection status
            if (data.error) {
                apiKeyStatus.textContent = 'Disconnected';
                apiKeyStatus.className = 'disconnected';
            } else {
                apiKeyStatus.textContent = 'Connected';
                apiKeyStatus.className = 'connected';

                localStorage.setItem('apiKey', apiKey);


            }
        })
        .catch(() => {
            translateStatus.style.display = 'none';
            // Show an error message
            alert('An error occurred while validating the API key.');
        });
}

function translateText() {
    var apiKey = localStorage.getItem('apiKey');

    // If the API key is not stored, get it from the input field
    if (apiKey === null) {
        apiKey = document.getElementById('apiKey').value;
    }
    var inputText = document.getElementById('inputText').value;
    var outputText = document.getElementById('outputText');
    var translateStatus = document.getElementById('translateStatus');

    // Check if the API key is not empty
    if (!apiKey.trim()) {
        alert('Please enter your OpenAI API key.');
        return;
    }

    // Check if the input text is not empty
    if (!inputText.trim()) {
        alert('Please enter some text.');
        return;
    }

    // Show the translation status
    translateStatus.style.display = 'block';

    // Call the translation API
    fetch('/translate-api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'text=' + encodeURIComponent(inputText) + '&apiKey=' + encodeURIComponent(apiKey)
    })
        .then(response => response.json())
        .then(data => {
            // Hide the translation status
            translateStatus.style.display = 'none';

            // Show the translated text or an error message
            if (data.error) {

                alert(data.error);
            } else {
                outputText.value = data.translated_text;
            }
        })
        .catch(() => {
            // Hide the translation status
            translateStatus.style.display = 'none';

            // Show an error message
            alert('An error occurred while translating the text.');
        });
}

