// Get the input elements that are currently hidden
var hiddenInputs = document.querySelectorAll("input[type='hidden']");

// Loop through the hidden inputs and make them visible
for (var i = 0; i < hiddenInputs.length; i++) {
    hiddenInputs[i].type = "text";
}
