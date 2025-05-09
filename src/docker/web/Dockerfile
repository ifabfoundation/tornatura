FROM node:20-alpine AS build
WORKDIR /app
RUN mkdir -p /app/web
RUN mkdir -p /app/libs
# Copy source files
COPY src/typescript/web/ ./web
COPY src/typescript/libs/ ./libs
WORKDIR /app/web
# Install dependencies
RUN npm install --no-cache
# Build the application
RUN npm run build

FROM nginx
# nginx conf file
COPY --from=build /app/web/nginx/default.conf /etc/nginx/conf.d/default.conf
# copy application from build stage
COPY --from=build --chown=root:www-data /app/web/dist/ /usr/share/nginx/html/
# change files permissions
RUN chmod -R a+rx /usr/share/nginx/html