# คู่มือ TiDB Cloud

## สมัครและ Setup

### 1. สมัคร Account
1. ไปที่ https://tidb.cloud
2. คลิก "Sign Up" → ใช้ GitHub/Google/Email
3. Verify email

### 2. สร้าง Cluster

**Free Tier (Serverless):**
- เข้าถึงได้ฟรี (limited queries/storage)
- เหมาะสำหรับ development

**ขั้นตอน:**
1. คลิก "Create Cluster"
2. เลือก "Serverless" (ฟรี) หรือ "Dedicated" (จ่าย)
3. เลือก Region: `aws/us-east-1` หรือ `aws/asia-southeast-1` (ใกล้ไทย)
4. ตั้งชื่อ Cluster
5. คลิก "Create Cluster"

### 3. สร้าง Database/Schema
```sql
CREATE DATABASE hr_rag;
USE hr_rag;

-- สร้างตาราง example
CREATE TABLE documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## เชื่อมต่อจาก Application

### Connection String
1. ไปที่ Cluster → "Connect"
2. เลือก "Connect with SQL Client"
3. จะได้ connection string ประมาณ:
```
mysql://username:password@gateway01.us-east-1.aws.tidbcloud.com:4000/hr_rag
```

### ตัวอย่าง Connection ใน Node.js

**ใช้ mysql2:**
```bash
npm install mysql2
```

```javascript
// นำเข้า mysql2 สำหรับเชื่อมต่อ MySQL
import mysql from 'mysql2/promise';

// สร้าง connection pool สำหรับจัดการหลาย connections
const pool = mysql.createPool({
  // ที่อยู่ของ TiDB Cloud server
  host: 'gateway01.us-east-1.aws.tidbcloud.com',
  // พอร์ตเริ่มต้นของ MySQL
  port: 4000,
  // ชื่อผู้ใช้
  user: 'username',
  // รหัสผ่าน
  password: 'password',
  // ชื่อ database
  database: 'hr_rag',
  // รอ connections เมื่อ pool เต็ม
  waitForConnections: true,
  // จำนวน connections สูงสุดใน pool
  connectionLimit: 10,
});

// ส่งออก pool เพื่อใช้ในไฟล์อื่น
export default pool;
```

**ใช้ Prisma:**
```bash
npm install prisma @prisma/client
npx prisma init
```

ใน `prisma/schema.prisma`:
```prisma
// แหล่งข้อมูลที่เชื่อมต่อ
datasource db {
  provider = "mysql"
  url      = env("DATABASE_URL")
}
```

### Environment Variables
```env
DATABASE_URL=mysql://username:password@gateway01.us-east-1.aws.tidbcloud.com:4000/hr_rag
```

## การใช้งาน TiDB Cloud Console

### Run SQL Queries
1. เลือก Cluster → "SQL Editor"
2. พิมพ์ SQL → กด "Run"

### ดู usage
- Cluster → "Overview" → ดู CPU, Request units, Storage

### Backup (Serverless)
- Auto backup 7 วัน
- ดูที่ "Backups" tab

## Tips

### Connection Pooling
TiDB Serverless มี limit requests/minute
- ใช้ connection pooling
- ปิด connection เมื่อไม่ใช้

### SSL/TLS
TiDB บังคับ SSL อยู่แล้ว ไม่ต้องตั้งค่าเพิ่ม

### Troubleshooting

**Can't connect:**
- ตรวจสอบ IP whitelist (ถ้าใช้ Dedicated)
- ตรวจ username/password

**Too many connections:**
- ลด connectionLimit
- ใช้ persistent connections อย่างถูกต้อง
