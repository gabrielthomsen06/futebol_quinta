# Imagem de desenvolvimento: o Vite roda com hot reload sobre o bind mount.
# O estágio de build para produção entra quando houver deploy — não faz parte do MVP.
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
