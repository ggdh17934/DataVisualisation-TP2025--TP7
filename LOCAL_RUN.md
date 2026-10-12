# Existing local installation / تشغيل النسخة المحلية

The dashboard is running at **http://localhost:8000/dashboard/2** on this computer.
Its analytical data are in your Supabase project. The separate local PostgreSQL
database stores Metabase's questions, dashboard and login.

From this TP7 folder, PowerShell:

```powershell
.\start-local.ps1
```

To stop it while preserving the dashboard:

```powershell
.\stop-local.ps1
```

These helpers reuse the portable official Metabase/Java/PostgreSQL installation
under the parent `.task-tools` folder. No system service was installed. After
restarting Windows, run the start helper again. On another computer, use the
included Docker Compose setup instead.

The local coursework login email is **student@localhost.test**. Its generated
password is in the ignored file `.secrets/metabase.json` in this local TP7 folder.
It is deliberately absent from GitHub. This is a local login identifier, not an
email account or a destination for messages.

اللوحة تعمل على الرابط المذكور عندما يكون الخادم وقاعدة تطبيقه يعملان.
بعد إعادة تشغيل Windows نفذ ملف `start-local.ps1` من PowerShell داخل مجلد TP7.
ملف `stop-local.ps1` يوقف النسخة دون حذف إعدادات اللوحة. بيانات تسجيل الدخول
الخاصة موجودة محلياً في `.secrets/metabase.json` ولا تُرفع إلى GitHub.
هذه الطريقة تخص النسخة المجهزة على هذا الجهاز؛ على جهاز آخر استعمل Docker Compose.
