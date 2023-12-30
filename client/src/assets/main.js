import * as marked from "marked";

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT;

export function scrollChatContainerToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

export function isChatContainerScrolledToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    return chatContainer.scrollTop + chatContainer.clientHeight >= chatContainer.scrollHeight;
}

export function addChatBubble(text, isUser) {
    const chatContainer = document.querySelector('.chat-container');
    const chatBubble = document.createElement('div');
    chatBubble.classList.add('chat-bubble');
    chatBubble.classList.add(isUser ? 'chat-bubble-right' : 'chat-bubble-left');
    chatBubble.innerHTML = isUser ? text : marked.parse(text);

    // Check if the user is already scrolled to the bottom
    var chatContainerIsAtBottom = isChatContainerScrolledToBottom();

    chatContainer.appendChild(chatBubble);

    // Scroll to bottom if the user was previously already scrolled to the bottom before the new content was added
    if (chatContainerIsAtBottom) {
        setTimeout(scrollChatContainerToBottom, 0); // wait for the DOM to update (Vue reactivity)
    }
}

export function toggleMenu() {
    const menuItems = document.querySelector('.menu-items');
    menuItems.classList.toggle('show');
}

export function copyCodeToClipboard(event) {
    if (event.target.matches('code')) {
        const codeText = event.target.textContent;
        navigator.clipboard.writeText(codeText);
    }
}

export function handleFormSubmit(event, isXhrLoading) {
    event.preventDefault(); // prevent form submission

    if (isXhrLoading.value) {
        // Prevent multiple requests from being sent at the same time
        return;
    }

    isXhrLoading.value = true;

    const inputField = document.getElementById('input-field');
    const text = inputField.value;

    const imageInputField = document.getElementById('file-upload');
    const image = imageInputField.files[0];

    var token = getTokenFromCookie();
    if (!token) {
        token = generateUUID();
        document.cookie = "token=" + token + ";path=/";
    }

    // Only send request if the user entered something
    if (text.length > 0) {
        addChatBubble(text.toString(), true);
        // Send HTTP POST request to "/ask-gemini" with parameter "query" of value text.toString()
        const formData = new FormData();
        formData.append("message", text.toString());
        formData.append("token", token);
        formData.append("image", image);

        fetch(API_ENDPOINT + "/ask-gemini", {
            method: "POST",
            body: formData
        })
            .then(response => {
                if (response.ok) {
                    // Handle the successful response here
                    return response.text();
                } else {
                    // Handle the error response here
                    throw new Error("XHR request failed with status: " + response.status);
                }
            })
            .then(responseText => {
                console.log(responseText);
                addChatBubble(responseText, false);
            })
            .catch(error => {
                console.error(error);
                addChatBubble("❌" + error.message, false);
            })
            .finally(() => {
                isXhrLoading.value = false;
            });

        inputField.value = ''; // clear the input field
    }
}

export function resetChat(event, isXhrLoading) {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.innerHTML = '';

    var token = getTokenFromCookie();
    if (!token) {
        token = generateUUID();
        document.cookie = "token=" + token + ";path=/";
    }

    // Send HTTP POST request to "/reset"
    const formData = new FormData();
    formData.append('token', token);

    isXhrLoading.value = true;
    fetch(API_ENDPOINT + "/reset", {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (response.ok) {
                return response.text();
            } else {
                throw new Error("XHR request failed with status: " + response.status);
            }
        })
        .then(responseText => {
            console.log(responseText);

            // Reset chat container content
            chatContainer.innerHTML = '';

            addChatBubble(responseText, false);
        })
        .catch(error => {
            console.error(error);

            if (error.message) {
                addChatBubble(error.message, false);
            } else {
                addChatBubble("❌" + error, false);
            }
        })
        .finally(() => {
            isXhrLoading.value = false;
        });
}

export function generateRandomHexString(length) {
    const characters = '0123456789abcdef';
    let hexString = '';
    for (let i = 0; i < length; i++) {
        const randomIndex = Math.floor(Math.random() * characters.length);
        hexString += characters[randomIndex];
    }
    return hexString;
}

export function generateUUID() {
    const cryptoObj = window.crypto || window.msCrypto;
    if (cryptoObj && cryptoObj.getRandomValues) {
        // Generate a random array of 16 bytes
        const randomBytes = new Uint8Array(16);
        cryptoObj.getRandomValues(randomBytes);

        // Set the version (4) and variant (8, 9, A, or B) bits
        randomBytes[6] = (randomBytes[6] & 0x0f) | 0x40;
        randomBytes[8] = (randomBytes[8] & 0x3f) | 0x80;

        // Convert the bytes to a hexadecimal string
        let uuid = "";
        for (let i = 0; i < 16; i++) {
            uuid += randomBytes[i].toString(16).padStart(2, "0");
        }

        return uuid;
    } else {
        // Fallback to a simple random string if crypto API is not available
        return generateRandomHexString();
    }
}

export function getTokenFromCookie() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('token=')) {
            return cookie.substring('token='.length, cookie.length);
        }
    }
    return null;
}

