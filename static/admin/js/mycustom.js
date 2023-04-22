

function showLoader () {
    $(`<div id="loader"><div class="spinner-grow text-primary" role="status">
        <span class="sr-only">Loading...</span>
        </div></div>`).appendTo('body')
    $('#myForm').submit()
}


const SUCCESS = '#11851b'
const ERROR = '#FF0000'
const INFO = '#f0ad4e'
function myToast(msg, bgColor) {
    Toastify({
        text: msg,
        duration: 3000,
        close: true,
        gravity: "top", // `top` or `bottom`
        position: "right", // `left`, `center` or `right`
        stopOnFocus: true, // Prevents dismissing of toast on hover
        style: {
            background: bgColor,
        },
    }).showToast();
}

