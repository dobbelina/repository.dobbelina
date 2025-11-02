# Testing Guide for Cumination v1.1.165

## 🎯 What Was Changed

This build includes:

### 🔒 **Critical Security Fixes**
- Fixed 30+ SQL injection vulnerabilities
- Removed unsafe `exec()`/`eval()` code execution
- All database queries now use parameterized statements

### 🚀 **BeautifulSoup HTML Parser Migration**
- Added BeautifulSoup4 infrastructure to `utils.py`
- Migrated PornHub site to use BeautifulSoup instead of regex
- More resilient to website HTML changes

---

## 📦 Installation

### **Option 1: Install from ZIP (Recommended)**

1. **Copy ZIP file to a location Kodi can access:**
   - Windows: Desktop or Downloads folder
   - Linux/Mac: Home directory
   - Or use USB drive

2. **Install BeautifulSoup4 addon (REQUIRED):**
   - Open Kodi
   - Go to: **Add-ons → Install from repository**
   - Navigate to: **Kodi Add-on repository → Program add-ons**
   - Find and install: **script.module.beautifulsoup4**
   - Wait for "Addon installed" notification

3. **Install Cumination addon:**
   - Go to: **Add-ons → Install from zip file**
   - Navigate to where you copied `plugin.video.cumination-1.1.165.zip`
   - Select the ZIP file
   - Wait for "Add-on installed" notification

### **Option 2: Upgrade Existing Installation**

If you already have Cumination installed:

1. Install BeautifulSoup4 first (see Option 1, step 2)
2. Install from ZIP (Kodi will upgrade automatically)
3. Restart Kodi (recommended)

---

## ✅ Testing Checklist

### **Test 1: Verify Addon Loads**

- [ ] Open Kodi Add-ons section
- [ ] Navigate to Video Add-ons
- [ ] Find "Cumination" addon
- [ ] Click to open it
- [ ] **Expected:** Main menu loads with site list

**❌ If it fails:** Check Kodi log for "BeautifulSoup not available" error

---

### **Test 2: PornHub Site (Primary Test)**

This site uses the new BeautifulSoup parser.

#### **2A: Video Listing**
- [ ] Open Cumination
- [ ] Select "PornHub"
- [ ] Wait for video list to load
- [ ] **Expected:** See 20-30 video thumbnails with titles and durations

**✅ Success indicators:**
- Videos display with thumbnails
- Titles are readable
- Duration times shown (e.g., "10:25")
- No error messages

**❌ If it fails:**
- Check Kodi log for "Error parsing video item" messages
- Note any missing thumbnails or titles
- Take screenshot if possible

#### **2B: Pagination**
- [ ] Scroll to bottom of video list
- [ ] Click "Next Page" button
- [ ] **Expected:** Page 2 loads with new videos
- [ ] **Expected:** URL shows `page=2`

#### **2C: Categories**
- [ ] Go back to PornHub main menu
- [ ] Click "Categories"
- [ ] **Expected:** List of categories with thumbnail images
- [ ] **Expected:** Each category shows video count (e.g., "Amateur (1,234 videos)")

#### **2D: Search**
- [ ] Go to PornHub main menu
- [ ] Click "Search"
- [ ] Enter a search term (e.g., "test")
- [ ] **Expected:** Search results appear
- [ ] **Expected:** Can play videos from search results

#### **2E: Video Playback**
- [ ] Click any video from list
- [ ] **Expected:** Video player starts
- [ ] **Expected:** Video streams and plays

---

### **Test 3: Other Sites (Regression Test)**

Test a few other sites to ensure they still work:

#### **3A: SpankBang**
- [ ] Open SpankBang site
- [ ] **Expected:** Videos load (uses old regex method, should still work)

#### **3B: XVideos**
- [ ] Open XVideos site
- [ ] **Expected:** Videos load

#### **3C: Any other favorite site**
- [ ] Open your preferred site
- [ ] **Expected:** Works as before

---

### **Test 4: Security Fixes (Favorites)**

This tests the SQL injection fixes.

- [ ] Play any video
- [ ] Add it to favorites (context menu → Add to Favorites)
- [ ] Go to main menu → Favorites
- [ ] **Expected:** Video appears in favorites
- [ ] **Expected:** Can play video from favorites
- [ ] **Expected:** No SQL errors in log

---

### **Test 5: Search Functionality**

Tests keyword database (was SQL injection vulnerable).

- [ ] Go to any site with Search
- [ ] Search for something (e.g., "test")
- [ ] Go to main menu → Search History
- [ ] **Expected:** Your search appears in history
- [ ] Click the search term
- [ ] **Expected:** Search runs again
- [ ] Delete search from history
- [ ] **Expected:** Keyword removed without errors

---

### **Test 6: Settings & Filters (PornHub specific)**

Tests the complex filtering system.

- [ ] Open PornHub
- [ ] Context menu on any video → Production → Select "Homemade"
- [ ] **Expected:** Page reloads showing only homemade videos
- [ ] Context menu → Quality → Select "HD"
- [ ] **Expected:** Page reloads showing only HD videos
- [ ] Context menu → Sort By → Select "Most Viewed"
- [ ] **Expected:** Videos re-sort by view count
- [ ] Click "Clear all filters"
- [ ] **Expected:** Resets to default view

---

## 🔍 Debugging & Logs

### **Enable Debug Logging**

1. Go to: **Settings → System → Logging**
2. Enable: **Enable debug logging**
3. Optional: **Enable component-specific logging** → Select all

### **View Kodi Log**

**Location by platform:**
- **Windows:** `%APPDATA%\Kodi\kodi.log`
- **Linux:** `~/.kodi/temp/kodi.log`
- **Mac:** `~/Library/Logs/kodi.log`
- **Android:** `/sdcard/Android/data/org.xbmc.kodi/files/.kodi/temp/kodi.log`

### **Search for Cumination Errors**

Open the log file and search for:
- `@@@@Cumination` - All addon log messages
- `Error parsing video item` - BeautifulSoup parsing errors
- `SQL` or `sqlite3` - Database errors
- `BeautifulSoup not available` - Missing dependency
- `Traceback` - Python exceptions

---

## 📊 What to Report

If you encounter issues, please report:

### **1. Basic Info**
- Kodi version (e.g., Kodi 20.2)
- Platform (Windows/Linux/Mac/Android/etc.)
- Cumination version: **1.1.165**

### **2. What Failed**
- Which test from checklist?
- Which site? (e.g., PornHub, SpankBang)
- What action? (e.g., opening site, pagination, search)

### **3. Error Details**
- Screenshot if possible
- Relevant log excerpts (search for `@@@@Cumination`)
- Any error messages shown on screen

### **4. What Works**
- Which tests passed?
- Which sites work correctly?

---

## 🎉 Expected Results

### **If Everything Works:**

✅ **PornHub:**
- Videos load quickly
- Pagination works smoothly
- Categories display correctly
- Search returns results
- Video playback works

✅ **Other Sites:**
- Continue working as before
- No regressions

✅ **Favorites:**
- Can add/remove favorites
- Favorites list displays correctly
- No database errors

✅ **Overall:**
- No SQL errors in logs
- No crashes
- Same or better performance

### **Known Limitations:**

⚠️ **Sucuri-protected sites:**
- May show error: "Please configure FlareSolverr"
- This is intentional (old unsafe bypass disabled)
- Solution: Set up FlareSolverr in addon settings

⚠️ **Old Cloudflare challenges:**
- May fail on some sites with old CF protection
- Solution: Use FlareSolverr

---

## 🆘 Rollback Instructions

If this build doesn't work:

1. **Uninstall current version:**
   - Go to: **Add-ons → My add-ons → Video add-ons**
   - Select: **Cumination**
   - Choose: **Uninstall**

2. **Reinstall previous version:**
   - Install from repository or previous ZIP file

3. **Your data is safe:**
   - Favorites are stored in `userdata/addon_data/plugin.video.cumination/`
   - They will restore automatically when you reinstall

---

## 📝 Version Info

**Build:** plugin.video.cumination-1.1.165.zip
**Build Date:** 2025-11-01
**Changes:**
- Security fixes (SQL injection)
- BeautifulSoup infrastructure
- PornHub site migration
- Multiple cam sites database fixes

**Dependencies:**
- Kodi 18.0+ (Leia or newer)
- script.module.beautifulsoup4 (NEW - required)
- script.module.kodi-six
- script.module.resolveurl
- script.module.resolveurl.xxx
- Other existing dependencies

---

## 🤝 Support

**Issues?** Report with:
1. Which test failed (from checklist above)
2. Kodi log excerpt
3. Your system info

**Questions?** Ask about:
- Installation steps
- BeautifulSoup4 addon
- Specific site behavior
- Log interpretation

---

## ✨ What's Different?

**User Experience:**
- PornHub site should be **more reliable**
- Fewer "site broken" errors over time
- Better error messages when things fail
- Slightly more verbose logging (for debugging)

**Under the Hood:**
- 30+ SQL injection vulnerabilities fixed
- Unsafe code execution removed
- Modern HTML parsing (PornHub only for now)
- Foundation for migrating other sites

---

**Good luck testing! 🚀**
