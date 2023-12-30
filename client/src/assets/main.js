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

    const inputField = document.getElementById('input-field');
    const text = inputField.value;

    var token = getTokenFromCookie();
    if (!token) {
        token = generateUUID();
        document.cookie = "token=" + token + ";path=/";
    }

    // Only send request if the user entered something
    if (text.length > 0) {
        addChatBubble(text.toString(), true);

        // Send HTTP POST request to "/ask-gemini" with parameter "query" of value text.toString()
        const xhr = new XMLHttpRequest();
        xhr.open("POST", API_ENDPOINT + "/ask-gemini", true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                // Check if the request is finished
                if (xhr.status === 200) {
                    // Handle the successful response here
                    console.log(xhr.responseText);

                    addChatBubble(xhr.responseText, false);
                } else {
                    try {
                        // Handle the error response here
                        console.error("XHR request failed with status:", xhr.status);
    
                        if ( xhr.responseText ) {
                            addChatBubble(xhr.responseText, false);
                        } else {
                            addChatBubble("❌" + xhr.status + " " + xhr.statusText, false);
                        }
                    } catch (e) {
                        console.error(xhr)
                        console.error(e)
                    }
                }

                isXhrLoading.value = false;
            }
        };
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        isXhrLoading.value = true;
        xhr.send("message=" + encodeURIComponent(text.toString()) + "&token=" + encodeURIComponent(token));

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
    const xhr = new XMLHttpRequest();
    xhr.open("POST", API_ENDPOINT + "/reset", true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            // Check if the request is finished
            if (xhr.status === 200) {
                // Handle the successful response here
                console.log(xhr.responseText);

                // Reset chat container content
                chatContainer.innerHTML = '';

                addChatBubble(xhr.responseText, false);
            } else {
                try {
                    // Handle the error response here
                    console.error("XHR request failed with status:", xhr.status);

                    if ( xhr.responseText ) {
                        addChatBubble(xhr.responseText, false);
                    } else {
                        addChatBubble("❌" + xhr.status + " " + xhr.statusText, false);
                    }
                } catch (e) {
                    console.error(xhr)
                    console.error(e)
                }
            }

            isXhrLoading.value = false;
        }
    };
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    isXhrLoading.value = true;
    xhr.send("token=" + encodeURIComponent(token));
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

