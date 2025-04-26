
# 🛠️ יצירת קובץ credentials.json באופן עצמאי

כדי להתחבר ליומן Google שלך, גוגל דורשת אישור OAuth דרך פרויקט ב־Google Cloud. להלן השלבים ליצירת קובץ `credentials.json`.

## 1️⃣ כניסה לקונסולת המפתחים של Google
- כנס לכתובת: [https://console.cloud.google.com/](https://console.cloud.google.com/)
- היכנס עם חשבון הגוגל שלך

## 2️⃣ יצירת פרויקט חדש
1. בפינה הימנית העליונה, לחץ על בחירת פרויקט → "חדש פרויקט"
2. תן שם (למשל: `Soonly`)
3. לחץ על **"צור"**

## 3️⃣ הפעלת Calendar API
1. בתפריט הימני לחץ על: **"APIs & Services" > "Library"**
2. חפש: **Google Calendar API**
3. לחץ עליו → ואז על **"Enable"**

## 4️⃣ יצירת אישור OAuth
1. עבור ל־**"APIs & Services" > "Credentials"**
2. לחץ על כפתור **"Create credentials"** → ובחר **OAuth client ID**
3. אם תקבל הודעה על צורך בהגדרת מסך ההסכמה – בצע את השלב הבא 👇

## 5️⃣ הגדרת מסך הסכמה (Consent Screen)
1. לחץ על **"OAuth consent screen"** בתפריט השמאלי
2. בחר **"External"** ולחץ על "Create"
3. מלא רק את השדות החובה:
   - App name: `Soonly`
   - User support email: כתובת המייל שלך
4. עבור לשלב הבא (Scopes) – **אין צורך להוסיף כלום**
5. עבור לשלב הבא (Test Users) – הוסף את כתובת המייל שלך
6. לחץ על "Save and continue"

## 6️⃣ יצירת OAuth Client
1. חזור ל־**"Credentials"**
2. לחץ שוב על **"Create credentials"** → ובחר **OAuth client ID**
3. בחר **Application type: Desktop app**
4. תן שם (למשל: `soonly-desktop`)
5. לחץ על **"Create"**
6. לחץ על **"Download JSON"** – זה הקובץ `credentials.json`

## 7️⃣ העתקת הקובץ
- שמור את הקובץ שהורדת בשם **`credentials.json`**
- והנח אותו באותה תיקייה שבה נמצא קובץ ההתקנה `Soonly.exe`

## 🎉 זהו!
בהפעלה הראשונה תתבקש להתחבר לחשבון גוגל ולאשר גישה ליומן שלך.

אם אתה מקבל הודעה כמו **"This app isn't verified"**, לחץ על **Advanced** ואז **Continue**.


📋 קובץ הגדרות ראשוני
לאחר התקנת התוכנה, יש לשנות את שם הקובץ config.example.json לשם config.json