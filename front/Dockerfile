# Сборка фронта
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Сервер статических файлов
FROM nginx:1.28-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# при необходимости: COPY ./nginx.conf /etc/nginx/conf.d/default.conf
