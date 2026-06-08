# Deployment Guide - Kamka Document Assistant

## Deployment Options

Choose based on your needs:

- **Heroku/Railway**: Quick, easy, no infrastructure knowledge needed
- **Docker**: Containerized deployment, works anywhere
- **AWS/GCP/Azure**: Scalable, production-grade
- **Vercel + Backend**: Best for Next.js frontend + separate backend

## Option 1: Vercel (Frontend) + Railway (Backend)

### Deploy Frontend on Vercel

1. **Push code to GitHub**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/kamka
   git push -u origin main
   ```

2. **Go to [Vercel](https://vercel.com)** and sign in with GitHub

3. **Create new project**:
   - Select your `kamka` repository
   - Select `frontend` as the root directory
   - Add environment variable:
     ```
     NEXT_PUBLIC_API_URL = https://kamka-backend.railway.app
     ```
   - Click Deploy

### Deploy Backend on Railway

1. **Go to [Railway](https://railway.app)** and sign in

2. **Create new project**:
   - Select "Deploy from GitHub"
   - Select your `kamka` repo
   - Configure service
   - Add environment variables (from your `.env`):
     ```
     OPENAI_API_KEY
     PINECONE_API_KEY
     CLOUDINARY_CLOUD_NAME
     CLOUDINARY_API_KEY
     CLOUDINARY_API_SECRET
     MONGODB_URI
     PINECONE_INDEX_NAME=kamka
     ```
   - Deploy

3. **Get your backend URL** from Railway dashboard and update Vercel:
   - Go to Vercel project settings
   - Update `NEXT_PUBLIC_API_URL` environment variable

## Option 2: Docker Deployment

### Create Dockerfiles

**backend/Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

**frontend/Dockerfile**:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next .next
COPY --from=builder /app/node_modules node_modules
COPY --from=builder /app/package.json package.json
COPY --from=builder /app/public public

EXPOSE 3000
CMD ["npm", "start"]
```

**docker-compose.yml**:

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      PINECONE_API_KEY: ${PINECONE_API_KEY}
      CLOUDINARY_CLOUD_NAME: ${CLOUDINARY_CLOUD_NAME}
      CLOUDINARY_API_KEY: ${CLOUDINARY_API_KEY}
      CLOUDINARY_API_SECRET: ${CLOUDINARY_API_SECRET}
      MONGODB_URI: ${MONGODB_URI}
      PINECONE_INDEX_NAME: kamka
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    depends_on:
      - backend
    restart: always
```

### Deploy with Docker

```bash
# Build images
docker-compose build

# Run containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Option 3: AWS Deployment

### Backend on AWS Lambda

1. Install Serverless Framework:

   ```bash
   npm install -g serverless
   serverless plugin install -n serverless-wsgi
   ```

2. Create `serverless.yml` in backend:

   ```yaml
   service: kamka-backend

   provider:
     name: aws
     runtime: python3.11
     region: us-east-1
     environment:
       OPENAI_API_KEY: ${env:OPENAI_API_KEY}
       # ... other env vars

   functions:
     api:
       handler: main.app
       events:
         - httpApi: "*"

   plugins:
     - serverless-wsgi
   ```

3. Deploy:
   ```bash
   serverless deploy
   ```

### Frontend on S3 + CloudFront

1. Build frontend:

   ```bash
   cd frontend
   npm run build
   ```

2. Create S3 bucket and CloudFront distribution
3. Upload contents of `.next` to S3
4. Set `NEXT_PUBLIC_API_URL` to your Lambda URL

## Option 4: Heroku (Old approach, still works)

### Backend on Heroku

1. Create `Procfile` in backend:

   ```
   web: gunicorn -w 4 -b 0.0.0.0:$PORT main:app
   ```

2. Create app:
   ```bash
   heroku create kamka-backend
   heroku config:set OPENAI_API_KEY=sk-...
   # ... set all other env vars
   git subtree push --prefix backend heroku main
   ```

### Frontend on Heroku

1. Create `Procfile` in frontend:

   ```
   web: npm run start
   ```

2. Create app:
   ```bash
   heroku create kamka-frontend
   heroku config:set NEXT_PUBLIC_API_URL=https://kamka-backend.herokuapp.com
   git subtree push --prefix frontend heroku main
   ```

## Production Checklist

- [ ] Set all environment variables
- [ ] Enable HTTPS/SSL
- [ ] Set up error logging (Sentry, etc.)
- [ ] Configure CORS properly for your domains
- [ ] Set up database backups
- [ ] Monitor API usage and costs
- [ ] Set up CI/CD pipeline
- [ ] Test file upload with large files
- [ ] Test chat with multiple documents
- [ ] Set up uptime monitoring
- [ ] Implement rate limiting
- [ ] Add authentication (if needed)
- [ ] Regular security audits

## Environment Variables for Production

### Backend

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=kamka
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
MONGODB_URI=mongodb+srv://...
```

### Frontend

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## Scaling Considerations

### Database

- MongoDB: Use Atlas with auto-scaling
- Pinecone: Start with starter plan, upgrade as needed

### Backend

- Use gunicorn with multiple workers
- Set up load balancer for multiple instances
- Consider serverless for cost efficiency

### Frontend

- Use CDN (CloudFront, Cloudflare) for assets
- Enable caching with proper headers
- Use image optimization

## Monitoring

Set up monitoring for:

1. **Application Performance**: APM tool (New Relic, DataDog)
2. **Error Tracking**: Sentry
3. **Logs**: CloudWatch, Datadog, or similar
4. **Uptime**: Uptime robot, Pingdom
5. **Database**: MongoDB Atlas monitoring

## Troubleshooting Deployments

### "Module not found" errors

- Ensure all packages are in requirements.txt
- Check Python version matches

### "CORS errors" in production

- Update backend CORS origins
- Use your actual domain names

### "API not responding"

- Check environment variables are set
- Verify database connectivity
- Check logs on deployment platform

### "Out of memory"

- Increase worker count in gunicorn
- Optimize document chunking
- Consider database query optimization

## Cost Estimation (Monthly)

| Service       | Free Tier       | Paid        |
| ------------- | --------------- | ----------- |
| Vercel        | 100GB bandwidth | $20/mo      |
| MongoDB Atlas | 512MB storage   | $57/mo      |
| Pinecone      | Starter         | $12/mo      |
| Cloudinary    | 25GB storage    | $99/mo      |
| OpenAI        | -               | Usage based |
| **Total**     | ~$5/mo          | ~$200/mo    |

Choose services based on your traffic and needs.
