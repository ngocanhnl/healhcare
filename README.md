## Medical Platform (Flask + MySQL + Bootstrap 5)

### 1) Project structure

```
/app
  /models
    appointment.py
    doctor.py
    enums.py
    schedule.py
    user.py
  /routes
    admin_routes.py
    auth_routes.py
    doctor_routes.py
    patient_routes.py
  /services
    appointment_service.py
    auth_service.py
    authz.py
    doctor_service.py
    forms.py
    schedule_service.py
  /templates
    base.html
    /auth
      login.html
      register.html
    /patient
      booking.html
      dashboard.html
      doctor_detail.html
      search_doctor.html
    /doctor
      appointment_detail.html
      appointments.html
      dashboard.html
      schedule_form.html
      schedules.html
    /admin
      dashboard.html
  /static
config.py
app.py
requirements.txt
/.env.example
/sql
  schema.sql
/scripts
  init_db.py
  seed.py
```

### 2) Prerequisites

- Python 3.11+ (khuyến nghị)
- MySQL 8+

### 3) Create database (SQL script)

Chạy file `sql/schema.sql` trong MySQL:

```sql
SOURCE sql/schema.sql;
```

Hoặc copy/paste nội dung vào MySQL client.

### 4) Configure environment

Tạo file `.env` từ `.env.example` và sửa `DATABASE_URL` đúng MySQL của bạn.

Ví dụ:

```
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/medical_platform?charset=utf8mb4
SECRET_KEY=your-secret
```

### 5) Install dependencies

Trong PowerShell tại thư mục project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 6) Create tables via SQLAlchemy (optional)

Nếu bạn muốn SQLAlchemy tự tạo tables (thay vì chạy SQL script):

```powershell
python .\scripts\init_db.py
```

### 7) Seed sample data

```powershell
python .\scripts\seed.py
```

Tài khoản mẫu được in ra sau khi seed.

### 8) Run server

```powershell
python .\app.py
```

Mở trình duyệt:

- Home/Search: `http://127.0.0.1:5000/doctors/search`
- Login: `http://127.0.0.1:5000/auth/login`

### 9) Notes (roles)

- **PATIENT**: search doctors, view profile/slots, book appointment, xem dashboard
- **DOCTOR**: CRUD schedules, xem & cập nhật trạng thái appointments
- **ADMIN**: xem danh sách users (màn admin dashboard)

