# Antariks Clipper - Desktop Build

## 🚀 Quick Build

**One-command build** (Backend + Frontend):

```cmd
cd backend
build.bat
```

Atau dari root:

```cmd
build-all.bat
```

## 📋 Requirements

### Python Dependencies

```cmd
cd backend
pip install -r requirements.txt
```

### External Tools (Required)

- **ffmpeg** - Video processing
- **yt-dlp** - YouTube downloads

Install via pip:

```cmd
pip install yt-dlp
```

Download ffmpeg dari: https://ffmpeg.org/download.html
Extract dan tambahkan ke PATH system.

### Node.js Dependencies

```cmd
cd frontend
npm install
```

## 🔧 Manual Build

### Step 1: Build Backend

```cmd
cd backend
python -m PyInstaller build-backend.spec --noconfirm
```

### Step 2: Copy ke Frontend Resources

```cmd
xcopy /E /I /Y dist\antariks-backend ..\frontend\resources\backend
```

### Step 3: Build Frontend

```cmd
cd ..\frontend
npm run build:electron
```

## 📦 Build Output

- **Unpacked**: `frontend/dist/win-unpacked/AntariksClipper.exe`
- **Installer**: `frontend/dist/AntariksClipper Setup.exe`

## ⚠️ Common Issues

### CMD Windows Appearing

✅ **FIXED** - All subprocess calls now use hidden console flags

### CORS Errors

✅ **FIXED** - Custom protocol registered with proper privileges

### Port Conflicts

- Backend runs on port **3211**
- Check `.env.production` has correct port

### Missing Dependencies

If exe fails to start:

1. Check Python dependencies installed: `pip install -r requirements.txt`
2. Verify ffmpeg in PATH: `ffmpeg -version`
3. Verify yt-dlp installed: `yt-dlp --version`

## 🧪 Testing

Test backend standalone:

```cmd
cd backend\dist\antariks-backend
antariks-backend.exe
```

Test frontend in dev mode:

```cmd
cd frontend
npm run dev
npm run electron:dev
```

## 📝 Notes

- Build time: ~3-5 minutes (first build)
- Backend exe size: ~500 MB (includes ML models)
- Final app size: ~600 MB

## 🔄 Rebuild After Changes

**Backend code changes**:

```cmd
cd backend
python -m PyInstaller build-backend.spec --noconfirm
xcopy /E /I /Y dist\antariks-backend ..\frontend\resources\backend
```

**Frontend code changes**:

```cmd
cd frontend
npm run build:electron
```

**Full rebuild**:

```cmd
build-all.bat
```
