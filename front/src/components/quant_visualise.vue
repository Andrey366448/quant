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
/* локальные дефолты-панели на случай, если глобально не заданы */
.quant-container{
  display: grid;
  gap: 16px;
  --panel: rgba(17,21,27,.92);
  --panel-2: rgba(17,21,27,.78);
  color: var(--text, #e8edf4);
}

/* Кнопочные ряды — в линию, с переносом при нехватке места */
.button-row,
.controls{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

/* Базовая кнопка в стиле образца */
.action-btn,
.btn{
  -webkit-tap-highlight-color: transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 18px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: .2px;
  border-radius: 12px;
  border: 0;
  cursor: pointer;
  color: #fff;
  background: linear-gradient(180deg, var(--primary, #5aa2ff), var(--primary-600, #3f7ef7));
  transition:
    transform var(--trans, .22s cubic-bezier(.2,.8,.2,1)),
    box-shadow var(--trans, .22s cubic-bezier(.2,.8,.2,1)),
    filter var(--trans, .22s cubic-bezier(.2,.8,.2,1));
  box-shadow:
    0 8px 18px rgba(63,126,247,.35),
    inset 0 1px 0 rgba(255,255,255,.18);
}
.action-btn:hover,
.btn:hover{
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(63,126,247,.42), inset 0 1px 0 rgba(255,255,255,.22);
  filter: brightness(1.03);
}
.action-btn:active,
.btn:active{ transform: translateY(0); box-shadow: 0 6px 14px rgba(63,126,247,.32); }
.action-btn:disabled,
.btn:disabled{ opacity:.6; cursor:not-allowed; }

/* Варианты */
.btn.secondary{
  color: var(--text, #e8edf4);
  background:
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.04)),
    var(--panel-2);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  box-shadow: var(--shadow-soft, 0 6px 20px rgba(0,0,0,.28));
}
.btn.secondary:hover{ border-color: rgba(255,255,255,.14); transform: translateY(-1px); }

.btn.accent{
  background: linear-gradient(180deg, #7b63ff, #6b4bff);
  box-shadow: 0 8px 18px rgba(107,75,255,.35), inset 0 1px 0 rgba(255,255,255,.18);
}

/* Сообщения */
.message{ color:#34d399; font-weight:600; }
.error{ color:#f87171; font-weight:600; }

/* Контент галереи */
.gallery-container .content{
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
  align-items: start;
  margin: 20px 0 6px;
}

/* Список файлов — карточный стиль */
.list{
  background:
    linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0)),
    var(--panel, #141a21);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  border-radius: calc(var(--radius, 14px) - 2px);
  padding: 12px;
  box-shadow: var(--shadow-soft, 0 6px 20px rgba(0,0,0,.28));
}
.list-title{ font-weight:700; margin-bottom:8px; color: var(--muted, #9aa7b6); }
.files{
  list-style:none;
  margin:0 0 8px 0;
  padding:0;
  max-height:50vh;
  overflow:auto;
}
.files li{
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  transition: background var(--trans, .22s cubic-bezier(.2,.8,.2,1)), border-color var(--trans, .22s cubic-bezier(.2,.8,.2,1));
}
.files li:hover{ background: rgba(255,255,255,.06); }
.files li.active{
  background: rgba(90,162,255,.14);
  border: 1px solid rgba(90,162,255,.35);
}
.files li.empty{ cursor: default; opacity:.7; }

/* Превью */
.preview{
  background:
    linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0)),
    var(--panel, #141a21);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  border-radius: calc(var(--radius, 14px) - 2px);
  padding: 12px;
  min-height: 200px;
  width: 100%;
  box-shadow: var(--shadow-soft, 0 6px 20px rgba(0,0,0,.28));
}
.preview.placeholder{ display:grid; place-items:center; color: var(--muted, #9aa7b6); }

.preview-header{
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.preview-title{
  font-weight:700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.close-btn{
  border: 1px solid var(--border, rgba(255,255,255,.08));
  background:
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.04)),
    var(--panel-2);
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  color: var(--text, #e8edf4);
  transition: transform var(--trans, .22s cubic-bezier(.2,.8,.2,1));
}
.close-btn:hover{ transform: translateY(-1px); }
.close-btn:active{ transform: translateY(0); }

.preview-body{
  display: grid;
  place-items: center;
  max-height: 60vh;
  overflow: hidden;
}
.img{
  max-width: 100%;
  max-height: 60vh;
  height: auto;
  object-fit: contain;
  display: block;
  border-radius: 10px;
}

/* Подсказка */
.hint{ margin-top: 8px; font-size: 12px; color: var(--muted, #9aa7b6); }

/* Красивый фокус */
:focus-visible{
  outline: 2px solid rgba(90,162,255,.9);
  outline-offset: 2px;
  border-radius: 10px;
}

/* Адаптивность */
@media (max-width: 720px){
  .gallery-container .content{ grid-template-columns: 1fr; }
}
</style>
