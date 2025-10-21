# Stage 1: build the Vue.js app
FROM node:18-alpine AS build-stage
WORKDIR /app

# Если у вас есть package-lock.json — лучше использовать npm ci
COPY package*.json ./
# На случай отсутствия lock-файла: сначала пробуем ci, иначе install
RUN npm ci || npm install

# Копируем остальной код и собираем приложение
COPY . .
# Если проект использует старый node-sass, могут понадобиться build-инструменты:
# RUN apk add --no-cache python3 make g++
RUN npm run build

# Stage 2: Nginx для раздачи статики
FROM nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
