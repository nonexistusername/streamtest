# 🛰️ STREAMTEST

A simple but powerful Python GUI tool to scan and test M3U IPTV playlists.  
It supports multi-threaded checking and live stream preview in VLC player.

---

## 📋 Features

- ✅ Multi-threaded stream testing
- ✅ Live preview of working streams using VLC
- ✅ Color-coded results (functional & broken)
- ✅ Functional and broken streams are saved automatically
- ✅ Simple and clean GUI
<br>
 <br>
📂 Playlist Requirements
You need a local .m3u file (not a URL).

The script will parse #EXTINF and stream links.

Valid streams will be saved to:

✅ ~/STREAMTEST/valid_streams.m3u

❌ ~/STREAMTEST/invalid_streams.m3u

✔️ The folder STREAMTEST is created automatically in the user's home directory.
<br>
 <br>
 ---

## 🆕 What's New (Latest Version)

Here’s what’s been improved and added in the latest version of **StreamTest**:

### 🔧 Bug Fixes
- ✅ Fixed incorrect detection of some stream statuses (no more false positives)
- ✅ Fixed stream counter display (total, functional, broken) – now accurate and live-updating

### 🎨 GUI Enhancements
- 🖼️ Improved layout and readability
- 🧭 Added top menu (OPTIONS) with Load / Start / Pause
- 🎛️ Sliders, labels and buttons now use bold fonts and better scaling

### 🚀 Features Added
- ▶️ Ability to **play any stream directly from the GUI** (both working and broken)
- 💾 Automatic saving of working and non-working streams to `~/STREAMTEST/`
- 📂 Auto-create output directory if missing

### 🧠 Smart Improvements
- 🌐 URLs without `http://` prefix are automatically corrected
- ⚠️ Added warning in README about supported stream types
- ✅ Added support for IP-based stream URLs

---
<br>
 <br>

## 🚀 Getting Started



git clone https://github.com/nonexistusername/streamtest.git
<br>
 <br>
cd streamtest
<br>
 <br>
 pip install requests
 <br>
 <br>
 python streamtest.py
  <br>
 <br>

## ⚠️ Supported Stream URL Formats

This tool supports only direct **HTTP/HTTPS** streams.

### ✅ Supported:
- `http://example.com:8080/stream/live.ts`
- `https://yourserver.xyz:8888/channel/1`
- `http://123.123.123.123:8000/live/test.ts`
- `192.168.1.100:8080/stream/live.ts` *(will be automatically fixed to `http://`)*

### ❌ Not supported:
- `rtmp://...`
- `rtsp://...`
- `udp://...`
- Playlist links (URLs to `.m3u` instead of file)
- Streams requiring session/cookies/auth via JavaScript

> ℹ️ Only local `.m3u` files are supported, not remote playlist URLs.

If your playlist contains raw IPs (without `http://`), the app will try to auto-fix them by adding `http://`.

---
## 📸 StreamTest GUI Preview

![Preview](https://raw.githubusercontent.com/nonexistusername/streamtest/main/streamtest.png)
 <br>
 <br>
![Another Preview](https://raw.githubusercontent.com/nonexistusername/streamtest/main/streamtest2.png)




