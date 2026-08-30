# Composition Validator - Synthesis Rules Extraction

**Date**: December 1, 2025
**Tool**: `composition_validator.py`
**Part Of**: SET-3 Agent Development Patterns
**Focus**: Validation rules for agent architectures against PLAYBOOK-3 best practices

---

## Rules Applied (10 total)

### Core Component Rules

#### comp_001_tool_registry_structure
**Category**: Composition
**Confidence**: 0.99
**Title**: Agent Tool Registry Structure - 4 Core Components Required

**Description**:
Valid agent architectures require exactly 4 core components present and properly configured:
1. agent_name (string) - Unique identifier for the agent
2. tools (list) - Array of tool definitions or tool names with registry
3. max_iterations (int) - Hard limit on iteration count
4. error_handling (dict) - Explicit error handling configuration

**Validation Rule**:
```python
CORE_COMPONENTS = [
    "agent_name",      # Required: identifies agent
    "tools",           # Required: defines available tools
    "max_iterations",  # Required: prevents infinite loops
    "error_handling"   # Required: handles failures explicitly
]
```

**Cost Impact**: Missing components = 20% compliance penalty per component
**Implementation**: Validate presence and type of each component

**Examples**:
- ✓ PASS: Agent with all 4 components properly defined
- ✗ FAIL: Agent missing error_handling configuration
- ✗ FAIL: Agent without max_iterations (infinite loop risk)

---

### Safety Rules

#### anti_001_infinite_tool_loops
**Category**: Anti-pattern
**Confidence**: 0.99
**Title**: Agents Must Prevent Infinite Tool Use Loops

**Description**:
Critical safety rule: agents looping indefinitely on tool calls consume unbounded costs and must be prevented with explicit limits.

**Prevention Mechanisms** (at least one required):
1. max_iterations: Hard limit on number of iterations
2. termination_criteria: Explicit completion conditions
3. loop_detection: Runtime detection of cycles

**Validation Rule**:
```python
# INVALID: No loop prevention
if not max_iterations and not termination_criteria:
    FAIL("Neither max_iterations nor termination_criteria specified")

# VALID: Has loop prevention
if max_iterations > 0 or termination_criteria:
    PASS("Infinite loop prevention enforced")
```

**Cost Impact**: Without prevention: cost → ∞ | With prevention: cost bounded
**Examples**:
- ✗ FAIL: Agent in loop calling same tool repeatedly
- ✓ PASS: Agent with max_iterations=10 termination clause

---

#### anti_002_silent_tool_failures
**Category**: Anti-pattern
**Confidence**: 0.97
**Title**: Tool Errors Must Be Explicitly Reported

**Description**:
Tool failures without error reporting leave agent without context, causing poor subsequent decisions and wasted iterations.

**Required Components**:
```python
error_handling = {
    "retry_policy": "exponential_backoff" | "immediate" | "none",
    "fallback_strategy": "skip_tool" | "escalate" | "abort",
    "logging": True  # Always log errors
}
```

**Validation Rule**:
- Check error_handling exists and is configured
- Verify retry_policy is specified
- Verify fallback_strategy is defined
- Verify logging is enabled

**Cost Impact**:
- With errors: 1-2 retries | Silent: 5-10 wasted calls then failure
- Silent failures = 300% cost increase from unnecessary iterations

**Examples**:
- ✗ FAIL: API timeout without error message to agent
- ✓ PASS: Tool returns {"error": "timeout", "retry_after": 5, "is_error": true}

---

#### anti_003_no_caching_implementation
**Category**: Anti-pattern
**Confidence**: 0.96
**Title**: Agents Without Caching Waste 85-90% of Costs

**Description**:
Agents without caching waste dramatically because:
- Tool definitions resent with every request (unnecessary)
- System prompts resent with every request (unnecessary)
- Conversation history duplicated (unnecessary)

**Three-Layer Caching Strategy Required**:
```
Layer 1: System Prompt + Tool Definitions (ephemeral cache)
Layer 2: Tool Outputs (ephemeral cache, 5 min TTL)
Layer 3: Conversation History (growing, 24 hour TTL)
```

**Validation Rule**:
- Check for caching_layers configuration
- Validate that at minimum "system" layer is cached
- Recommend full 3-layer strategy

**Cost Impact**:
- No caching: $500/day for 10K conversations
- With caching: $50/day for same workload (90% savings)

**Examples**:
- ✗ FAIL: Tool definitions sent with every request (no cache)
- ✓ PASS: caching_layers: ["system", "tools", "conversation"]

---

#### anti_004_unconstrained_thinking
**Category**: Anti-pattern
**Confidence**: 0.90
**Title**: Extended Thinking Must Have Budget Constraints

**Description**:
Extended thinking without explicit budget constraints adds 10-30% cost for no justification on simple tasks.

**Budget Recommendations by Task Complexity**:
```python
COMPLEXITY_BUDGETS = {
    "trivial": 500,           # "What's 2+2?"
    "simple": 1000,           # "Fix typo"
    "moderate": 5000,         # "Design component"
    "complex": 10000,         # "Multi-step workflow"
    "very_complex": 15000     # "System redesign"
}
```

**Validation Rule**:
- If thinking_mode enabled, must have budget_tokens
- Budget must be >= 100 (minimum viable)
- Budget should match task_complexity recommendation

**Cost Impact**:
- Unconstrained: 30% cost increase on all tasks
- Proper constraint: Cost only on justified tasks

**Examples**:
- ✗ FAIL: thinking_mode enabled without budget_tokens
- ✗ FAIL: Complex task with thinking_budget=100 (too small)
- ✓ PASS: Moderate task with thinking_budget=5000

---

#### anti_005_missing_session_management
**Category**: Anti-pattern
**Confidence**: 0.94
**Title**: Multi-Turn Agents REQUIRE Session Management

**Description**:
Multi-turn agents need session persistence to maintain conversation state across interactions. Without it:
- Conversation history lost between turns
- Previous API calls' benefits lost (caching breaks)
- User experience broken

**Session Management Requirements**:
```python
# REQUIRED for multi-turn agents:
session_management = {
    "type": "database" | "redis" | "file",
    "ttl_hours": 24,  # Session lifetime
    "persistence": True
}
```

**Validation Rule**:
- Only applies to agent_type == "multi_turn"
- Single-turn agents (agent_type == "single_turn") exempt
- Must have complete session config if multi-turn

**Cost Impact**:
- Without sessions: Each turn pays full cost (caching broken)
- With sessions: 90% savings continue across turns

**Examples**:
- ✗ FAIL: Multi-turn chatbot losing context between refreshes
- ✓ PASS: Session persistence with database storage

---

### Constraint Rules

#### constr_002_max_iterations_safety
**Category**: Constraint
**Confidence**: 0.98
**Title**: Max Iterations Must Be Set (Hard Safety Constraint)

**Description**:
Maximum iterations is non-negotiable safety constraint. Agents without limits risk:
- Unbounded cost (system compromise)
- Infinite loops (system hang)
- Resource exhaustion

**Implementation**:
```python
# REQUIRED:
max_iterations: int  # Must be positive integer > 0

# RECOMMENDED BY COMPLEXITY:
task_complexity = {
    "trivial": 3,         # Simple single-step tasks
    "simple": 5,          # Straightforward operations
    "moderate": 10,       # Multi-step workflows
    "complex": 15,        # Research, analysis tasks
    "very_complex": 20    # System design, planning
}
```

**Validation Rule**:
- max_iterations must be present
- Must be positive integer
- Warning if significantly exceeds recommendation

**Cost Impact**:
- Without limit: Cost → ∞ | With limit: Cost bounded × max_iterations

**Examples**:
- ✗ FAIL: max_iterations not specified
- ✗ FAIL: max_iterations = 0 or negative
- ⚠ WARNING: max_iterations = 50 for trivial task
- ✓ PASS: max_iterations = 10 for moderate task

---

### Composition Rules

#### comp_003_three_layer_caching_strategy
**Category**: Composition
**Confidence**: 0.94
**Title**: Three-Layer Caching Strategy for Cost Optimization

**Description**:
Caching provides multiplicative cost reductions when properly layered:
- 1 layer: 50% savings
- 2 layers: 75% savings
- 3 layers: 90% savings

**Three Layers**:
```
Layer 1 (SYSTEM): Tool definitions + system prompt
  - Type: ephemeral cache
  - TTL: 5 minutes
  - Savings: 30-50%

Layer 2 (TOOLS): Tool outputs for repeated calls
  - Type: ephemeral cache
  - TTL: 5 minutes
  - Savings: 20-40%

Layer 3 (CONVERSATION): Growing conversation history
  - Type: persistent (growing)
  - TTL: 24+ hours
  - Savings: 30-60%
```

**Validation Rule**:
- Check caching_layers array
- Count implemented layers
- Estimate savings based on layers present

**Cost Impact**: Multiplicative
- No caching: 100% cost
- 1 layer: 50% cost
- 2 layers: 25% cost
- 3 layers: 10% cost

**Examples**:
- ✗ FAIL: caching_layers not specified
- ⚠ WARNING: Only "system" layer cached (50% savings)
- ✓ PASS: All three layers cached (90% savings)

---

### Compatibility Rules

#### compat_001_tool_caching_with_multi_calls
**Category**: Compatibility
**Confidence**: 0.92
**Title**: Tool Caching Compatible Only With Multi-Call Scenarios

**Description**:
Tool caching (especially tool definition caching) is only beneficial when:
- Same tools called multiple times
- Same tool definitions sent multiple times
- Multi-turn or batch scenarios

**Validation Rule**:
- Identify high-frequency tools
- Add rate limiting for external API tools
- Cache tool definitions that are called repeatedly

**Cost Impact**:
- Single tool call: caching overhead wastes resources
- 10+ tool calls: caching saves 50-80%

**Examples**:
- ✗ NOT RECOMMENDED: Single one-off tool call with caching overhead
- ✓ RECOMMENDED: 20 web_search calls within 5 minutes (cache hits)

---

#### compat_005_agent_tool_definitions
**Category**: Compatibility
**Confidence**: 0.91
**Title**: Tool Definitions Must Be Cacheable

**Description**:
Tool definitions should be:
1. Included in system prompt (cacheable)
2. Formatted consistently (enables cache hits)
3. Validated against schema before caching

**Tool Definition Requirements**:
```python
tool_definition = {
    "name": str,                    # Unique tool identifier
    "description": str,             # Clear description (clarity >= 0.8)
    "parameters": {                 # JSON Schema
        "type": "object",
        "properties": { ... },
        "required": [ ... ]
    }
}
```

**Validation Rule**:
- Check that tool definitions are in system prompt with cache_control
- Verify all tools have name + description + parameters
- Ensure consistency across calls (exact byte match for cache)

**Cost Impact**:
- Tools not cached: redefined every request
- Tools cached: single definition, reused

**Recommendation**:
- Use cache_control: {"type": "ephemeral"} on tool definitions
- Achieves 30-40% cost reduction for multi-turn scenarios

---

## Meta-Insights Extracted

### Insight 1: Core Components Are Minimum Viable Architecture
The 4 core components (agent_name, tools, max_iterations, error_handling) form the absolute minimum required for a safe agent. Missing even one introduces critical risks:
- No agent_name: Cannot track executions
- No tools: Agent cannot interact with world
- No max_iterations: Unbounded cost risk (system compromise)
- No error_handling: Silent failures cascade

**Implication**: Validation should treat missing components as CRITICAL failures.

### Insight 2: Safety Rules Have Hierarchical Severity
Safety rules follow severity hierarchy:
1. **CRITICAL** (must not be violated): infinite_loop_prevention, error_handling
2. **HIGH** (strongly recommended): caching, session_management
3. **MEDIUM** (best practices): thinking_budget, rate_limiting
4. **LOW** (optimizations): multi-layer caching strategy

**Implication**: Validator can recommend without blocking execution, but critical rules must fail validation.

### Insight 3: Caching Savings Are Multiplicative
Unlike additive cost savings (batch + thinking), caching layers compound:
- Base cost: 100%
- +System cache: 50%
- +Tool cache: 25% (50% of 50%)
- +Conversation cache: 10% (50% of 25%)

**Formula**: Total_cost = Base × 0.5^(num_layers)

**Implication**: Third layer provides highest ROI despite effort. Going from 2→3 layers cuts cost in half again.

### Insight 4: Session Management Is Binary (Not Gradual)
For multi-turn agents, session management is binary:
- Present: 90% savings continue across turns
- Absent: Each turn pays 100% cost (cache resets)

**Implication**: For multi-turn scenarios, cost difference is 10x (not 1.5x). This is the single highest-impact safety rule.

### Insight 5: Error Handling Prevents Exponential Cost Growth
Without explicit error handling, failed tools cause cascading iterations:
- Tool fails silently → Agent retries → Tool fails again → Loop
- Result: 5-10 wasted iterations before agent gives up
- Cost multiplier: 5-10x

**Implication**: Error handling is cheaper than the cost of debugging failures in production.

### Insight 6: Thinking Budget Must Match Task Complexity
Extended thinking without matching task complexity wastes resources:
- Simple task (trivial) with 10K budget: 20x unnecessary cost
- Complex task (very_complex) with 500 budget: Reasoning truncated

**Formula**: ROI = benefit_from_thinking / (thinking_budget × cost_per_token)

**Implication**: Budget should scale with task signals (decision points, uncertainty, novelty).

### Insight 7: Multi-Turn Agents Have Different Rules
Multi-turn agents introduce new requirements not present in single-turn:
- Session management (persist state)
- Growing caching strategy (history grows each turn)
- Context window management (token count increases)

**Implication**: Validation rules must differentiate agent_type. Single-turn validators should not fail on session management.

### Insight 8: Compliance Score Is Weighted, Not Averaged
Compliance score weights components by risk:
- Missing core components: -20% each (4 components = -80% if all missing)
- Failed safety checks: -15% each (5 checks)
- Anti-patterns: -25% for CRITICAL, -15% for HIGH, -10% for MEDIUM
- Missing caching layers: -10% total (distributed across 3 layers)

**Implication**: Single critical issue can tank score to 50% even if other things are good.

---

## Validation Rules Implementation Details

### Validation Algorithm

```
1. Load agent architecture
2. Validate core components (fail if any missing)
3. Run 5 safety checks (fail if critical, warn if high)
4. Detect 5 anti-patterns
5. Validate caching strategy
6. Generate recommendations
7. Calculate compliance score with weighting
8. Determine overall status (passed/warning/failed)
9. Return full report with improvements
```

### Compliance Score Calculation

```python
score = 1.0
score -= 0.20 * (missing_components / 4)
score -= 0.15 * (failed_safety_checks)
score -= 0.05 * (warning_safety_checks)
score -= 0.25 * (critical_patterns)
score -= 0.15 * (high_patterns)
score -= 0.10 * (medium_patterns)
score -= 0.10 * (missing_cache_layers / 3)
return max(0.0, min(1.0, score))
```

### Overall Status Determination

```
FAILED if:
  - Any missing core components
  - Any critical safety check failure
  - Any critical anti-pattern

PASSED_WITH_WARNINGS if:
  - All core components present
  - No critical failures
  - Some warnings or high-severity patterns

PASSED if:
  - All core components present
  - All safety checks pass
  - No anti-patterns or only low-severity
```

---

## Recommendations Engine

Recommendations are generated based on validation findings and prioritized:

### Priority Levels
- **HIGH**: Cost reduction > 20%, or security improvement
- **MEDIUM**: Cost reduction 10-20%, or reliability improvement
- **LOW**: Cost reduction < 10%, or optimizations

### Categories
- **caching**: Add missing caching layers
- **error_handling**: Improve error handling
- **safety**: Add safety constraints
- **performance**: Optimize latency or throughput
- **thinking**: Adjust thinking budget

### Estimated Benefits
Each recommendation includes:
- Estimated cost reduction percentage
- Estimated latency improvement
- Implementation complexity (low/medium/high)
- Related rules that would be addressed

---

## Summary Statistics

**Total Rules Applied**: 10
**Categories**:
- Anti-pattern rules: 3 (anti_001, anti_002, anti_003, anti_004, anti_005)
- Composition rules: 2 (comp_001, comp_003)
- Constraint rules: 1 (constr_002)
- Compatibility rules: 2 (compat_001, compat_005)

**Validation Coverage**:
- Core components: 100% (4/4 required)
- Safety checks: 5 checks across 5 rules
- Anti-patterns: 5 patterns detected
- Caching validation: 3-layer strategy
- Recommendations: Generated from findings

**Severity Levels Tracked**:
- CRITICAL: 3 rules (infinite loops, error handling, max iterations)
- HIGH: 4 rules (caching, session management, tool definitions)
- MEDIUM: 2 rules (thinking budget, rate limiting)
- LOW: 1 rule (optimization recommendations)

