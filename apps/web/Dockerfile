FROM node:22-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY index.html ./
COPY postcss.config.js ./
COPY tailwind.config.ts ./
COPY tsconfig.json ./
COPY tsconfig.node.json ./
COPY vite.config.ts ./
COPY src ./src

EXPOSE 5173

CMD ["npm", "run", "dev"]
