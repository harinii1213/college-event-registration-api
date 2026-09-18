\## Production Deployment



\### Production Environment



Before deployment, configure the required environment variables:



```env

DATABASE\_URL=postgresql+asyncpg://username:password@host:5432/college\_events

JWT\_SECRET\_KEY=your-production-secret-key

