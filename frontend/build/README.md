# Application Icons

This directory should contain application icons for building the desktop app.

## Required Icons

### Windows
- **icon.ico** - 256x256 pixels, ICO format
  - Used for: Windows application icon, taskbar, installer

### macOS
- **icon.icns** - ICNS format (Mac icon bundle)
  - Should contain multiple sizes: 16x16, 32x32, 128x128, 256x256, 512x512, 1024x1024

### Linux
- **icon.png** - 512x512 pixels, PNG format
  - Used for: Linux desktop icon, AppImage

## Creating Icons

### Quick Options

1. **Online Converters**:
   - https://icoconvert.com/ (PNG to ICO)
   - https://cloudconvert.com/ (PNG to ICNS)
   - https://www.img2go.com/convert-to-icon

2. **Desktop Tools**:
   - Adobe Photoshop
   - GIMP (free)
   - Inkscape (for vector)

### Design Guidelines

- Use square dimensions (1:1 aspect ratio)
- High resolution source: 1024x1024 minimum
- Simple, recognizable design
- Works well at small sizes (16x16)
- Transparent background recommended
- Brand colors for recognition

### Example Workflow

1. Create 1024x1024 PNG with transparent background
2. Convert to ICO (Windows):
   ```
   convert icon-1024.png -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico
   ```
3. Convert to ICNS (macOS):
   ```
   mkdir icon.iconset
   sips -z 16 16     icon-1024.png --out icon.iconset/icon_16x16.png
   sips -z 32 32     icon-1024.png --out icon.iconset/icon_16x16@2x.png
   sips -z 32 32     icon-1024.png --out icon.iconset/icon_32x32.png
   sips -z 64 64     icon-1024.png --out icon.iconset/icon_32x32@2x.png
   sips -z 128 128   icon-1024.png --out icon.iconset/icon_128x128.png
   sips -z 256 256   icon-1024.png --out icon.iconset/icon_128x128@2x.png
   sips -z 256 256   icon-1024.png --out icon.iconset/icon_256x256.png
   sips -z 512 512   icon-1024.png --out icon.iconset/icon_256x256@2x.png
   sips -z 512 512   icon-1024.png --out icon.iconset/icon_512x512.png
   sips -z 1024 1024 icon-1024.png --out icon.iconset/icon_512x512@2x.png
   iconutil -c icns icon.iconset
   ```

## Testing Icons

After adding icons, rebuild the app:
```bash
npm run dist
```

Check if icons appear:
- Windows: Right-click .exe > Properties > Icon
- macOS: Open .app in Finder
- Linux: AppImage in file manager

## Placeholder

Until custom icons are created, Electron Builder will use default icons.

To disable icon warnings during development, you can temporarily comment out icon paths in `package.json`:

```json
{
  "win": {
    // "icon": "build/icon.ico",
    ...
  }
}
```

## Branding

For Antariks Clipper:
- Consider using: Video clip symbol, scissors, or filmstrip
- Brand colors: (to be determined)
- Style: Modern, clean, professional
