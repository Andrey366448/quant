<template>
  <div id="app">
    <h1 class="header-title">Обработка графа квантовым алгоритмом, РТУ МИРЭА команда "Краники"</h1>
    
    <LoadFiles />
    <FileView />
    <QuantVisualise />
  </div>
</template>

<script>
import LoadFiles from './components/load.vue'
import FileView from './components/file_view.vue'
import QuantVisualise from './components/quant_visualise.vue'

export default {
  name: 'App',
  components: {
    LoadFiles,
    FileView,
    QuantVisualise
  }
}
</script>

<style>
/* ====== Темная тема, аккуратные отступы и нормальная прокрутка ====== */
:root{
  --bg: #0f1216;
  --panel: #161a20;
  --panel-2:#1b2027;
  --text:#e8edf4;
  --muted:#9aa7b6;
  --primary:#5aa2ff;
  --primary-600:#3f7ef7;
  --border: rgba(255,255,255,.08);
  --radius: 14px;
  --shadow: 0 10px 30px rgba(0,0,0,.35);
  --shadow-soft: 0 6px 20px rgba(0,0,0,.28);
  --trans: .22s cubic-bezier(.2,.8,.2,1);
}

/* Плавная прокрутка по якорям */
html { scroll-behavior: smooth; }

* { box-sizing: border-box; }

/* База страницы */
html, body {
  height: 100%;
  margin: 0;
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(90,162,255,.12), transparent 60%),
    radial-gradient(900px 500px at 110% 0%, rgba(152,103,255,.10), transparent 60%),
    var(--bg);
  color: var(--text);
  font: 500 16px/1.6 Avenir, Helvetica, Arial, system-ui, -apple-system, Segoe UI, Roboto, "Noto Sans", sans-serif;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Тонкие скроллбары (Firefox + WebKit) */
:root { scrollbar-width: thin; scrollbar-color: rgba(255,255,255,.24) transparent; }
*::-webkit-scrollbar { width: 10px; height: 10px; }
*::-webkit-scrollbar-track { background: transparent; }
*::-webkit-scrollbar-thumb {
  background-color: rgba(255,255,255,.18);
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: padding-box;
}
*::-webkit-scrollbar-thumb:hover { background-color: rgba(255,255,255,.28); }

/* Контейнер приложения */
#app{
  width: min(980px, 92vw);
  margin: 24px auto 64px;
  padding: 24px;
  background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,0)) , var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* “Стеклянная” шапка, остаётся на виду */
.header-title{
  margin: 0;
  width: 100%;
  padding: 18px 22px;
  font-weight: 800;
  letter-spacing: .2px;
  text-align: center;
  font-size: clamp(22px, 1.8vw + 16px, 34px);
  color: var(--text);
  background:
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,0)),
    var(--panel-2);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) - 2px);
  box-shadow: var(--shadow-soft);
  position: sticky;
  top: 12px;
  z-index: 10;
  backdrop-filter: saturate(115%) blur(6px);
  -webkit-backdrop-filter: saturate(115%) blur(6px);
}

/* Блок кнопок */
.button-container{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  width: 100%;
  background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0)) , var(--panel-2);
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) - 2px);
}

/* Кнопка загрузки / действия */
.load-btn{
  -webkit-tap-highlight-color: transparent;
  flex: 1 1 240px;
  background: linear-gradient(180deg, var(--primary), var(--primary-600));
  color: #fff;
  border: 0;
  padding: 12px 18px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: .2px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform var(--trans), box-shadow var(--trans), filter var(--trans);
  box-shadow: 0 8px 18px rgba(63,126,247,.35), inset 0 1px 0 rgba(255,255,255,.18);
}
.load-btn:hover{ transform: translateY(-1px); box-shadow: 0 10px 22px rgba(63,126,247,.42); filter: brightness(1.03); }
.load-btn:active{ transform: translateY(0); box-shadow: 0 6px 14px rgba(63,126,247,.32); }
.load-btn:disabled{ opacity:.6; cursor:not-allowed; }

/* Фокус видимый и приятный */
:focus-visible{
  outline: 2px solid rgba(90,162,255,.9);
  outline-offset: 2px;
  border-radius: 10px;
}

/* Карточный стиль для внутренних блоков/компонентов (если добавите класс .card) */
.card{
  width: 100%;
  background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0)) , var(--panel);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) - 2px);
  padding: 16px;
  box-shadow: var(--shadow-soft);
}

/* Текстовые элементы */
h2, h3{
  margin: 10px 0 6px;
  line-height: 1.25;
}
p{ margin: 0 0 10px; color: var(--text); }
small, .muted{ color: var(--muted); }

/* Ссылки */
a{
  color: var(--primary);
  text-decoration: none;
  transition: color var(--trans), opacity var(--trans);
}
a:hover{ opacity: .9; text-decoration: underline; }

/* Выделение текста */
::selection{ background: rgba(90,162,255,.28); color: #fff; }

/* Мелкие анимации + уважение к prefers-reduced-motion */
@keyframes fadeInUp{
  from{ opacity:0; transform: translateY(6px); }
  to{ opacity:1; transform: translateY(0); }
}
#app > * { animation: fadeInUp .5s var(--trans) both; }
@media (prefers-reduced-motion: reduce){
  *{ animation: none !important; transition: none !important; }
}

/* Адаптивность */
@media (max-width: 560px){
  #app{ padding: 16px; margin: 12px auto 40px; }
  .header-title{ top: 8px; padding: 14px 16px; }
}

</style>

