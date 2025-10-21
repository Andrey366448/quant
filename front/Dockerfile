# Stage 1: build the Vue.js app
FROM node:lts-alpine AS build-stage
WORKDIR /app

# Установка зависимостей
COPY package*.json ./
RUN npm install

# Копируем остальной код и собираем приложение
COPY . .
RUN npm run build

# Stage 2: Nginx для сервировки статических файлов
FROM nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Открываем порт 80 и запускаем Nginx
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
