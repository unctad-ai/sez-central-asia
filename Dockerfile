FROM python:3.12-slim
WORKDIR /app
COPY . ./site
RUN mv site/server ./server && rm -f site/Dockerfile site/docker-compose.yml site/nginx.conf site/.dockerignore site/README.md
ENV PORT=80 SITE_DIR=/app/site DATA_DIR=/data PYTHONUNBUFFERED=1
EXPOSE 80
CMD ["python", "server/app.py"]
