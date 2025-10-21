<template>
  <div id="app">
    <!-- Заголовок -->
    <h1 class="header-title">Обработка графа квантовым алгоритмом, РТУ МИРЭА команда "Краники"</h1>
    
    <!-- Контейнер с кнопками и загрузкой файлов -->
    <LoadFiles />

    <!-- Компонент для отображения файлов -->
    <FileView />
  </div>
</template>

<script>
import LoadFiles from './components/load.vue'
import FileView from './components/file_view.vue'  // Импортируем новый компонент

export default {
  name: 'App',
  components: {
    LoadFiles,
    FileView  // Регистрируем компонент для использования
  }
}
</script>

<style>
/* Устанавливаем фон для всей страницы */
html, body {
  display: flex;
  justify-content: center;
  height: 50%;
  margin: 0;
  background-color: #202326; /* Темный фон для всей страницы */
  color: white; /* Белый цвет текста на всей странице */
}

/* Контейнер для содержимого приложения */
#app {
  display: flex;
  flex-direction: column;
  justify-content: center; /* Центрируем по вертикали */
  align-items: center; /* Центрируем по горизонтали */
  width: 100%;
  max-width: 600px; /* Устанавливаем одинаковую ширину для всех блоков */
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  /*background-color: #202326; /* Темный фон для блока */
  margin-top: 60px;
  padding: 20px;
  border-radius: 10px; /* Закругление углов блока */
}

/* Стиль для заголовка */
.header-title {
  font-size: 24px;
  font-weight: bold;
  color: white; /* Белый текст */
  margin-bottom: 20px;
  background-color: #333; /* Темный фон заголовка */
  padding: 15px 30px; /* Отступы для заголовка */
  border-radius: 10px; /* Закругление фона заголовка */
  width: 100%; /* Ширина заголовка по всей ширине контейнера */
  box-sizing: border-box; /* Учитываем отступы внутри элемента */
}

/* Контейнер для кнопок */
.button-container {
  display: flex;
  justify-content: center; /* Центрируем кнопки по горизонтали */
  width: 100%; /* Ширина контейнера кнопок по всей ширине */
  gap: 20px; /* Отступы между кнопками */
  background-color: #333; /* Темный фон для контейнера с кнопками */
  padding: 15px; /* Отступы для контейнера */
  border-radius: 10px; /* Закругление фона контейнера */
  box-sizing: border-box; /* Учитываем отступы внутри элемента */
}

/* Стиль для кнопок */
.load-btn {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 12px; /* Увеличенное закругление кнопок */
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 48%; /* Кнопки занимают одинаковую ширину */
}

.load-btn:hover {
  background-color: #0056b3;
}
</style>

