# Fix: Module Not Found Errors in React Dev Server

**Problem:** Webpack dev server can't find components even though they exist.

**Root Cause:** React Scripts (webpack) caching issue - the dev server cache gets corrupted and doesn't see file changes.

---

## ✅ Quick Fix (Choose One)

### **Option 1: Complete Restart (Recommended)**

```bash
cd frontend

# Kill all dev servers
pkill -f react-scripts

# Clear all caches
rm -rf node_modules/.cache
rm -rf .cache
rm -rf build

# Restart
npm start
```

### **Option 2: Use Restart Script**

```bash
cd frontend
./restart_dev_server.sh
```

### **Option 3: Nuclear Option (If Above Fails)**

```bash
cd frontend

# Kill servers
pkill -f react-scripts
pkill -f node

# Remove everything
rm -rf node_modules
rm -rf node_modules/.cache
rm -rf build
rm -rf .cache

# Reinstall
npm install

# Start fresh
npm start
```

---

## 🔍 Why This Happens

**React Scripts/Webpack Issue:**
1. Dev server uses aggressive caching for speed
2. Sometimes cache gets out of sync with file system
3. Particularly common after:
   - Git checkouts
   - File moves/renames
   - Large commits
   - Computer sleep/wake

**Not a Code Problem:**
- ✅ All component files exist
- ✅ All imports are correct
- ✅ Build works fine (`npm run build`)
- ❌ Dev server cache is stale

---

## 🎯 Verify Files Exist

If you get module errors, verify files actually exist:

```bash
cd frontend

# Check bridge components
ls -la src/components/bridge/
# Should see: BridgeCard.jsx, BiddingBox.jsx, etc.

# Check play components
ls -la src/components/play/
# Should see: TurnIndicator.js, ScoreModal.jsx, etc.

# Check other components
ls -la src/components/
ls -la src/components/auth/
ls -la src/components/learning/
```

**If files are missing:**
- Check git status: `git status`
- Check recent commits: `git log --oneline -5`
- Checkout from git: `git checkout <file>`

**If files exist but error persists:**
- It's a cache issue - use Option 1 above

---

## 🚫 Common Mistakes

**DON'T do these:**
- ❌ Just run `npm start` again (cache persists)
- ❌ Only clear `node_modules/.cache` (there are other caches)
- ❌ Try to fix imports (they're already correct)
- ❌ Reinstall npm packages (not needed usually)

**DO these:**
- ✅ Kill the process first
- ✅ Clear ALL caches
- ✅ Then restart

---

## 📊 Verification

After restarting, you should see:

```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.X.X:3000
```

**If you still see errors:**
1. Check the error message carefully
2. Verify file paths in error match actual files
3. Check import statements in App.js
4. Try Nuclear Option (Option 3)

---

## 🔧 Prevention

To avoid this issue:

1. **Always stop dev server before:**
   - Git checkout/pull
   - Large file moves
   - Switching branches

2. **Clear cache periodically:**
   ```bash
   rm -rf node_modules/.cache
   ```

3. **Use build to verify:**
   ```bash
   npm run build
   ```
   If build works, it's definitely a dev server cache issue.

---

## 💡 Understanding the Error

When you see:
```
ERROR: Can't resolve './components/bridge/BridgeCard'
```

This means:
- Webpack looked for `src/components/bridge/BridgeCard.jsx`
- Webpack's cached file index says it doesn't exist
- But the file DOES exist on disk
- Solution: Clear cache so webpack rebuilds its index

---

## 🎯 For Your Technical Review

**When demonstrating:**
1. ✅ Use production build (`npm run build` + `serve -s build`)
2. ✅ Or restart dev server before demo
3. ✅ Keep cache clear

**If error during demo:**
1. Stay calm - it's a known cache issue
2. Run Option 1 fix (takes 30 seconds)
3. Explain it's webpack caching (not a code bug)

---

**Last Updated:** 2025-10-16
**Status:** Known Issue - Cache-related, not code bug
**Impact:** Development only (production builds work fine)
