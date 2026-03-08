# คู่มือ Deploy บน Vercel

## เตรียมตัวก่อน Deploy

### 1. ติดตั้ง Vercel CLI (optional)
```bash
npm i -g vercel
vercel login
```

### 2. เตรียม Environment Variables
สร้างไฟล์ `.env.local` หรือ copy จาก `.env.example`:
```bash
cp .env.example .env.local
```

กรอกค่าต่างๆ:
```env
# Database
DATABASE_URL=your_tidb_connection_string

# Supabase (ถ้าใช้)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Vector DB (Chroma หรือ Qdrant)
CHROMA_DB_URL=your_chroma_url
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key

# Other
NEXT_PUBLIC_API_URL=your_api_url
```

## Deploy ผ่าน Vercel CLI

```bash
vercel
```

ตอบคำถามตามที่แนะนำ:
- Set up and deploy? `Y`
- Which scope? `<your-username>`
- Want to override settings? `N`

### Deploy to Production
```bash
vercel --prod
```

## Deploy ผ่าน GitHub

### 1. Push code ไป GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

### 2. เชื่อมต่อ Vercel
1. ไปที่ https://vercel.com
2. คลิก "Add New..." → "Project"
3. เลือก GitHub repo
4. กด "Import"

### 3. ตั้งค่า Environment Variables
ในหน้า Project Settings → Environment Variables:
- เพิ่มทีละตัว หรือ import จาก `.env`
- **สำคัญ:** ต้อง set `NODE_ENV = production` สำหรับ production

### 4. Deploy
- คลิก "Deploy" รอจนเสร็จ
- ได้ URL สวยๆ เช่น `your-project.vercel.app`

## การตั้งค่าเพิ่มเติม

### Custom Domain
1. Project Settings → Domains
2. ใส่ domain ของคุณ
3. ทำ DNS configuration ตามที่ Vercel บอก

### CI/CD
Vercel จะ auto-deploy ทุกครั้งที่ push ใหม่

### Preview Deployments
ทุก PR จะได้ preview URL อัตโนมัติ

## Troubleshooting

### Build Failed
- ดู log ที่ Vercel dashboard
- ตรวจสอบ Node version ใน `package.json`:
```json
{
  // กำหนดเวอร์ชัน Node.js ที่ใช้ได้
  "engines": {
    "node": ">=18.x"
  }
}
```

### Environment Variables ไม่ทำงาน
- ตรวจสอบว่า add ถูกต้องทุกตัว
- สำหรับ Next.js ต้องมี `NEXT_PUBLIC_` prefix สำหรับ client-side vars

### 503 Error
- ลอง redeploy หรือ check function logs
