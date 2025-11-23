# راهنمای پیاده‌سازی تشخیص کاربران بلاک شده از پیام‌های همگانی

## ⚠️ توجه: انتخاب کتابخانه

این راهنما شامل کد برای **دو کتابخانه** مختلف است:

1. **aiogram** (aiogram 2.x / 3.x) - کتابخانه مدرن و async
2. **python-telegram-bot** (PTB 13.x / 20.x) - کتابخانه معروف و پایدار

> **⚠️ مهم**: این دو کتابخانه **نمی‌توانند همزمان** در یک پروژه استفاده شوند. یکی را انتخاب کنید و کد مربوط به همان را استفاده کنید.

### تفاوت‌ها:
- `aiogram`: سریع‌تر، مدرن‌تر، async محور
- `python-telegram-bot`: پایدارتر، مستندات بیشتر، جامعه بزرگتر

---

## 💡 ایده کلی

به جای ارسال پیام تست جداگانه، از **همان پیام‌های اطلاع‌رسانی** که به کاربران می‌فرستید استفاده می‌کنیم و از خطاهای ارسال، تشخیص می‌دهیم که کدام کاربران ربات را بلاک کرده‌اند.

---

## 🔧 پیاده‌سازی

### 1️⃣ ساختار دیتابیس (ذخیره وضعیت کاربران)

```python
# مثال با SQLite
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    phone TEXT,
    name TEXT,
    status TEXT DEFAULT 'active',  -- active, blocked, inactive
    last_message_sent_at TIMESTAMP,
    last_block_detected_at TIMESTAMP,
    last_activity_at TIMESTAMP
);
```

یا با دیتابیس دیگری که دارید (PostgreSQL, MySQL، ...)

---

### 2️⃣ تابع بهبود یافته برای ارسال پیام همگانی

> **⚠️ مهم**: کد زیر برای **aiogram** نوشته شده. اگر از **python-telegram-bot** استفاده می‌کنید، به بخش "نسخه python-telegram-bot" مراجعه کنید.

#### 📦 نسخه aiogram (aiogram 2.x یا 3.x)

```python
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from datetime import datetime
import asyncio

async def broadcast_message_with_block_detection(
    bot: Bot,
    message_text: str,
    users_list: list,  # لیست user_id ها
    delay: float = 0.05  # تاخیر بین ارسال پیام‌ها (برای جلوگیری از Rate Limit)
):
    """
    ارسال پیام همگانی با تشخیص خودکار کاربران بلاک شده
    """
    success_count = 0
    blocked_count = 0
    failed_count = 0
    blocked_users = []

    for user_id in users_list:
        try:
            # ارسال پیام به کاربر
            await bot.send_message(
                chat_id=user_id,
                text=message_text
            )

            # موفق بود = کاربر فعال است
            success_count += 1
            await update_user_status(user_id, 'active', message_sent=True)

        except TelegramBadRequest as e:
            error_msg = str(e).lower()

            # تشخیص بلاک شدن
            if any(keyword in error_msg for keyword in [
                'chat not found',
                'chat_id is empty',
                'user is deactivated',
                'bot was blocked'
            ]):
                blocked_count += 1
                blocked_users.append(user_id)
                await update_user_status(user_id, 'blocked', block_detected=True)

            else:
                # خطای دیگر (مثلاً متن خیلی طولانی)
                failed_count += 1
                print(f"خطا برای کاربر {user_id}: {e}")

        except TelegramForbiddenError:
            # کاربر ربات را بلاک کرده
            blocked_count += 1
            blocked_users.append(user_id)
            await update_user_status(user_id, 'blocked', block_detected=True)

        except Exception as e:
            # خطای غیرمنتظره
            failed_count += 1
            print(f"خطای غیرمنتظره برای کاربر {user_id}: {e}")

        # تاخیر برای جلوگیری از Rate Limit
        await asyncio.sleep(delay)

    # گزارش نهایی
    return {
        'total': len(users_list),
        'success': success_count,
        'blocked': blocked_count,
        'failed': failed_count,
        'blocked_users': blocked_users
    }
```

#### 📦 نسخه python-telegram-bot (python-telegram-bot 13.x یا 20.x)

```python
from telegram import Bot
from telegram.error import TelegramError, BadRequest, Forbidden, Unauthorized
from datetime import datetime
import asyncio

async def broadcast_message_with_block_detection(
    bot: Bot,
    message_text: str,
    users_list: list,  # لیست user_id ها
    delay: float = 0.05  # تاخیر بین ارسال پیام‌ها
):
    """
    ارسال پیام همگانی با تشخیص خودکار کاربران بلاک شده
    (نسخه python-telegram-bot)
    """
    success_count = 0
    blocked_count = 0
    failed_count = 0
    blocked_users = []
    
    for user_id in users_list:
        try:
            # ارسال پیام به کاربر
            await bot.send_message(
                chat_id=user_id,
                text=message_text
            )
            
            # موفق بود = کاربر فعال است
            success_count += 1
            await update_user_status(user_id, 'active', message_sent=True)
            
        except Forbidden:
            # کاربر ربات را بلاک کرده
            blocked_count += 1
            blocked_users.append(user_id)
            await update_user_status(user_id, 'blocked', block_detected=True)
        
        except Unauthorized:
            # کاربر ربات را بلاک کرده یا غیرفعال شده
            blocked_count += 1
            blocked_users.append(user_id)
            await update_user_status(user_id, 'blocked', block_detected=True)
        
        except BadRequest as e:
            error_msg = str(e).lower()
            
            # تشخیص بلاک شدن از خطاهای BadRequest
            if any(keyword in error_msg for keyword in [
                'chat not found',
                'chat_id is empty',
                'user is deactivated',
                'bot was blocked'
            ]):
                blocked_count += 1
                blocked_users.append(user_id)
                await update_user_status(user_id, 'blocked', block_detected=True)
            else:
                # خطای دیگر
                failed_count += 1
                print(f"خطا برای کاربر {user_id}: {e}")
        
        except TelegramError as e:
            # خطای عمومی تلگرام
            failed_count += 1
            print(f"خطای تلگرام برای کاربر {user_id}: {e}")
        
        except Exception as e:
            # خطای غیرمنتظره
            failed_count += 1
            print(f"خطای غیرمنتظره برای کاربر {user_id}: {e}")
        
        # تاخیر برای جلوگیری از Rate Limit
        await asyncio.sleep(delay)
    
    # گزارش نهایی
    return {
        'total': len(users_list),
        'success': success_count,
        'blocked': blocked_count,
        'failed': failed_count,
        'blocked_users': blocked_users
    }
```

> **نکته**: در `python-telegram-bot` نسخه 20.x از `context.bot` استفاده می‌شود:
> ```python
> await context.bot.send_message(chat_id=user_id, text=message_text)
> ```

---

### 3️⃣ تابع بروزرسانی وضعیت کاربر

```python
async def update_user_status(
    user_id: int,
    status: str,  # 'active', 'blocked', 'inactive'
    message_sent: bool = False,
    block_detected: bool = False,
    activity: bool = False
):
    """
    بروزرسانی وضعیت کاربر در دیتابیس
    """
    now = datetime.now()

    if message_sent:
        # بروزرسانی زمان آخرین پیام ارسالی
        db.execute(
            "UPDATE users SET last_message_sent_at = ?, status = 'active' WHERE user_id = ?",
            (now, user_id)
        )

    if block_detected:
        # بروزرسانی زمان تشخیص بلاک
        db.execute(
            "UPDATE users SET status = 'blocked', last_block_detected_at = ? WHERE user_id = ?",
            (now, user_id)
        )

    if activity:
        # بروزرسانی آخرین فعالیت
        db.execute(
            "UPDATE users SET last_activity_at = ?, status = 'active' WHERE user_id = ?",
            (now, user_id)
        )
```

---

### 4️⃣ دستور آمارگیری (بهبود یافته)

```python
async def get_statistics_command(message: Message):
    """
    دستور آمارگیری با نمایش کاربران بلاک شده
    """
    # دریافت آمار از دیتابیس
    total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    users_with_phone = db.execute("SELECT COUNT(*) FROM users WHERE phone IS NOT NULL").fetchone()[0]
    users_without_phone = total_users - users_with_phone
    active_users = db.execute(
        "SELECT COUNT(*) FROM users WHERE status = 'active'"
    ).fetchone()[0]
    blocked_users = db.execute(
        "SELECT COUNT(*) FROM users WHERE status = 'blocked'"
    ).fetchone()[0]

    # محاسبه درصدها
    active_percent = (active_users / total_users * 100) if total_users > 0 else 0
    blocked_percent = (blocked_users / total_users * 100) if total_users > 0 else 0

    # ساخت پیام آمار
    stats_message = f"""
📊 آمار کاربران ربات:
━━━━━━━━━━━━━━━━━
👥 کل کاربران: {total_users:,}
📱 کاربران با شماره: {users_with_phone:,}
❌ کاربران بدون شماره: {users_without_phone:,}
━━━━━━━━━━━━━━━━━
✅ کاربران فعال: {active_users:,} ({active_percent:.1f}%)
🚫 کاربران بلاک شده: {blocked_users:,} ({blocked_percent:.1f}%)
━━━━━━━━━━━━━━━━━
📈 نرخ فعال: {(active_users/total_users*100) if total_users > 0 else 0:.1f}%
    """

    await message.answer(stats_message)
```

---

### 5️⃣ استفاده در کد اصلی ربات

#### 📦 نسخه aiogram

```python
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("broadcast"))
async def broadcast_handler(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    # دریافت متن پیام از ادمین
    broadcast_text = message.text.replace("/broadcast", "").strip()

    # دریافت لیست تمام کاربران از دیتابیس
    all_users = db.execute("SELECT user_id FROM users").fetchall()
    user_ids = [row[0] for row in all_users]

    # ارسال با تشخیص بلاک
    result = await broadcast_message_with_block_detection(
        bot=bot,
        message_text=broadcast_text,
        users_list=user_ids,
        delay=0.05
    )

    # گزارش به ادمین
    report = f"""
📤 گزارش ارسال پیام همگانی:
━━━━━━━━━━━━━━━━━
✅ ارسال موفق: {result['success']}
🚫 کاربران بلاک شده: {result['blocked']}
❌ خطا: {result['failed']}
━━━━━━━━━━━━━━━━━
📊 کل: {result['total']}
    """

    await message.answer(report)
```

#### 📦 نسخه python-telegram-bot

```python
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    # دریافت متن پیام از ادمین
    broadcast_text = update.message.text.replace("/broadcast", "").strip()

    # دریافت لیست تمام کاربران از دیتابیس
    all_users = db.execute("SELECT user_id FROM users").fetchall()
    user_ids = [row[0] for row in all_users]

    # ارسال با تشخیص بلاک (استفاده از context.bot)
    result = await broadcast_message_with_block_detection(
        bot=context.bot,
        message_text=broadcast_text,
        users_list=user_ids,
        delay=0.05
    )

    # گزارش به ادمین
    report = f"""
📤 گزارش ارسال پیام همگانی:
━━━━━━━━━━━━━━━━━
✅ ارسال موفق: {result['success']}
🚫 کاربران بلاک شده: {result['blocked']}
❌ خطا: {result['failed']}
━━━━━━━━━━━━━━━━━
📊 کل: {result['total']}
    """

    await update.message.reply_text(report)

# ثبت handler
application.add_handler(CommandHandler("broadcast", broadcast_handler))
```

---

## 🎯 مزایای این روش

✅ **بدون پیام اضافی**: از همان پیام‌های اطلاع‌رسانی استفاده می‌شود  
✅ **بدون اذیت کاربر**: کاربر پیام اضافی نمی‌بیند  
✅ **بروزرسانی خودکار**: هر بار که پیام همگانی می‌فرستید، وضعیت بروز می‌شود  
✅ **دقیق**: بر اساس خطاهای واقعی تلگرام  
✅ **کارا**: بدون نیاز به تست دستی جداگانه

---

## 📝 نکات مهم

1. **Rate Limit**: حتماً delay بین ارسال پیام‌ها قرار دهید (حداقل 0.05 ثانیه)

2. **Error Handling**: همه خطاها را catch کنید و فقط خطاهای مربوط به بلاک را ثبت کنید

3. **ذخیره تاریخ**: تاریخ آخرین تشخیص بلاک را ذخیره کنید تا بدانید چه زمانی شناسایی شده

4. **بروزرسانی وضعیت**: اگر کاربر دوباره فعال شد (مثلاً پیام ارسال شد)، وضعیت را به 'active' تغییر دهید

5. **بهینه‌سازی**: برای تعداد زیاد کاربران، می‌توانید از asyncio.gather با batch استفاده کنید

---

## 🔄 حالت پیشرفته (Optional)

اگر می‌خواهید بعد از مدتی دوباره بررسی کنید که آیا کاربر دوباره فعال شده:

```python
async def recheck_blocked_users(bot: Bot):
    """
    بررسی مجدد کاربران بلاک شده (مثلاً هر هفته)
    """
    blocked_users = db.execute(
        "SELECT user_id FROM users WHERE status = 'blocked'"
    ).fetchall()

    for (user_id,) in blocked_users:
        try:
            # تست با پیام خاموش
            await bot.send_message(
                chat_id=user_id,
                text=".",  # متن کوتاه
                disable_notification=True
            )
            # موفق شد = کاربر دوباره فعال شد
            await update_user_status(user_id, 'active')
        except:
            # هنوز بلاک شده
            pass
```
