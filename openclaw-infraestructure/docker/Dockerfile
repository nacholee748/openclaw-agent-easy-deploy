FROM node:22-slim

# Instalar git (necesario para clonar OpenClaw)
RUN apt-get update && apt-get install -y git openssl && rm -rf /var/lib/apt/lists/*

# Instalar pnpm
RUN npm install -g pnpm

# Crear usuario sin privilegios
RUN useradd -m -s /bin/bash openclaw

# Clonar, instalar y compilar OpenClaw
USER openclaw
WORKDIR /home/openclaw

RUN git clone https://github.com/openclaw/openclaw.git
WORKDIR /home/openclaw/openclaw
RUN pnpm install && pnpm build

# Crear directorio de configuración
RUN mkdir -p /home/openclaw/.openclaw

ENV NODE_ENV=production

EXPOSE 3000

CMD ["pnpm", "start"]
