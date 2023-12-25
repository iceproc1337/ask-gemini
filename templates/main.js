function addChatBubble(text, isUser) {
    const chatContainer = document.querySelector('.chat-container');
    const chatBubble = document.createElement('div');
    chatBubble.classList.add('chat-bubble');
    chatBubble.classList.add(isUser ? 'chat-bubble-right' : 'chat-bubble-left');
    chatBubble.innerText = text;
    chatContainer.appendChild(chatBubble);

    // Check if the user is already scrolled to the bottom
    if (chatContainer.scrollTop + chatContainer.clientHeight >= chatContainer.scrollHeight) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } else {
        chatContainer.scrollTop = chatContainer.scrollHeight;
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
    console.log(text);

    addChatBubble(text.toString(), true);

    // Send HTTP POST request to "/ask-gemini" with parameter "query" of value text.toString()
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/ask-gemini", true);
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

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('chat-form');
    const menuButton = document.querySelector('.menu-button');
    const chatContainer = document.querySelector('.chat-container');

    menuButton.addEventListener('click', toggleMenu);
    chatContainer.addEventListener('click', copyCodeToClipboard);
    form.addEventListener('submit', handleFormSubmit);
});
