<template>
  <div class="load-container">
    <h2>Загрузите файлы</h2>
    
    <button class="load-btn" @click="selectFiles">
      Загрузить файлы
    </button>
    
    <input
      ref="fileInput"
      type="file"
      multiple
      @change="handleFileChange"
      class="file-input"
    />
    
    <button class="load-btn" @click="loadFilesFromServer">
      Загрузить файлы с сервера
    </button>

    <!-- Список файлов с сервера -->
    <ul v-if="files.length > 0">
      <li v-for="(file, index) in files" :key="index">{{ file }}</li>
    </ul>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "LoadFiles",
  data() {
    return {
      files: [],  // Список файлов с сервера
    };
  },
  methods: {
    selectFiles() {
      this.$refs.fileInput.click();
    },
    handleFileChange(event) {
      const files = event.target.files;
      // Загрузка файлов на сервер
      this.uploadFiles(files);
    },
    async uploadFiles(files) {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append("file", files[i]);
      }

      try {
        await axios.post("http://127.0.0.1:8000/upload/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        alert("Файлы загружены");
        this.loadFilesFromServer();  // Обновить список файлов
      } catch (error) {
        console.error("Ошибка при загрузке файлов:", error);
      }
    },
    async loadFilesFromServer() {
      try {
        const response = await axios.get("http://127.0.0.1:8000/files/");
        this.files = response.data.files;
      } catch (error) {
        console.error("Ошибка при получении файлов с сервера:", error);
      }
    }
  }
};
</script>

<style scoped>
.load-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background-color: #333;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  color: white; /* Цвет всего текста белый */
}

h2 {
  background-color: #333;
  font-size: 24px;
  margin-bottom: 20px;
  color: white; /* Цвет заголовка белый */
}

/* Контейнер для кнопок, для их размещения в линию */
.button-container {
  display: flex;
  justify-content: center; /* Центрирует кнопки по горизонтали */
  gap: 30px; /* Увеличенные отступы между кнопками */
  background-color: #333; /* Серый фон для контейнера */
  padding: 15px 30px; /* Добавим отступы для контейнера */
  border-radius: 10px; /* Увеличим закругление фона */
}

.load-btn {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 12px; /* Увеличенное закругление кнопок */
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.load-btn:hover {
  background-color: #0056b3;
}

.file-input {
  display: none;
}
</style>