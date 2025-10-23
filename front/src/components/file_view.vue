<template>
  <div class="file-view-container">
    <!-- Кнопка для отображения списка файлов -->
    <button class="load-btn" @click="toggleFileList">
      {{ showFiles ? 'Скрыть список файлов' : 'Посмотреть файлы' }}
    </button>

    <!-- Кнопка для обновления списка файлов -->
    <button v-if="showFiles" class="load-btn" @click="loadFilesFromServer">
      Обновить список файлов
    </button>

    <!-- Кнопка для скачивания всех файлов -->
    <button v-if="showFiles" class="load-btn" @click="downloadFiles">
      Скачать все файлы
    </button>

    <!-- Список загруженных файлов, показывается при нажатии на кнопку -->
    <div v-if="showFiles" class="file-list">
      <ul>
        <li v-for="(file, index) in files" :key="index">
          {{ file }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "FileView",
  data() {
    return {
      showFiles: false,
      files: []
    };
  },
  methods: {
    // Метод для переключения видимости списка файлов
    toggleFileList() {
      this.showFiles = !this.showFiles;
      if (this.showFiles) {
        this.loadFilesFromServer();
      }
    },

    // Метод для получения файлов с сервера
    async loadFilesFromServer() {
      try {
        const response = await axios.get("http://127.0.0.1:8000/upload/");
        console.log("Полученные файлы:", response.data.files);
        this.files = response.data.files;
      } catch (error) {
        console.error("Ошибка при получении файлов с сервера:", error);
      }
    },

    // Метод для скачивания всех файлов в архиве клиенту
    async downloadFiles() {
      try {
        const response = await axios.get("http://127.0.0.1:8000/download/", {
          responseType: 'blob', 
        });

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'uploads.zip');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link); 
      } catch (error) {
        console.error("Ошибка при скачивании файлов:", error);
        alert("Ошибка при скачивании файлов.");
      }
    }
  }
};
</script>

<style scoped>
.file-view-container {
  width: 100%;
  max-width: 600px;
  background-color: #333;
  color: white;
  padding: 20px;
  margin-top: 20px;
  border-radius: 10px;
}

.load-btn {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 100%;
}

.load-btn:hover {
  background-color: #0056b3;
}

.file-list {
  margin-top: 20px;
}

.file-list ul {
  list-style-type: none;
  padding: 0;
}

.file-list li {
  background-color: #444;
  padding: 10px;
  margin-bottom: 5px;
  border-radius: 5px;
}
</style>
