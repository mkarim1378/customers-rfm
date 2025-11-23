# راهنمای اتصال به GitHub

## مرحله 1: ایجاد Repository در GitHub

1. به [GitHub.com](https://github.com) بروید و وارد حساب کاربری خود شوید
2. روی دکمه **"New"** یا **"+"** در بالای صفحه کلیک کنید
3. نام repository را انتخاب کنید (مثلاً: `customer-list-manager` یا `customers-list-with-kia`)
4. توضیحات را اضافه کنید (اختیاری)
5. **Public** یا **Private** را انتخاب کنید
6. **DO NOT** initialize with README (چون ما قبلاً README داریم)
7. روی **"Create repository"** کلیک کنید

## مرحله 2: اتصال Repository محلی به GitHub

بعد از ایجاد repository، GitHub یک URL به شما می‌دهد. دستورات زیر را در terminal اجرا کنید:

```bash
# به جای YOUR_USERNAME و REPO_NAME، اطلاعات repository خود را قرار دهید
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

یا اگر از SSH استفاده می‌کنید:

```bash
git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

## مثال

اگر repository شما `customer-list-manager` و username شما `john-doe` باشد:

```bash
git remote add origin https://github.com/john-doe/customer-list-manager.git
git branch -M main
git push -u origin main
```

## نکات مهم

- اگر repository را با نام دیگری ایجاد کردید، URL را تغییر دهید
- برای push کردن، باید در GitHub احراز هویت کنید (token یا SSH key)
- اگر اولین بار است، ممکن است نیاز به تنظیم username و email در git داشته باشید:
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"
  ```

