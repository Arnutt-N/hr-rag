# คู่มือ Supabase

## สมัครและ Setup

### 1. สมัคร Account
1. ไปที่ https://supabase.com
2. คลิก "Start your project"
3. Sign in ด้วย GitHub

### 2. สร้าง Project
1. คลิก "New Project"
2. เลือก Organization
3. กรอกรายละเอียด:
   - Name: `hr-rag`
   - Database Password: ใส่รหัสที่แข็งแรง
   - Region: เลือก `Singapore` (ap-southeast-1) ใกล้ไทย
4. รอสร้างประมาณ 2 นาที

## ฟีเจอร์ที่ใช้

### 1. Database (PostgreSQL)

**สร้าง Table ผ่าน UI:**
1. ไปที่ "Table Editor" → "New Table"
2. ตั้งชื่อ เช่น `documents`
3. เพิ่ม columns:
   - `id` (uuid, primary key, default: gen_random_uuid())
   - `content` (text)
   - `metadata` (jsonb)
   - `created_at` (timestamptz, default: now())

**สร้าง Table ด้วย SQL:**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy สำหรับ public read (ปรับตาม need)
CREATE POLICY "Allow public read" ON documents
    FOR SELECT USING (true);
```

### 2. Authentication

**เปิดใช้งาน:**
1. ไปที่ "Authentication" → "Providers"
2. เปิด "Email" (default เปิดอยู่)

**สร้าง User:**
```javascript
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123'
})
```

**Sign In:**
```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})
```

### 3. Storage (File Upload)
1. ไปที่ "Storage" → "New Bucket"
2. ตั้งชื่อ: `documents`
3. เลือก Public/Private

**Upload File:**
```javascript
const { data, error } = await supabase.storage
  .from('documents')
  .upload('folder/filename.pdf', file)
```

### 4. Realtime (optional)
```javascript
const channel = supabase
  .channel('table-db-changes')
  .on('postgres_changes', { 
    event: 'INSERT', 
    schema: 'public', 
    table: 'documents' 
  }, (payload) => {
    console.log('New document:', payload.new)
  })
  .subscribe()
```

## เชื่อมต่อ Application

### Install Client
```bash
npm install @supabase/supabase-js
```

### Setup Client
```javascript
// นำเข้า function สำหรับสร้าง Supabase client
import { createClient } from '@supabase/supabase-js'

// URL ของ Supabase project
const supabaseUrl = 'https://your-project.supabase.co'
// Anonymous key (public key) สำหรับ client-side
const supabaseAnonKey = 'your-anon-key'

// สร้างและส่งออก client
export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### Environment Variables
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

**หา Keys:**
- Project Settings → API
- `URL` = Project URL
- `anon key` = public key (ใช้ใน client)
- `service_role key` = secret key (ใช้ server-side เท่านั้น!)

## Supabase + RAG

### Vector Storage
Supabase สนับสนุน pgvector:

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- สร้าง table สำหรับ embeddings
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    embedding vector(1536), -- สำหรับ OpenAI ada-002
    created_at TIMESTAMPTZ DEFAULT now()
);

-- สร้าง index (HNSW)
CREATE INDEX ON document_embeddings 
USING hnsw (embedding vector_cosine_ops);
```

### Query with Similarity
```sql
SELECT d.*, 
       1 - (e.embedding <=> query_embedding::vector) as similarity
FROM documents d
JOIN document_embeddings e ON d.id = e.document_id
WHERE e.embedding <=> query_embedding::vector < 0.5
ORDER BY e.embedding <=> query_embedding::vector
LIMIT 5;
```

## Troubleshooting

**RLS Policy blocked:**
- ตรวจสอบ policies ใน "Authentication" → "Policies"

**Storage upload failed:**
- ตรวจจำนวน bucket limits
- ตรวจ file size limit (default 6MB)

**Connection timeout:**
- ลองใช้ Singapore region
- ตรวจ network
