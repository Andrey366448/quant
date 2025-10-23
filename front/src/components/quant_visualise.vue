<template>
  <div class="quant-container">
    <h2>Запуск алгоритмов</h2>

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

    <!-- ===== QI: визуализации квант-вдохновлённого ===== -->
    <div class="gallery-container">
      <div class="controls">
        <button class="btn" @click="toggleListQi">
          {{ showListQi ? 'Скрыть визуализации квант-вдохновлённого алгоритма' : 'Показать визуализации квант-вдохновлённого алгоритма' }}
        </button>
        <button
          v-if="showListQi"
          class="btn secondary"
          @click="downloadCsvQi"
          aria-label="Скачать submission.csv и total_time.csv (QI)"
          title="Скачать submission.csv и total_time.csv (QI)"
          style="margin-left: 8px;"
        >
          Скачать результаты CSV
        </button>
      </div>

      <div v-if="showListQi" class="content">
        <div class="list">
          <div class="list-title">Файлы (PNG)</div>
          <ul class="files">
            <li
              v-for="(f, idx) in filesQi"
              :key="'qi-'+idx"
              :class="{ active: f === selectedQi }"
              @click="selectQi(f)"
              title="Открыть превью"
            >
              {{ f }}
            </li>
            <li v-if="filesQi.length === 0" class="empty">Пока пусто</li>
          </ul>
          <button class="btn secondary" @click="refreshQi" :disabled="loadingListQi">
            {{ loadingListQi ? 'Обновляю...' : 'Обновить список' }}
          </button>
        </div>

        <div class="preview" v-if="selectedQi && showPreviewQi">
          <div class="preview-header">
            <div class="preview-title" :title="selectedQi">{{ selectedQi }}</div>
            <button class="close-btn" @click="closePreviewQi" aria-label="Закрыть превью">×</button>
          </div>
          <div class="preview-body">
            <img
              :src="imageUrlQi(selectedQi)"
              alt="preview"
              class="img"
              @error="onImgError"
            />
          </div>
          <div class="hint">Кликни по имени файла слева, чтобы открыть другое изображение</div>
        </div>
        <div class="preview placeholder" v-else>Выберите файл слева</div>
      </div>
    </div>

    <!-- ===== QF: визуализации полного квантового ===== -->
    <div class="gallery-container">
      <div class="controls">
        <button class="btn" @click="toggleListQf">
          {{ showListQf ? 'Скрыть визуализации полного квантового алгоритма' : 'Показать визуализации полного квантового алгоритма' }}
        </button>
        <button
          v-if="showListQf"
          class="btn secondary"
          @click="downloadCsvQf"
          aria-label="Скачать submission.csv и total_time.csv (QF)"
          title="Скачать submission.csv и total_time.csv (QF)"
          style="margin-left: 8px;"
        >
          Скачать  результаты CSV
        </button>
      </div>

      <div v-if="showListQf" class="content">
        <div class="list">
          <div class="list-title">Файлы (PNG)</div>
          <ul class="files">
            <li
              v-for="(f, idx) in filesQf"
              :key="'qf-'+idx"
              :class="{ active: f === selectedQf }"
              @click="selectQf(f)"
              title="Открыть превью"
            >
              {{ f }}
            </li>
            <li v-if="filesQf.length === 0" class="empty">Пока пусто</li>
          </ul>
          <button class="btn secondary" @click="refreshQf" :disabled="loadingListQf">
            {{ loadingListQf ? 'Обновляю...' : 'Обновить список' }}
          </button>
        </div>

        <div class="preview" v-if="selectedQf && showPreviewQf">
          <div class="preview-header">
            <div class="preview-title" :title="selectedQf">{{ selectedQf }}</div>
            <button class="close-btn" @click="closePreviewQf" aria-label="Закрыть превью">×</button>
          </div>
          <div class="preview-body">
            <img
              :src="imageUrlQf(selectedQf)"
              alt="preview"
              class="img"
              @error="onImgError"
            />
          </div>
          <div class="hint">Кликни по имени файла слева, чтобы открыть другое изображение</div>
        </div>
        <div class="preview placeholder" v-else>Выберите файл слева</div>
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

      // QI
      showListQi: false,
      filesQi: [],
      selectedQi: "",
      showPreviewQi: false,
      loadingListQi: false,
      baseListUrlQi: "http://127.0.0.1:8000/visualised_qi/",
      baseImgUrlQi: "http://127.0.0.1:8000/static/visualised_qi/",

      // QF
      showListQf: false,
      filesQf: [],
      selectedQf: "",
      showPreviewQf: false,
      loadingListQf: false,
      baseListUrlQf: "http://127.0.0.1:8000/visualised_qf/",
      baseImgUrlQf: "http://127.0.0.1:8000/static/quant_full/visualised_qf/",
    };
  },
  computed: {
    hasGraphMinQi() {
      return this.filesQi.includes("graph_min.png");
    },
    hasGraphMinQf() {
      return this.filesQf.includes("graph_min.png");
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
        // опционально: автообновление списка
        if (this.showListQi) this.refreshQi();
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
        if (this.showListQf) this.refreshQf();
      } catch (e) {
        console.error(e);
        this.error = "Ошибка при запуске полного квантового алгоритма.";
      } finally {
        this.loadingFull = false;
      }
    },

    // ===== QI gallery =====
    toggleListQi() {
      this.showListQi = !this.showListQi;
      if (this.showListQi && this.filesQi.length === 0) this.refreshQi();
    },
    async refreshQi() {
      this.loadingListQi = true;
      try {
        const { data } = await axios.get(this.baseListUrlQi);
        this.filesQi = data.files || [];
        if (!this.filesQi.includes(this.selectedQi)) {
          this.selectedQi = "";
          this.showPreviewQi = false;
        }
      } catch (e) {
        console.error("Не удалось получить список PNG (QI):", e);
        alert("Ошибка при получении изображений (QI).");
      } finally {
        this.loadingListQi = false;
      }
    },
    selectQi(f) {
      this.selectedQi = f;
      this.showPreviewQi = true;
    },
    imageUrlQi(filename) {
      return `${this.baseImgUrlQi}${encodeURIComponent(filename)}?t=${Date.now()}`;
    },
    closePreviewQi() {
      this.showPreviewQi = false;
    },

    // ===== QF gallery =====
    toggleListQf() {
      this.showListQf = !this.showListQf;
      if (this.showListQf && this.filesQf.length === 0) this.refreshQf();
    },
    async refreshQf() {
      this.loadingListQf = true;
      try {
        const { data } = await axios.get(this.baseListUrlQf);
        this.filesQf = data.files || [];
        if (!this.filesQf.includes(this.selectedQf)) {
          this.selectedQf = "";
          this.showPreviewQf = false;
        }
      } catch (e) {
        console.error("Не удалось получить список PNG (QF):", e);
        alert("Ошибка при получении изображений (QF).");
      } finally {
        this.loadingListQf = false;
      }
    },
    selectQf(f) {
      this.selectedQf = f;
      this.showPreviewQf = true;
    },
    imageUrlQf(filename) {
      return `${this.baseImgUrlQf}${encodeURIComponent(filename)}?t=${Date.now()}`;
    },
    closePreviewQf() {
      this.showPreviewQf = false;
    },

    // общие
    onImgError() {
      alert("Не удалось загрузить изображение. Проверьте, что файл существует.");
    },

    // ===== скачивание CSV =====
    downloadCsvQi() {
      // ZIP с submission.csv (или submissions.csv) + total_time.csv из корня back/
      window.location.href = "http://127.0.0.1:8000/download/csv/bundle/qi";
    },
    downloadCsvQf() {
      // ZIP с CSV из back/quant_full/
      window.location.href = "http://127.0.0.1:8000/download/csv/bundle/qf";
    },

    // быстрый доступ к минимальному графу
    openGraphMinQi() {
      if (!this.hasGraphMinQi) return;
      this.selectedQi = "graph_min.png";
      this.showPreviewQi = true;
      this.showListQi = true;
      this.$nextTick(() => this.$el.querySelector(".preview")?.scrollIntoView({ behavior: "smooth", block: "start" }));
    },
    openGraphMinQf() {
      if (!this.hasGraphMinQf) return;
      this.selectedQf = "graph_min.png";
      this.showPreviewQf = true;
      this.showListQf = true;
      this.$nextTick(() => this.$el.querySelectorAll(".preview")?.[1]?.scrollIntoView({ behavior: "smooth", block: "start" }));
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
  font-size: 12px;
}
</style>