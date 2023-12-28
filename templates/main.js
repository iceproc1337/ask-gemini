API_ENDPOINT = "/api"

function scrollChatContainerToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addChatBubble(text, isUser) {
    const chatContainer = document.querySelector('.chat-container');
    const chatBubble = document.createElement('div');
    chatBubble.classList.add('chat-bubble');
    chatBubble.classList.add(isUser ? 'chat-bubble-right' : 'chat-bubble-left');
    chatBubble.innerHTML = isUser ? text : marked.parse(text);
    
    // Check if the user is already scrolled to the bottom
    var chatContainerIsAtBottom = chatContainer.scrollTop + chatContainer.clientHeight >= chatContainer.scrollHeight;

    chatContainer.appendChild(chatBubble);

    // Scroll to bottom if the user was previously already scrolled to the bottom before the new content was added
    if (chatContainerIsAtBottom) {
        scrollChatContainerToBottom();
    }
}

function toggleMenu() {
    const menuItems = document.querySelector('.menu-items');
    menuItems.classList.toggle('show');
}

function copyCodeToClipboard(event) {
    if (event.target.matches('code')) {
        const codeText = event.target.textContent;
        navigator.clipboard.writeText(codeText);
    }
}

function handleFormSubmit(event) {
    event.preventDefault(); // prevent form submission

    const inputField = document.getElementById('input-field');
    const text = inputField.value;

    // Only send request if the user entered something
    if (text.length > 0) {
        addChatBubble(text.toString(), true);

        // Send HTTP POST request to "/ask-gemini" with parameter "query" of value text.toString()
        const xhr = new XMLHttpRequest();
        xhr.open("POST", API_ENDPOINT + "/ask-gemini", true);
        xhr.withCredentials = true;
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
                // Handle the response here
                console.log(xhr.responseText);
                addChatBubble(xhr.responseText, false);
            }
        };
        xhr.send("message=" + encodeURIComponent(text.toString()));

        inputField.value = ''; // clear the input field
    }
}

function resetChat() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.innerHTML = '';

    // Send HTTP GET request to "/reset"
    const xhr = new XMLHttpRequest();
    xhr.open("GET", API_ENDPOINT + "/reset", true);
    xhr.withCredentials = true;
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Handle the response here
            console.log(xhr.responseText);

            // Reset chat container content
            chatContainer.innerHTML = '';

            addChatBubble(xhr.responseText, false);
        }
    };
    xhr.send();
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('chat-form');
    const menuButton = document.querySelector('.menu-button');
    const chatContainer = document.querySelector('.chat-container');
    const resetButton = document.querySelector('.menu-item-reset');

    menuButton.addEventListener('click', toggleMenu);
    chatContainer.addEventListener('click', copyCodeToClipboard);
    form.addEventListener('submit', handleFormSubmit);
    resetButton.addEventListener('click', resetChat);

    scrollChatContainerToBottom();
});
