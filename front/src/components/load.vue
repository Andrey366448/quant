<template>
  <div class="load-container-header">
    <h2>Загрузите файлы</h2>
    <div class="load-container">
    <!-- Кнопка загрузки файлов с клиента-->
    <button class="load-btn" @click="selectFiles">
      Загрузить исходные данные data.csv
    </button>
    
    <input
      ref="fileInput"
      type="file"
      multiple
      @change="handleFileChange"
      class="file-input"
    />
    
    <!-- Кнопка загрузки файлов с сервера -->
    <button class="load-btn" @click="loadFilesFromServer">
      Загрузить файлы с сервера
    </button>

    <!-- Кнопка для очистки всех файлов -->
    <button class="load-btn" @click="clearFiles">
      Очистить исходные данные
    </button>

    <!-- Список файлов с сервера -->
    <ul v-if="files.length > 0">
      <li v-for="(file, index) in files" :key="index">{{ file }}</li>
    </ul>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "LoadFiles",
  data() {
    return {
      files: [],
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
        this.loadFilesFromServer();
      } catch (error) {
        console.error("Ошибка при загрузке файлов:", error);
      }
    },

    async loadFilesFromServer() {
      try {
        const response = await axios.post("http://127.0.0.1:8000/upload/fromserver/");

       alert(response.data.message);
      } catch (error) {
          console.error("Ошибка при загрузке файлов с сервера:", error);
        alert("Ошибка при загрузке файлов.");
      }   
    },

    // Метод для очистки всех файлов
    async clearFiles() {
      try {
        const response = await axios.delete("http://127.0.0.1:8000/upload/clear/");
        alert(response.data.message);
        this.files = [];
      } catch (error) {
        console.error("Ошибка при очистке файлов с сервера:", error);
        alert("Ошибка при очистке файлов.");
      }
    },
  }
};
</script>

<style scoped>
.load-container-header 

.load-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  color: white;
}

h2 {
  font-size: 24px;
  margin-bottom: 20px;
  color: white;
}

.button-container {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding: 15px 30px;
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
}

.load-btn:hover {
  background-color: #0056b3;
}

.file-input {
  display: none;
}
</style>