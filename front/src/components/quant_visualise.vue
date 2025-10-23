<template>
  <div class="quant-container">
    <h2>Квантовая визуализация</h2>

    <!-- КНОПКИ ЗАПУСКА АЛГОРИТМОВ -->
    <div class="button-row">
      <button class="action-btn" :disabled="loadingInspired" @click="runQuantInspired">
        {{ loadingInspired ? 'Запуск...' : 'Квант-вдохновлённый' }}
      </button>
      <button class="action-btn" :disabled="loadingFull" @click="runQuantFull">
        {{ loadingFull ? 'Запуск...' : 'Полный квантовый' }}
      </button>
    </div>

    <p v-if="message" class="message">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <!-- ГАЛЕРЕЯ PNG ИЗ visualised_qi -->
    <div class="gallery-container">
      <div class="controls">
        <button class="btn" @click="toggleList">
          {{ showList ? 'Скрыть визуализации' : 'Показать визуализации' }}
        </button>
      </div>
      <!-- Кнопка видна только если есть graph_min.png -->
        <button
          v-if="hasGraphMin"
          class="btn accent"
          @click="openGraphMin"
          aria-label="Открыть граф с минимальным временем"
        >
          граф с минимальным временем
        </button>

      <div v-if="showList" class="content">
        <div class="list">
          <div class="list-title">Файлы (PNG)</div>
          <ul class="files">
            <li
              v-for="(f, idx) in files"
              :key="idx"
              :class="{ active: f === selected }"
              @click="select(f)"
              title="Открыть превью"
            >
              {{ f }}
            </li>
            <li v-if="files.length === 0" class="empty">Пока пусто</li>
          </ul>
          <button class="btn secondary" @click="refresh" :disabled="loadingList">
            {{ loadingList ? 'Обновляю...' : 'Обновить список' }}
          </button>
        </div>

        <!-- Компактное превью с кнопкой закрытия -->
        <div class="preview" v-if="selected && showPreview">
          <div class="preview-header">
            <div class="preview-title" :title="selected">{{ selected }}</div>
            <button class="close-btn" @click="closePreview" aria-label="Закрыть превью">×</button>
          </div>

          <div class="preview-body">
            <img
              :src="imageUrl(selected)"
              alt="preview"
              class="img"
              @error="onImgError"
            />
          </div>

          <div class="hint">Кликни по имени файла слева, чтобы открыть другое изображение</div>
        </div>

        <div class="preview placeholder" v-else>
          Выберите файл слева
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "QuantVisualise",
  data() {
    return {
      // запуск алгоритмов
      loadingInspired: false,
      loadingFull: false,
      message: "",
      error: "",

      // галерея
      showList: false,
      files: [],
      selected: "",
      showPreview: false,
      loadingList: false,

      baseListUrl: "http://127.0.0.1:8000/visualised_qi/",
      baseImgUrl: "http://127.0.0.1:8000/static/visualised_qi/",
    };
  },
  computed: {
    // Есть ли в списке graph_min.png
    hasGraphMin() {
      return this.files.includes("graph_min.png");
    },
  },
  methods: {
    // ===== запуск алгоритмов =====
    async runQuantInspired() {
      this.message = "";
      this.error = "";
      this.loadingInspired = true;
      try {
        const res = await axios.post("http://127.0.0.1:8000/quant_inspired/");
        this.message = res.data?.message ?? "Готово.";
      } catch (e) {
        console.error(e);
        this.error = "Ошибка при запуске квант-вдохновлённого алгоритма.";
      } finally {
        this.loadingInspired = false;
      }
    },
    async runQuantFull() {
      this.message = "";
      this.error = "";
      this.loadingFull = true;
      try {
        const res = await axios.post("http://127.0.0.1:8000/quant_full/");
        this.message = res.data?.message ?? "Готово.";
      } catch (e) {
        console.error(e);
        this.error = "Ошибка при запуске полного квантового алгоритма.";
      } finally {
        this.loadingFull = false;
      }
    },

    // ===== галерея PNG =====
    toggleList() {
      this.showList = !this.showList;
      if (this.showList && this.files.length === 0) this.refresh();
    },
    async refresh() {
      this.loadingList = true;
      try {
        const { data } = await axios.get(this.baseListUrl);
        this.files = data.files || [];
        if (!this.files.includes(this.selected)) {
          this.selected = "";
          this.showPreview = false;
        }
      } catch (e) {
        console.error("Не удалось получить список PNG:", e);
        alert("Ошибка при получении списка изображений.");
      } finally {
        this.loadingList = false;
      }
    },
    select(f) {
      this.selected = f;
      this.showPreview = true; // открываем компактное превью при выборе
    },
    imageUrl(filename) {
      // cache-busting
      return `${this.baseImgUrl}${encodeURIComponent(filename)}?t=${Date.now()}`;
    },
    closePreview() {
      this.showPreview = false;
    },
    onImgError() {
      alert("Не удалось загрузить изображение. Проверьте, что файл существует.");
    },

    // Открыть graph_min.png, если он есть
    openGraphMin() {
      if (!this.hasGraphMin) return;
      this.selected = "graph_min.png";
      this.showPreview = true;
      this.showList = true; // раскроем список, чтобы было видно контекст
      this.$nextTick(() => {
        const el = this.$el.querySelector(".preview");
        el?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    },
  },
};
</script>

<style scoped>
.quant-container {
  display: grid;
  gap: 16px;
}

.button-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn,
.btn {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid #ddd;
  background: #f7f7f7;
  cursor: pointer;
}
.action-btn:disabled,
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message { color: #0f7b0f; }
.error { color: #b00020; }

.gallery-container .content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  align-items: start;
}

/* Список файлов */
.list {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}
.list-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.files {
  list-style: none;
  margin: 0 0 8px 0;
  padding: 0;
  max-height: 50vh;
  overflow: auto;
}
.files li {
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.files li:hover { background: #f3f4f6; }
.files li.active {
  background: #e8f0fe;
  border: 1px solid #cfe1ff;
}
.files li.empty {
  color: #888;
  cursor: default;
}

/* Превью (компактное) */
.preview {
  border: 1px solid #eee;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
  min-height: 160px;
  width: min(90vw, 560px);   /* держим компактным */
}

.preview.placeholder {
  display: grid;
  place-items: center;
  color: #666;
}

.preview-header {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.preview-title {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.close-btn {
  border: none;
  background: #f3f4f6;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}
.close-btn:hover { background: #e5e7eb; }

.preview-body {
  /* рамка под картинку, чтобы она точно не вылезала */
  display: grid;
  place-items: center;
  max-height: 60vh;
  overflow: hidden;
}

/* Картинка никогда не выходит за пределы блока/вьюпорта */
.img {
  max-width: 100%;
  max-height: 60vh;
  height: auto;
  object-fit: contain;
  display: block;
}

/* маленькая подсказка */
.hint {
  margin-top: 8px;
  color: #6b7280;
  font-size: 12px;
}
</style>