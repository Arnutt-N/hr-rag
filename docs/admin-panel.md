# HR-RAG Admin Panel Documentation

## Overview

Admin Panel สำหรับ HR-RAG System ช่วยให้ผู้ดูแลระบบสามารถจัดการผู้ใช้ ดู analytics และควบคุมการตั้งค่าระบบได้

## Access

เข้าถึงที่: `http://localhost:3000/admin`

**Note:** ต้องมี role `admin` จึงจะเข้าถึงได้

## Features

### 1. Dashboard (`/admin`)
- แสดงสถิติระบบรวม (Users, Projects, Documents, Messages)
- แสดงกิจกรรมรายวัน (7 วันล่าสุด)
- แสดง Top Active Users
- แสดง Top LLM Providers

### 2. User Management (`/admin/users`)
- รายการผู้ใช้ทั้งหมดพร้อม pagination
- ค้นหาผู้ใช้ (search)
- ดูข้อมูลผู้ใช้ (email, role, status)
- Enable/Disable users
- Reset password
- ดูจำนวน projects และ chat sessions ต่อ user

### 3. Analytics (`/admin/analytics`)
- Daily Activity Line Chart (30 วัน)
- LLM Provider Usage Pie Chart
- New Users Bar Chart
- New Documents Bar Chart

### 4. Content Management (`/admin/content`)
- ดู Projects ทั้งหมด
- ดู Documents ทั้งหมด
- ค้นหา content
- ลบ documents

### 5. System Settings (`/admin/settings`)
- Default LLM Provider
- Default Embedding Model
- Rate Limiting
- Feature Flags:
  - Guest Access
  - Public Projects
  - API Key Management
  - Evaluation Module
- Maintenance Mode

### 6. Logs (`/admin/logs`)
- System logs ทั้งหมด
- Filter ตาม level (info, success, warn, error)
- แสดง timestamp, user, endpoint

### 7. Security (`/admin/security`)
- Login attempts log
- แสดง successful/failed attempts
- IP address tracking

## API Endpoints

### Dashboard
```http
GET /admin/analytics?days=30
```

### Users
```http
GET    /admin/users?page=1&page_size=20&search=
GET    /admin/users/{id}
POST   /admin/users/reset-password
POST   /admin/users/toggle-status
```

### Content
```http
GET    /admin/projects?page=1&search=
GET    /admin/documents?page=1&search=
DELETE /admin/documents/{id}
```

### Settings
```http
GET  /admin/settings
POST /admin/settings
```

### Logs
```http
GET /admin/logs?level=error
GET /admin/security/login-attempts?success=false
```

## Making a User Admin

ใน database ให้ตั้งค่า `role = 'admin'` สำหรับ user ที่ต้องการ:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
```

## Security Considerations

1. **Admin routes ถูก protect ด้วย middleware**
2. **ทุก API endpoint ตรวจสอบ `require_admin`**
3. **ตรวจสอบสิทธิ์ทุกครั้งก่อน access sensitive data**
4. **Login attempts ถูก log ไว้ตรวจสอบ**

## Future Enhancements

- [ ] Bulk user actions
- [ ] Email notifications
- [ ] Advanced filtering
- [ ] Data export (CSV, JSON)
- [ ] Audit trail
- [ ] IP blocking
- [ ] 2FA for admin

---

*Last updated: March 2026*
