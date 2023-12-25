function domAddUserInput(text) {
    var chatContainer = document.querySelector('.chat-container');
    var chatBubble = document.createElement('div');
    chatBubble.classList.add('chat-bubble');
    chatBubble.classList.add('chat-bubble-right');
    chatBubble.innerText = text;
    chatContainer.appendChild(chatBubble);

    // Check if the user is already scrolled to the bottom
    if (chatContainer.scrollTop + chatContainer.clientHeight >= chatContainer.scrollHeight) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function domAddGeminiOutput(text) {
    var chatContainer = document.querySelector('.chat-container');
    var chatBubble = document.createElement('div');
    chatBubble.classList.add('chat-bubble');
    chatBubble.classList.add('chat-bubble-left');

    chatBubble.innerHTML = marked.parse(text);
    chatContainer.appendChild(chatBubble);

    // Check if the user is already scrolled to the bottom
    if (chatContainer.scrollTop + chatContainer.clientHeight >= chatContainer.scrollHeight) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function toggleMenu() {
    var menuItems = document.querySelector('.menu-items');
    menuItems.classList.toggle('show');
}

function onChatContainerClick(event) {
    if (event.target.matches('code')) {
        // Copy the text inside the code block to the clipboard
        navigator.clipboard.writeText(event.target.textContent);
    }
}

function onDomContentLoaded() {
    var inputField = document.getElementById('input-field');
    var form = document.getElementById('chat-form');
    var menuButton = document.querySelector('.menu-button');
    var chatContainer = document.querySelector('.chat-container');

    form.addEventListener('submit', function (e) {
        e.preventDefault(); // prevent form submission
        let text = inputField.value;
        console.log(text);

        domAddUserInput(text.toString());

        // Send HTTP POST request to "/ask-gemini" with parameter "query" of value text.toString()
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/ask-gemini", true);
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
                // Handle the response here
                console.log(xhr.responseText);
                domAddGeminiOutput(xhr.responseText);
            }
        };
        xhr.send("query=" + encodeURIComponent(text.toString()));

        inputField.value = ''; // clear the input field
    });

    // Show menu items when menu button is clicked
    menuButton.addEventListener('click', toggleMenu);

    chatContainer.addEventListener('click', onChatContainerClick);
}

document.addEventListener('DOMContentLoaded', onDomContentLoaded);
