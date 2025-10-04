# HR Recruiting Agent - Public Deployment Guide

This guide will help you deploy your HR Recruiting Agent application publicly so it can be accessed from anywhere.

## 🚀 Deployment Options

### Option 1: Railway (Recommended - Easiest)

Railway is the easiest platform to deploy your application:

1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub
2. **Connect Repository**: Connect your GitHub repository
3. **Deploy**: Railway will automatically detect the `railway.json` file and deploy
4. **Set Environment Variables**: 
   - Go to your project settings
   - Add environment variables:
     - `EMAIL_USER`: your-email@example.com
     - `EMAIL_PASSWORD`: your-app-password
     - `CEREBRAS_API_KEY`: your-cerebras-api-key
5. **Access**: Your app will be available at a public URL like `https://your-app-name.up.railway.app`

### Option 2: Render

1. **Sign up**: Go to [render.com](https://render.com) and sign up
2. **New Web Service**: Create a new Web Service
3. **Connect Repository**: Connect your GitHub repository
4. **Configure**:
   - Build Command: (leave empty, uses Dockerfile)
   - Start Command: `/app/start.sh`
   - Environment: Docker
5. **Set Environment Variables**: Add EMAIL_USER, EMAIL_PASSWORD, and CEREBRAS_API_KEY
6. **Deploy**: Click Deploy

### Option 3: Fly.io

1. **Install Fly CLI**: Follow instructions at [fly.io/docs](https://fly.io/docs/)
2. **Login**: `fly auth login`
3. **Launch**: `fly launch` (this will create the app)
4. **Set Secrets**:
   ```bash
   fly secrets set EMAIL_USER=your-email@example.com
   fly secrets set EMAIL_PASSWORD=your-app-password
   fly secrets set CEREBRAS_API_KEY=your-cerebras-api-key
   ```
5. **Deploy**: `fly deploy`

### Option 4: Docker Hub + Any Platform

1. **Push to Docker Hub**:
   ```bash
   # Tag your image
   docker tag hr-recruiting-agent:latest yourusername/hr-recruiting-agent:latest
   
   # Push to Docker Hub
   docker push yourusername/hr-recruiting-agent:latest
   ```

2. **Deploy on any platform** that supports Docker Hub:
   - Heroku
   - DigitalOcean App Platform
   - AWS ECS
   - Google Cloud Run
   - Azure Container Instances

## 🔧 Environment Variables Required

Set these environment variables in your deployment platform:

- `EMAIL_USER`: Your email address for sending emails
- `EMAIL_PASSWORD`: Your email app password (not your regular password)
- `CEREBRAS_API_KEY`: Your Cerebras API key for LLM functionality

## 📋 Pre-deployment Checklist

- [ ] Test locally with `docker run -p 8501:8501 hr-recruiting-agent`
- [ ] Verify environment variables are set correctly
- [ ] Check that all dependencies are in requirements.txt
- [ ] Ensure Dockerfile builds successfully

## 🌐 Post-deployment

After deployment:
1. Your app will have a public URL
2. Test the application thoroughly
3. Monitor logs for any issues
4. Set up monitoring if needed

## 🆘 Troubleshooting

### Common Issues:

1. **Port Issues**: Make sure your platform uses the PORT environment variable
2. **Memory Issues**: Some platforms have memory limits - check logs
3. **Environment Variables**: Ensure EMAIL_USER, EMAIL_PASSWORD, and CEREBRAS_API_KEY are set
4. **Build Failures**: Check that all dependencies are properly specified

### Getting Help:

- Check platform-specific documentation
- Review application logs
- Test locally first to ensure everything works

## 💡 Pro Tips

1. **Railway** is the easiest for beginners
2. **Render** offers good free tier
3. **Fly.io** gives you more control
4. Always test locally before deploying
5. Use environment variables for secrets, never hardcode them
