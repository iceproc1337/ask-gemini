<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { scrollChatContainerToBottom, toggleMenu, copyCodeToClipboard, handleFormSubmit, resetChat } from '@/assets/main.js';

const isXhrLoading = ref(false);
const isDialogOpen = ref(false);
const uploadedImage = ref(null);
const uploadedImageUrl = ref("");

const handleImageUpload = (e) => {
  // Handle image upload logic here
  uploadedImage.value = e.target.files[0];
  uploadedImageUrl.value = URL.createObjectURL(uploadedImage.value);
  isDialogOpen.value = true;
};

const closeDialog = () => {
  const fileUpload = document.getElementById('file-upload');
  isDialogOpen.value = false;
  uploadedImage.value = null;
  uploadedImageUrl.value = "";
  fileUpload.value = null;
};

onMounted(() => {
  const form = document.getElementById('chat-form');
  const menuButton = document.querySelector('.menu-button');
  const chatContainer = document.querySelector('.chat-container');
  const resetButton = document.querySelector('.menu-item-reset');

  menuButton.addEventListener('click', toggleMenu);
  chatContainer.addEventListener('click', copyCodeToClipboard);
  form.addEventListener('submit', (e) => handleFormSubmit(e, isXhrLoading));
  resetButton.addEventListener('click', (e) => resetChat(e, isXhrLoading));

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
  <div class="chat-container" :class="{ 'chat-loading': isXhrLoading }">
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
      <button type="submit" class="input-button send-button">
        <img src="@/assets/send_black_24dp.svg" alt="Send" class="send-icon" />
      </button>
      <label for="file-upload" class="input-button custom-file-upload">
        <img src="@/assets/picture_24dp.svg">
      </label>
      <input id="file-upload" type="file" accept="image/*" @change="handleImageUpload" style="display: none;" />
    </form>
  </div>

  <!-- Dialog Box Overlay -->
  <div class="dialog-box" v-if="isDialogOpen">
    <div class="dialog-header">
      <div class="dialog-title">Attach image</div>
      <button class="dialog-close" @click="closeDialog">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
          <path
            d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
        </svg>
      </button>
    </div>
    <div class="dialog-content">
      <!-- Image preview goes here -->
      <img class="dialog-image-preview" v-if="uploadedImageUrl" :src="uploadedImageUrl" alt="Image Preview">
    </div>
  </div>
</template>

<style scoped>
.dialog-box {
  background-color: white;
  width: 20%;
  max-height: 60%;
  min-width: 200px;
  max-width: 400px;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  position: absolute;
  bottom: 60px;
  right: 18px;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.dialog-title {
  font-size: 18px;
  font-weight: bold;
}

.dialog-image-preview {
  max-width: 100%;
  max-height: 100%;

  object-fit: contain;
}

.dialog-close {
  background-color: transparent;
  border: none;
  cursor: pointer;
}

.dialog-content {
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
  max-height: 100%;
  flex-grow: 1;
  flex-shrink: 1;
  overflow-y: hidden;
}
</style>
