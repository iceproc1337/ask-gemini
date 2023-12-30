<script setup>
import { onBeforeUnmount, onMounted } from "vue";
import * as marked from "marked";

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT;

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
    // xhr.withCredentials = true;
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
  // xhr.withCredentials = true;
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


onMounted(() => {
  const form = document.getElementById('chat-form');
  const menuButton = document.querySelector('.menu-button');
  const chatContainer = document.querySelector('.chat-container');
  const resetButton = document.querySelector('.menu-item-reset');

  menuButton.addEventListener('click', toggleMenu);
  chatContainer.addEventListener('click', copyCodeToClipboard);
  form.addEventListener('submit', handleFormSubmit);
  resetButton.addEventListener('click', resetChat);

  scrollChatContainerToBottom();
})

onBeforeUnmount(() => {
  const form = document.getElementById('chat-form');
  const menuButton = document.querySelector('.menu-button');
  const chatContainer = document.querySelector('.chat-container');
  const resetButton = document.querySelector('.menu-item-reset');

  menuButton.removeEventListener('click', toggleMenu);
  chatContainer.removeEventListener('click', copyCodeToClipboard);
  form.removeEventListener('submit', handleFormSubmit);
  resetButton.removeEventListener('click', resetChat);
});

</script>

<template>
  <div class="title-wrapper">
    <div class="title">
      <div class="title-text">Ask Gemini!</div>
    </div>
    <button class="menu-button">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
        <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
      </svg>
      <div class="menu-items">
        <div class="menu-item menu-item-reset">Reset</div>
      </div>
    </button>
  </div>
  <div class="chat-container">
    <div class="chat-bubble chat-bubble-left">
      <p>Hello! I am a large language model, trained by Google. I am designed to understand and generate human
        language, and to perform many kinds of tasks that require language understanding and generation.</p>
      <p>Here is a brief summary of what I can do:</p>
      <ul>
        <li><strong>Answer questions:</strong> I can answer questions on a wide range of topics, including
          science, history, geography, culture, and current events.</li>
        <li><strong>Translate languages:</strong> I can translate text and speech between over 100 languages.
        </li>
        <li><strong>Write different types of content:</strong> I can write articles, blog posts, stories, poems,
          and more.</li>
        <li><strong>Generate creative ideas:</strong> I can help you come up with new ideas for projects,
          products, and marketing campaigns.</li>
        <li><strong>Summarize information:</strong> I can summarize long documents, articles, and videos into
          shorter, more concise pieces.</li>
        <li><strong>Help with research:</strong> I can help you find information on any topic, and I can also
          help you organize and analyze data.</li>
        <li><strong>Write and debug code:</strong> I can write code in many different programming languages, and
          I can also help you debug code.</li>
        <li><strong>Control smart home devices:</strong> I can control smart home devices such as lights,
          thermostats, and door locks.</li>
        <li><strong>Play games:</strong> I can play a variety of games, including chess, checkers, and trivia.
        </li>
        <li><strong>Provide entertainment:</strong> I can tell jokes, sing songs, and play music.</li>
        <li><strong>Simulate human conversation:</strong> I can simulate human conversation and answer your
          questions in a natural and conversational way.</li>
      </ul>
      <p>I am still under development, but I am learning new things every day. I am always looking for ways to
        improve my skills and knowledge so that I can better assist you.</p>
      <p>I am excited to help you with your tasks and to answer your questions. Please let me know if you have any
        questions or if there is anything I can help you with.</p>
    </div>
  </div>
  <div class="input-container">
    <form id="chat-form">
      <input class="input-field" type="text" placeholder="Ask something..." id="input-field">
      <input type="submit" style="display: none;">
    </form>
  </div>
</template>
