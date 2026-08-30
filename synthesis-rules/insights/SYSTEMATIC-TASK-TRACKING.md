# Systematic Task Tracking - Preventing Lost Items
**Created:** 2025-10-30
**Trigger:** Discovered NLKE KG migration was missing from tracking

---

## The Problem

**What Happened:** Completed Cycle 1 (Master KG extraction) but forgot about pending NLKE KG SQLite migration.

**Why It Happened:** TodoWrite was used for *current cycle tasks* but not for *discovered pending items*.

**Impact:** Could have completed NLKE migration during the same session instead of deferring to next session.

---

## The Solution: Multi-Level Todo Tracking

### Level 1: Session Todos (Current Focus)
**Purpose:** Track current cycle/session tasks
**Update Frequency:** Real-time during session
**Example:**
- Phase 1: Extract nodes
- Phase 2: Define relationships
- Phase 3: Migrate to SQLite

### Level 2: Discovered Todos (Found During Work)
**Purpose:** Capture items discovered while working
**Update Frequency:** Immediately when discovered
**Example:**
- Found NLKE KG has JSON but no SQLite → Add todo immediately
- Found Gemini CLI KG exists → Add todo to explore/integrate
- Found process improvement opportunity → Add todo to implement

### Level 3: Strategic Todos (Future Cycles)
**Purpose:** Track planned future work
**Update Frequency:** At end of each cycle
**Example:**
- Cycle 2: Create Handbooks 4-6
- Cycle 3: Integrate all knowledge graphs
- Future: Implement direct SQLite extraction

---

## Systematic Checklist for End of Session

### Before Saying "We're Done"

Run this checklist to catch missed items:

1. **File System Audit**
   ```bash
   # Find all JSON knowledge graphs
   ls -lh *knowledge-graph*.json

   # Check which have SQLite equivalents
   ls -lh *.db kg-factory/backend/*.db

   # Identify gaps
   ```

2. **TodoWrite Comprehensive Update**
   - [ ] Current cycle tasks marked complete
   - [ ] Discovered pending items added
   - [ ] Future cycle tasks outlined
   - [ ] Dependencies noted

3. **Documentation Cross-Check**
   - [ ] Session summary mentions all discovered items
   - [ ] Handoff package includes all action items
   - [ ] Known issues section captures everything

4. **Knowledge Graph Inventory**
   - [ ] All JSON knowledge graphs identified
   - [ ] All SQLite databases identified
   - [ ] Missing migrations documented in todos
   - [ ] Integration opportunities noted

5. **System State Verification**
   - [ ] All services documented (running/stopped)
   - [ ] All databases listed (active/archived)
   - [ ] All configuration files noted
   - [ ] All log files identified

---

## Prevention Mechanisms

### 1. Proactive Todo Scanning

**After ANY discovery operation (Glob, ls, find), immediately check:**
- "Did I find something that needs action?"
- "Should this be in the todo list?"
- "Is there a matching SQLite for this JSON?"

**Example:**
```bash
# After discovering files
ls -lh *knowledge-graph*.json
# Immediately ask: "Which of these need SQLite migration?"
# Immediately add to TodoWrite if missing
```

### 2. State Transition Todos

**When changing work focus, always:**
1. Mark current todos complete
2. Scan for new todos discovered during work
3. Add strategic todos for next phase

### 3. Inventory-Driven Todos

**Maintain inventories, generate todos from gaps:**

**Knowledge Graph Inventory:**
- Claude API KG: JSON ✅ SQLite ✅
- Gemini CLI KG: JSON ✅ SQLite ✅
- Master KG: JSON ✅ SQLite ✅
- NLKE KG: JSON ✅ SQLite ❌ → **ADD TODO**

**Documentation Inventory:**
- Session Summary: ✅
- Meta-Cognition: ✅
- Handoff Package: ✅
- Quick Reference: ❌ → **ADD TODO**

### 4. Cross-Reference Validation

**Before ending session:**
1. Session summary mentions all files → Check todos include all action items
2. Handoff package lists databases → Check todos include missing migrations
3. System audit shows gaps → Check todos include remediation

---

## Template: End of Session Todo Update

```markdown
## Completed This Session
- [x] [List what was actually completed]

## Discovered Pending Items
- [ ] [Items found during work that need future action]
- [ ] [Missing migrations, configurations, etc.]

## Strategic Next Steps
- [ ] [Planned future cycles]
- [ ] [Process improvements to implement]

## Dependencies / Blockers
- [ ] [Items waiting on user decision]
- [ ] [Items requiring external resources]
```

---

## Tools to Use

### 1. TodoWrite (Primary)
**When to use:**
- Start of session (current tasks)
- During session (discovered items)
- End of session (future planning)

**How to use:**
- Mark completed tasks immediately
- Add discovered items immediately
- Include both content and activeForm

### 2. Glob + ls (Discovery)
**When to use:** Any file operation

**Trigger question:**
"Did I just discover something that needs action?"

**Example workflow:**
```bash
ls -lh *knowledge-graph*.json  # Discovery
# → See nlke-knowledge-graph-v1.json
# → Question: "Does this have SQLite?"
ls -lh *nlke*.db  # Check
# → No match
# → Action: Add to TodoWrite immediately
```

### 3. Grep (Validation)
**When to use:** Checking documentation completeness

**Example:**
```bash
# Check if NLKE is mentioned in handoff
grep -i nlke HANDOFF-PACKAGE.md
# If missing → Update documentation AND todos
```

---

## Real Example from Today

### What Happened (Imperfect)
1. Completed Master KG extraction
2. Used TodoWrite for cycle tasks only
3. User reminder: "don't forget NLKE KG"
4. Realized it was missing from todos

### What Should Have Happened (Systematic)
1. Complete Master KG extraction
2. Run inventory: `ls -lh *knowledge-graph*.json`
3. See 4 JSON files: Claude API, Gemini CLI, Master, NLKE
4. Check SQLite: `ls -lh *.db kg-factory/backend/*.db`
5. See 3 databases: Claude API, Gemini CLI, Master
6. **Immediately add to TodoWrite:** "NLKE KG missing SQLite migration"
7. Include in session summary and handoff

### Updated End-of-Session Checklist (Integrated)
```bash
# 1. Mark current work complete in TodoWrite
# 2. Run inventory
ls -lh *knowledge-graph*.json
ls -lh *.db kg-factory/backend/*.db

# 3. Identify gaps
# Compare lists → Find missing migrations

# 4. Update TodoWrite immediately
# Add all discovered pending items

# 5. Verify in documentation
grep -i "missing\|pending\|todo" SESSION-SUMMARY*.md HANDOFF*.md

# 6. Final TodoWrite review
# Ensure all gaps are captured
```

---

## Meta-Cognition Insight

**Learning:** TodoWrite is not just for *current work* - it's for *all known work*
- ✅ Current cycle tasks
- ✅ Discovered pending items
- ✅ Strategic future work
- ✅ Missing migrations
- ✅ Process improvements

**Updated Practice:**
After ANY discovery operation (ls, Glob, inventory, audit):
1. Ask: "Did I find work that needs to be done?"
2. If yes: Add to TodoWrite immediately
3. Don't wait until "end of session"

**This prevents:** Forgetting items that were discovered but not immediately acted upon.

---

## Checklist for Next Session Start

1. **Read TodoWrite list** (captures all pending from previous sessions)
2. **Read HANDOFF-PACKAGE.md** (system state, action items)
3. **Read SESSION-SUMMARY** (context from last session)
4. **Run inventory** (verify current state matches documentation)
5. **Update todos** (mark completed, add newly discovered)

---

## Success Metrics

**Before this system:**
- ❌ Discovered NLKE KG needs migration → Forgot until user reminder

**With this system:**
- ✅ Discover item → Add to TodoWrite immediately
- ✅ End of session → All gaps captured
- ✅ Next session → Start with complete todo list
- ✅ No user reminders needed for discovered items

---

## Integration with Meta-Cognition Framework

This systematic task tracking should be added to `meta-cognition-framework.md` as:

**Part 6: Meta-Cognition for AI Agents**
- Section 6.4: **Systematic Task Discovery and Tracking**
  - Proactive todo scanning after discoveries
  - Inventory-driven todo generation
  - Multi-level todo tracking (current/discovered/strategic)
  - Prevention mechanisms for forgetting discovered items

---

## Template Code for Auto-Discovery

```python
# Add this to end-of-session routine
def discover_pending_todos():
    """Scan for common forgotten items"""
    import json
    from pathlib import Path

    todos = []

    # Find JSON KGs without SQLite
    for json_file in Path('.').glob('*knowledge-graph*.json'):
        expected_db = json_file.stem + '.db'
        if not Path(expected_db).exists():
            todos.append(f"Convert {json_file.name} to SQLite")

    # Find incomplete documentation
    expected_docs = [
        'SESSION-SUMMARY-*.md',
        'HANDOFF-PACKAGE.md',
        'meta-cognition-framework.md'
    ]
    for pattern in expected_docs:
        if not list(Path('.').glob(pattern)):
            todos.append(f"Create missing: {pattern}")

    return todos

# Run before ending session
pending = discover_pending_todos()
if pending:
    print("⚠️ Discovered pending todos:")
    for todo in pending:
        print(f"  - {todo}")
    print("\n→ Add these to TodoWrite before ending session!")
```

---

**Next Update:** Integrate this into meta-cognition-framework.md as Section 6.4
