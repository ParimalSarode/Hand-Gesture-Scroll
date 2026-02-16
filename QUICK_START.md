# QUICK START GUIDE FOR ANTIGRAVITY

## 🚀 Build APK in 5 Steps

### Step 1: Setup Ubuntu Environment (10 minutes)

```bash
# Run these commands in Ubuntu terminal:

sudo apt update && sudo apt upgrade -y

sudo apt install -y python3-pip build-essential git zip unzip openjdk-11-jdk autoconf libtool pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev

pip3 install --user buildozer cython --break-system-packages

echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

---

### Step 2: Copy Project Files (1 minute)

```bash
# Create project directory
mkdir ~/finger_scroll_app
cd ~/finger_scroll_app

# Copy these 2 files into this directory:
# - main.py
# - buildozer.spec
```

---

### Step 3: Build APK (30-60 minutes)

```bash
cd ~/finger_scroll_app

buildozer -v android debug
```

**WAIT!** First build downloads ~1.5GB and takes time.

---

### Step 4: Find APK (1 minute)

```bash
ls -lh ~/finger_scroll_app/bin/

# You'll see: fingerscroll-1.0-debug.apk
```

---

### Step 5: Install on Phone (2 minutes)

```bash
# Copy to Windows Desktop:
cp bin/fingerscroll-1.0-debug.apk /mnt/c/Users/YOUR_USERNAME/Desktop/

# Then:
# 1. Transfer APK to phone
# 2. Install on phone
# 3. Open app
# 4. Grant camera permission
# 5. Press START
# 6. Test scrolling!
```

---

## 🔧 If Build Fails

```bash
# Clean and rebuild:
buildozer android clean
buildozer -v android debug
```

---

## ✅ Success Criteria

- [ ] APK file created (size ~20-30MB)
- [ ] Installs on Android phone (API 21+)
- [ ] Camera permission granted
- [ ] Camera preview shows when START pressed
- [ ] Moving finger up scrolls up
- [ ] Moving finger down scrolls down
- [ ] Works in Instagram/YouTube

---

## 📱 Client Deliverables

**Provide to client:**
1. ✅ `fingerscroll-1.0-debug.apk` - The app
2. ✅ `README.md` - Full documentation
3. ✅ `main.py` - Source code
4. ✅ `buildozer.spec` - Build config

**Installation guide for client:**
1. Download APK to phone
2. Enable "Install from unknown sources"
3. Tap APK to install
4. Open app
5. Grant camera permission
6. Press START
7. Enjoy hands-free scrolling!

---

## ⏱️ Time Estimate

- **First-time setup:** 10 minutes
- **First build:** 30-60 minutes  
- **Subsequent builds:** 2-5 minutes
- **Total:** ~1.5 hours

---

## 🎯 Final Check

Before delivering:
- [ ] Built successfully
- [ ] Tested on real Android device
- [ ] Camera works
- [ ] Scrolling works in test apps
- [ ] No crashes
- [ ] All files included

---

**That's it! Simple and straightforward.** 🚀
