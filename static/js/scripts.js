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
                var urlMap = {
                    'webnovel.com': 'https://nobleradar.com/go/webnovel',
                    'amazon.com': 'https://nobleradar.com/go/amazon'
                  };
                var lines = response.message.split('\n');
                // Format the response message
                var formattedMessage = '<p>' + lines.join('</p><p>') + '</p>';
                formattedMessage = formattedMessage.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');

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

window.onload = function() {
    document.getElementById('quizSubmit').onclick = function() {
        alert('Your answers have been submitted!');
    };
};


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