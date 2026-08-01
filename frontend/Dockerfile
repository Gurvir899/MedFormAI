FROM node:22-slim

workdir /app

copy package.json package-lock.json* ./
run npm ci --prefer-offline 2>/dev/null || npm install

copy . .

run npm run build

expose 3000

cmd ["npm", "start"]
