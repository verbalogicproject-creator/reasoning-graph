#!/usr/bin/env python3
"""
reasoning-graph P2 query unit — NLKE Intent-Driven Query Interface.

Ported 2026-07-14 from systems/eco-system/extra/intent_query.py per open call
#7's declaration ("adapt extra/intent_query.py — smallest unit of adaptation").
Schema match was exact (nodes.node_id/name/description/node_type, edges.
source_node_id/target_node_id/edge_type — the same 'claude' profile as
kgs/reasoning-graph.db) so this is a port, not a redesign: default DB path
repointed at the combined store, --db/--json added, everything else — all 7
plan-declared primitives (want_to/can_it/compose_for/trace/why_not/
similar_to/alternatives) plus the original's 10 Phase-2 extensions — kept as-is.

This module implements the NLKE query patterns:
- want_to(goal) - "I want to X" -> find tools that achieve the goal
- can_it(capability) - "Can Claude Code do X?" -> yes/no + how + limitations
- trace(node_a, node_b) - Find path between two nodes in the KG

Paradigm: Structure > Training. The KG IS the semantic index.
No embeddings needed - Claude-in-conversation provides semantic analysis.

NLKE Validation #7 - Gemini-3-Pro Integration
November 2025
"""

import sqlite3
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict

DB_PATH = Path(__file__).parent / "kgs" / "reasoning-graph.db"


# =============================================================================
# GOAL-TO-TOOL MAPPINGS (Emergent Insight #26: Intent IS the Embedding)
# =============================================================================

GOAL_TO_TOOLS = {
    # File Operations
    'read': ['Read'], 'view': ['Read'], 'examine': ['Read'], 'check': ['Read'],
    'look': ['Read'], 'inspect': ['Read'], 'see': ['Read'], 'open': ['Read'],

    'write': ['Write'], 'create': ['Write'], 'make': ['Write'],
    'save': ['Write'], 'generate': ['Write'], 'output': ['Write'],

    'edit': ['Edit'], 'modify': ['Edit'], 'fix': ['Edit'], 'change': ['Edit'],
    'update': ['Edit'], 'patch': ['Edit'], 'replace': ['Edit'],

    # Search Operations
    'find': ['Glob', 'Grep'], 'search': ['Grep', 'Glob', 'WebSearch'],
    'locate': ['Glob', 'Grep'], 'discover': ['Glob', 'Grep'],
    'match': ['Grep', 'Glob'], 'pattern': ['Grep', 'Glob'],

    # Execution
    'run': ['Bash'], 'execute': ['Bash'], 'test': ['Bash'],
    'build': ['Bash'], 'install': ['Bash'], 'compile': ['Bash'],
    'deploy': ['Bash'], 'start': ['Bash'], 'command': ['Bash'],

    # Web Operations
    'fetch': ['WebFetch'], 'download': ['WebFetch'], 'get': ['WebFetch'],
    'url': ['WebFetch'], 'http': ['WebFetch'], 'webpage': ['WebFetch'],
    'google': ['WebSearch'], 'lookup': ['WebSearch'],

    # Meta Operations
    'delegate': ['Task'], 'agent': ['Task'], 'parallel': ['Task'],
    'subagent': ['Task'], 'spawn': ['Task'],

    'plan': ['TodoWrite'], 'track': ['TodoWrite'], 'todo': ['TodoWrite'],
    'organize': ['TodoWrite'], 'checklist': ['TodoWrite'],

    'ask': ['AskUserQuestion'], 'question': ['AskUserQuestion'],
    'clarify': ['AskUserQuestion'], 'confirm': ['AskUserQuestion'],

    # Compound Goals (Emergent Insight #27: Multi-Tool Intent)
    'understand': ['Read', 'Glob', 'Grep'],
    'refactor': ['Grep', 'Read', 'Edit'],
    'debug': ['Read', 'Bash', 'Grep'],
    'explore': ['Glob', 'Grep', 'Read'],
    'implement': ['Read', 'Write', 'Edit'],
    'migrate': ['Grep', 'Read', 'Edit', 'Bash'],
    'document': ['Read', 'Write'],
}

# Intent keywords for classification (extends GOAL_TO_TOOLS with verb forms)
INTENT_KEYWORDS = {
    'cost_reduction': ['cost', 'cheap', 'save', 'budget', 'price', 'reduce', 'efficient'],
    'speed': ['fast', 'quick', 'performance', 'latency', 'slow', 'speed'],
    'scale': ['large', 'big', 'scale', 'volume', 'massive', 'many', 'batch'],
    'safety': ['safe', 'secure', 'protect', 'guard', 'permission', 'sandbox'],
    'simplicity': ['simple', 'easy', 'basic', 'straightforward', 'beginner'],
}


class IntentDrivenQuery:
    """
    NLKE-style intent-driven query interface.

    Key Insight: The KG structure already encodes semantic relationships.
    We don't need embeddings - we need intent classification and graph traversal.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._cache = {}

    def close(self):
        """Close database connection."""
        self.conn.close()

    # =========================================================================
    # CORE NLKE METHODS
    # =========================================================================

    def want_to(self, goal: str, k: int = 10) -> List[Dict]:
        """
        "I want to X" -> find tools/capabilities that achieve the goal.

        Implements NLKE query-cookbook.py want_to() pattern.

        Args:
            goal: User's goal in natural language
            k: Maximum number of results

        Returns:
            List of tools with relevance scores and explanations
        """
        goal_lower = goal.lower()
        results = []
        seen_tools = set()

        # Step 1: Direct goal-to-tool mapping
        for keyword, tools in GOAL_TO_TOOLS.items():
            if keyword in goal_lower:
                for tool_name in tools:
                    if tool_name not in seen_tools:
                        tool_info = self._get_tool_info(tool_name)
                        if tool_info:
                            tool_info['match_type'] = 'goal_keyword'
                            tool_info['matched_keyword'] = keyword
                            tool_info['score'] = 1.0
                            results.append(tool_info)
                            seen_tools.add(tool_name)

        # Step 2: Intent keyword matching from KG
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT node_id, name, description, intent_keywords
            FROM nodes
            WHERE node_type = 'tool' AND intent_keywords IS NOT NULL
        """)

        for row in cursor.fetchall():
            if row['name'] in seen_tools:
                continue

            intent_keywords = json.loads(row['intent_keywords']) if row['intent_keywords'] else []
            matches = [kw for kw in intent_keywords if kw.lower() in goal_lower]

            if matches:
                tool_info = self._get_tool_info(row['name'])
                if tool_info:
                    tool_info['match_type'] = 'intent_keyword'
                    tool_info['matched_keywords'] = matches
                    tool_info['score'] = len(matches) / max(len(intent_keywords), 1)
                    results.append(tool_info)
                    seen_tools.add(row['name'])

        # Step 3: Use case search
        use_case_matches = self._search_use_cases(goal_lower)
        for match in use_case_matches:
            if match['tool_name'] not in seen_tools:
                tool_info = self._get_tool_info(match['tool_name'])
                if tool_info:
                    tool_info['match_type'] = 'use_case'
                    tool_info['matched_use_case'] = match['use_case']
                    tool_info['score'] = 0.7
                    results.append(tool_info)
                    seen_tools.add(match['tool_name'])

        # Step 3.5 (added 2026-07-14, P2 port): synthesis_rule content search.
        # The original intent_query.py predates any rule nodes -- Steps 1-3 above
        # only ever query node_type='tool'. Without this, want_to() cannot surface
        # rule content at all (confirmed empirically: "is this agent architecture
        # complete?" returned zero rule matches before this addition). Mirrors the
        # use-case search shape exactly, just against synthesis_rule.description.
        seen_rules = set()
        rule_matches = self._search_rule_statements(goal_lower)
        for match in rule_matches:
            if match['rule_id'] not in seen_rules:
                rule_info = self._get_rule_info(match['rule_id'])
                if rule_info:
                    rule_info['match_type'] = 'rule_match'
                    rule_info['matched_word'] = match['matched_word']
                    rule_info['score'] = 0.65
                    results.append(rule_info)
                    seen_rules.add(match['rule_id'])

        # Step 4: Sort by score and return top k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]

    def can_it(self, capability: str) -> Dict:
        """
        "Can Claude Code do X?" -> yes/no + how + limitations + workarounds.

        Implements NLKE query-cookbook.py can_it() pattern.

        Args:
            capability: The capability to check

        Returns:
            Dict with 'can', 'how', 'limitations', 'workarounds'
        """
        capability_lower = capability.lower()
        result = {
            'can': False,
            'capability': capability,
            'how': [],
            'limitations': [],
            'workarounds': [],
            'related_tools': []
        }

        # Step 1: Check limitations that block this capability
        cursor = self.conn.cursor()

        # Find limitations matching the capability
        cursor.execute("""
            SELECT n.node_id, n.description, t.name as tool_name
            FROM nodes n
            JOIN edges e ON n.node_id = e.target_node_id
            JOIN nodes t ON e.source_node_id = t.node_id
            WHERE n.node_type = 'limitation'
              AND e.edge_type = 'tool_has_limitation'
              AND (LOWER(n.description) LIKE ? OR LOWER(n.name) LIKE ?)
        """, (f'%{capability_lower}%', f'%{capability_lower}%'))

        limitations = cursor.fetchall()
        if limitations:
            result['limitations'] = [
                {'description': l['description'], 'tool': l['tool_name']}
                for l in limitations
            ]

        # Step 2: Find workarounds for those limitations
        for limitation in limitations:
            cursor.execute("""
                SELECT w.description
                FROM edges e
                JOIN nodes w ON e.target_node_id = w.node_id
                WHERE e.source_node_id = ?
                  AND e.edge_type = 'has_workaround'
            """, (limitation['node_id'],))

            workarounds = cursor.fetchall()
            for w in workarounds:
                result['workarounds'].append({
                    'for_limitation': limitation['description'][:50],
                    'solution': w['description']
                })

        # Step 3: Check if any tool supports this capability via use cases
        cursor.execute("""
            SELECT t.name as tool_name, uc.description as use_case
            FROM nodes t
            JOIN edges e ON t.node_id = e.source_node_id
            JOIN nodes uc ON e.target_node_id = uc.node_id
            WHERE t.node_type = 'tool'
              AND e.edge_type = 'tool_has_use_case'
              AND LOWER(uc.description) LIKE ?
        """, (f'%{capability_lower}%',))

        matching_use_cases = cursor.fetchall()
        if matching_use_cases:
            result['can'] = True
            result['how'] = [
                {'tool': m['tool_name'], 'use_case': m['use_case']}
                for m in matching_use_cases
            ]
            result['related_tools'] = list(set(m['tool_name'] for m in matching_use_cases))

        # Step 4: Also check tool descriptions
        cursor.execute("""
            SELECT name, description
            FROM nodes
            WHERE node_type = 'tool'
              AND LOWER(description) LIKE ?
        """, (f'%{capability_lower}%',))

        for row in cursor.fetchall():
            if row['name'] not in result['related_tools']:
                result['related_tools'].append(row['name'])
                if not result['can']:
                    result['can'] = True

        # Step 5: Check intent keywords
        cursor.execute("""
            SELECT name, intent_keywords
            FROM nodes
            WHERE node_type = 'tool' AND intent_keywords IS NOT NULL
        """)

        # Fixed 2026-07-14 (found via organic query batch, not the fixture):
        # was phrase-substring-only ("capability_lower in kw or kw in capability_lower"),
        # which missed e.g. can_it("access the internet") even though web_fetch declares
        # intent_keyword "access url" -- neither phrase is a substring of the other. Every
        # other matcher in this file (want_to's Step 2/3, _search_rule_statements) already
        # splits on words; this brings Step 5 in line rather than leaving it as a special
        # case. Word-overlap is a superset of substring matching, so this can only add
        # matches, never remove ones the fixture already relies on.
        cap_words = set(w for w in capability_lower.split() if len(w) > 3)
        for row in cursor.fetchall():
            intent_keywords = json.loads(row['intent_keywords']) if row['intent_keywords'] else []
            matched = False
            for kw in intent_keywords:
                kw_lower = kw.lower()
                if capability_lower in kw_lower or kw_lower in capability_lower:
                    matched = True
                    break
                kw_words = set(w for w in kw_lower.split() if len(w) > 3)
                if cap_words & kw_words:
                    matched = True
                    break
            if matched:
                if row['name'] not in result['related_tools']:
                    result['related_tools'].append(row['name'])
                    if not result['can']:
                        result['can'] = True

        return result

    def trace(self, node_a: str, node_b: str, max_depth: int = 4) -> Dict:
        """
        Find path between two nodes in the KG.

        Implements NLKE trace_relationship() pattern for transitive inference.

        Args:
            node_a: Starting node (name or node_id)
            node_b: Target node (name or node_id)
            max_depth: Maximum search depth

        Returns:
            Dict with path, edge types, and inference explanation
        """
        # Resolve node names to IDs
        node_a_id = self._resolve_node_id(node_a)
        node_b_id = self._resolve_node_id(node_b)

        if not node_a_id or not node_b_id:
            return {
                'found': False,
                'error': f"Could not resolve: {node_a if not node_a_id else node_b}",
                'path': [],
                'edge_types': []
            }

        # BFS to find shortest path
        path = self._bfs_path(node_a_id, node_b_id, max_depth)

        if not path:
            return {
                'found': False,
                'from': node_a,
                'to': node_b,
                'path': [],
                'edge_types': [],
                'inference': f"No path found between {node_a} and {node_b} within depth {max_depth}"
            }

        # Get node names and edge types for the path
        path_names = []
        edge_types = []
        cursor = self.conn.cursor()

        for i, node_id in enumerate(path):
            cursor.execute("SELECT name, node_type FROM nodes WHERE node_id = ?", (node_id,))
            row = cursor.fetchone()
            if row:
                path_names.append({'name': row['name'], 'type': row['node_type']})

            if i < len(path) - 1:
                cursor.execute("""
                    SELECT edge_type FROM edges
                    WHERE source_node_id = ? AND target_node_id = ?
                """, (path[i], path[i+1]))
                edge_row = cursor.fetchone()
                if edge_row:
                    edge_types.append(edge_row['edge_type'])

        # Generate inference explanation
        inference = self._generate_inference(path_names, edge_types)

        return {
            'found': True,
            'from': node_a,
            'to': node_b,
            'path': path_names,
            'path_length': len(path) - 1,
            'edge_types': edge_types,
            'inference': inference
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Get comprehensive tool information."""
        cache_key = f"tool_{tool_name}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT node_id, name, title, description, category
            FROM nodes
            WHERE node_type = 'tool' AND LOWER(name) = LOWER(?)
        """, (tool_name,))

        row = cursor.fetchone()
        if not row:
            return None

        tool_info = {
            'node_id': row['node_id'],
            'name': row['name'],
            'title': row['title'],
            'description': row['description'],
            'category': row['category'],
            'use_cases': [],
            'limitations': [],
            'combinations': []
        }

        # Get use cases
        cursor.execute("""
            SELECT n.description
            FROM edges e
            JOIN nodes n ON e.target_node_id = n.node_id
            WHERE e.source_node_id = ? AND e.edge_type = 'tool_has_use_case'
            LIMIT 5
        """, (row['node_id'],))
        tool_info['use_cases'] = [r['description'] for r in cursor.fetchall()]

        # Get limitations
        cursor.execute("""
            SELECT n.description
            FROM edges e
            JOIN nodes n ON e.target_node_id = n.node_id
            WHERE e.source_node_id = ? AND e.edge_type = 'tool_has_limitation'
            LIMIT 3
        """, (row['node_id'],))
        tool_info['limitations'] = [r['description'] for r in cursor.fetchall()]

        # Get combinations
        cursor.execute("""
            SELECT n.name, n.metadata
            FROM edges e
            JOIN nodes n ON e.target_node_id = n.node_id
            WHERE e.source_node_id = ? AND e.edge_type = 'tool_has_combination'
            LIMIT 3
        """, (row['node_id'],))
        for r in cursor.fetchall():
            metadata = json.loads(r['metadata']) if r['metadata'] else {}
            tool_info['combinations'].append({
                'with_tool': metadata.get('with_tool', 'Unknown'),
                'pattern': metadata.get('pattern', 'N/A')
            })

        self._cache[cache_key] = tool_info
        return tool_info.copy()

    # Reasoning-layer node types want_to()'s rule-search step covers. Widened
    # 2026-07-14 (found via an organic query batch, not the fixture): the
    # original 2026-07-14 fix only listed 'synthesis_rule' because
    # 'handbook_capability' didn't exist yet -- it was added later the same
    # session (P0.5 Lane B). want_to("cache an expensive operation") and
    # want_to("validate json output") should surface hbcap_prompt_caching /
    # hbcap_json_mode but silently couldn't, because this list went stale
    # relative to the graph the moment Lane B ran. Any future reasoning-layer
    # node type added to the graph should be appended here too.
    REASONING_NODE_TYPES = ('synthesis_rule', 'handbook_capability')

    def _get_rule_info(self, rule_id: str) -> Optional[Dict]:
        """Get reasoning-layer node info (synthesis_rule or handbook_capability
        -- added 2026-07-14, P2 port -- mirrors _get_tool_info's shape so
        callers can treat tool/rule/capability results uniformly)."""
        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(self.REASONING_NODE_TYPES))
        cursor.execute(f"""
            SELECT node_id, name, title, description, category, metadata
            FROM nodes
            WHERE node_type IN ({placeholders}) AND node_id = ?
        """, (*self.REASONING_NODE_TYPES, rule_id))
        row = cursor.fetchone()
        if not row:
            return None
        meta = json.loads(row['metadata']) if row['metadata'] else {}
        return {
            'node_id': row['node_id'],
            'name': row['title'] or row['name'] or row['node_id'],
            'title': row['title'],
            'description': row['description'],
            'category': row['category'],
            'confidence': meta.get('confidence'),
            'use_cases': [], 'limitations': [], 'combinations': [],
        }

    def _search_rule_statements(self, query: str) -> List[Dict]:
        """Search reasoning-layer node descriptions matching query words
        (added 2026-07-14, P2 port; widened 2026-07-14 to cover
        handbook_capability alongside synthesis_rule). Same word-split
        LIKE-match shape as _search_use_cases, just against the reasoning
        layer instead of the tool layer -- that layer didn't exist when
        intent_query.py was written."""
        cursor = self.conn.cursor()
        words = [w for w in query.split() if len(w) > 3]  # skip short stopword-ish tokens
        placeholders = ','.join('?' * len(self.REASONING_NODE_TYPES))

        results = []
        for word in words:
            cursor.execute(f"""
                SELECT node_id, description
                FROM nodes
                WHERE node_type IN ({placeholders}) AND LOWER(description) LIKE ?
            """, (*self.REASONING_NODE_TYPES, f'%{word}%'))
            for row in cursor.fetchall():
                results.append({'rule_id': row['node_id'], 'matched_word': word})

        return results

    def _search_use_cases(self, query: str) -> List[Dict]:
        """Search use cases matching query."""
        cursor = self.conn.cursor()

        # Split query into words for LIKE matching
        words = [w for w in query.split() if len(w) > 2]

        results = []
        for word in words:
            cursor.execute("""
                SELECT t.name as tool_name, uc.description as use_case
                FROM nodes t
                JOIN edges e ON t.node_id = e.source_node_id
                JOIN nodes uc ON e.target_node_id = uc.node_id
                WHERE t.node_type = 'tool'
                  AND e.edge_type = 'tool_has_use_case'
                  AND LOWER(uc.description) LIKE ?
            """, (f'%{word}%',))

            for row in cursor.fetchall():
                results.append({
                    'tool_name': row['tool_name'],
                    'use_case': row['use_case'],
                    'matched_word': word
                })

        return results

    def _resolve_node_id(self, node_ref: str) -> Optional[str]:
        """Resolve node name or ID to node_id."""
        cursor = self.conn.cursor()

        # Try direct ID match
        cursor.execute("SELECT node_id FROM nodes WHERE node_id = ?", (node_ref,))
        if cursor.fetchone():
            return node_ref

        # Try name match (case-insensitive)
        cursor.execute("SELECT node_id FROM nodes WHERE LOWER(name) = LOWER(?)", (node_ref,))
        row = cursor.fetchone()
        if row:
            return row['node_id']

        # Try partial name match
        cursor.execute("SELECT node_id FROM nodes WHERE LOWER(name) LIKE LOWER(?)", (f'%{node_ref}%',))
        row = cursor.fetchone()
        if row:
            return row['node_id']

        return None

    def _bfs_path(self, start: str, end: str, max_depth: int) -> Optional[List[str]]:
        """BFS to find shortest path between nodes."""
        if start == end:
            return [start]

        cursor = self.conn.cursor()
        visited = {start}
        queue = [(start, [start])]

        while queue and len(queue[0][1]) <= max_depth:
            current, path = queue.pop(0)

            # Get all neighbors (both directions)
            cursor.execute("""
                SELECT target_node_id as neighbor FROM edges WHERE source_node_id = ?
                UNION
                SELECT source_node_id as neighbor FROM edges WHERE target_node_id = ?
            """, (current, current))

            for row in cursor.fetchall():
                neighbor = row['neighbor']
                if neighbor == end:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def _generate_inference(self, path_names: List[Dict], edge_types: List[str]) -> str:
        """Generate natural language inference from path."""
        if not path_names or not edge_types:
            return ""

        parts = []
        for i, (node, edge) in enumerate(zip(path_names[:-1], edge_types)):
            next_node = path_names[i + 1]

            # Make edge types human-readable
            edge_readable = edge.replace('_', ' ')

            parts.append(f"{node['name']} {edge_readable} {next_node['name']}")

        return " → ".join(parts)

    def classify_intent(self, query: str) -> List[str]:
        """Classify query into intent categories."""
        query_lower = query.lower()
        intents = []

        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                intents.append(intent)

        return intents or ['general']

    # =========================================================================
    # PHASE 2: EXTENDED QUERY METHODS (10 new methods)
    # =========================================================================

    def similar_to(self, tool_name: str, k: int = 5) -> List[Dict]:
        """
        Find tools similar to the given tool based on:
        - Shared edge types (tools with similar use_cases)
        - Common combinations (tools often used together)
        - Category overlap

        Uses Jaccard similarity on connected node sets.
        Insight #35: Jaccard Similarity as Structure Metric
        """
        tool_info = self._get_tool_info(tool_name)
        if not tool_info:
            return [{'error': f'Tool not found: {tool_name}'}]

        tool_connections = self._get_connections(tool_name)

        similarities = []
        for other_tool in self.list_tools():
            if other_tool['name'] != tool_name:
                other_connections = self._get_connections(other_tool['name'])

                # Jaccard similarity
                intersection = len(tool_connections & other_connections)
                union = len(tool_connections | other_connections)
                jaccard = intersection / union if union > 0 else 0

                if jaccard > 0:
                    similarities.append({
                        'tool': other_tool['name'],
                        'category': other_tool['category'],
                        'similarity': round(jaccard, 3),
                        'shared_patterns': list(tool_connections & other_connections)[:3],
                        'description': other_tool['description'][:80] + '...'
                    })

        # Confidence floor added 2026-07-14 (FCL-009, promoted to a real fix after
        # recurring across Task/TodoWrite/AskUserQuestion/BashOutput): tools with mostly
        # unique edge profiles score near-zero against everything (observed noise band
        # 0.067-0.088), but the old code returned a top-k regardless, presenting noise as
        # a ranked answer. Empirically-grounded floor (observed real-signal band starts at
        # 0.143): below it, report honestly via the same 'error' sentinel already used for
        # "tool not found" -- both `main()`'s CLI loop and alternatives() already handle it.
        FLOOR = 0.1
        strong = [s for s in similarities if s['similarity'] >= FLOOR]
        if similarities and not strong:
            top = max(similarities, key=lambda x: x['similarity'])
            return [{'error': f"No strong match for {tool_name} above confidence floor "
                               f"({FLOOR}) -- {len(similarities)} candidate(s) below threshold, "
                               f"strongest was {top['tool']} at {top['similarity']}"}]

        return sorted(strong, key=lambda x: x['similarity'], reverse=True)[:k]

    def _get_connections(self, tool_name: str) -> Set[str]:
        """Get set of connected node names for a tool (for Jaccard similarity)."""
        cursor = self.conn.cursor()
        connections = set()

        # Get outgoing edges
        cursor.execute("""
            SELECT n.name, e.edge_type
            FROM nodes t
            JOIN edges e ON t.node_id = e.source_node_id
            JOIN nodes n ON e.target_node_id = n.node_id
            WHERE LOWER(t.name) = LOWER(?)
        """, (tool_name,))

        for row in cursor.fetchall():
            name = row['name'] if row['name'] else 'unknown'
            edge_type = row['edge_type'] if row['edge_type'] else 'unknown'
            connections.add(f"{edge_type}:{name[:30]}")

        return connections

    def compose_for(self, goal: str, max_tools: int = 3) -> Dict:
        """
        Find multi-tool compositions that achieve complex goals.

        Insight #36: Composition Through Edge Traversal
        Multi-tool workflows emerge from following edges.
        """
        # Decompose goal into sub-goals
        sub_goals = self._decompose_goal(goal)

        # Find tools for each sub-goal
        tool_sequence = []
        for sub_goal in sub_goals:
            matches = self.want_to(sub_goal, k=1)
            if matches:
                tool_sequence.append({
                    'sub_goal': sub_goal,
                    'tool': matches[0]['name'],
                    'score': matches[0].get('score', 0)
                })

        # Validate composition via edges
        composition = self._validate_composition([t['tool'] for t in tool_sequence])

        # Generate workflow description
        workflow = self._generate_workflow(tool_sequence)

        return {
            'goal': goal,
            'decomposition': sub_goals,
            'tools': tool_sequence[:max_tools],
            'workflow': workflow,
            'compatible': composition['valid'],
            'compatibility_notes': composition.get('notes', [])
        }

    def _decompose_goal(self, goal: str) -> List[str]:
        """Decompose a complex goal into sub-goals."""
        goal_lower = goal.lower()

        # Pattern-based decomposition
        sub_goals = []

        # Check for compound goals
        compound_patterns = {
            'refactor': ['find', 'read', 'edit'],
            'migrate': ['find', 'read', 'edit', 'test'],
            'debug': ['read', 'search', 'fix'],
            'bug': ['search', 'read', 'fix'],  # added 2026-07-14, closes FCL-003: "fix a bug
                                                # found via search" has no substring match against
                                                # any prior key ('debug' isn't literally in that
                                                # phrase); search-first ordering matches the
                                                # canonical query's own "found via search" wording
            'implement': ['read', 'create', 'write'],
            'test': ['read', 'run'],
            'deploy': ['build', 'run'],
            'understand': ['find', 'read'],
            'document': ['read', 'write'],
        }

        # Fixed 2026-07-14 (FCL-007, promoted to a real fix after a 2nd organic-usage
        # occurrence): was "return on the first matching key" -- a goal spanning multiple
        # categories (e.g. "build a new feature, write tests, and deploy it" matches both
        # 'test' and 'deploy') silently collapsed to whichever key happened first in dict
        # order, discarding the rest. Now collects steps from EVERY matching pattern,
        # deduplicated in first-seen order, so a multi-category goal composes instead of
        # collapsing to whichever category matched first.
        matched_steps = []
        seen_steps = set()
        for pattern, steps in compound_patterns.items():
            if pattern in goal_lower:
                for step in steps:
                    if step not in seen_steps:
                        matched_steps.append(step)
                        seen_steps.add(step)
        if matched_steps:
            # Bare step words (not `f"{step} for {goal}"`) -- fixed 2026-07-14 as part of
            # closing FCL-003: re-embedding the full goal text let one category's keyword
            # (e.g. "fix") bleed into every other sub-goal's want_to() resolution.
            return matched_steps

        # If no compound pattern, return original goal
        return [goal]

    def _validate_composition(self, tools: List[str]) -> Dict:
        """Check if tools can work together."""
        cursor = self.conn.cursor()
        notes = []
        valid = True

        for i, tool in enumerate(tools):
            if i == 0:
                continue

            prev_tool = tools[i-1]

            # Check for combination edge
            cursor.execute("""
                SELECT 1 FROM nodes t1
                JOIN edges e ON t1.node_id = e.source_node_id
                JOIN nodes c ON e.target_node_id = c.node_id
                WHERE LOWER(t1.name) = LOWER(?)
                  AND e.edge_type = 'tool_has_combination'
                  AND c.metadata LIKE ?
            """, (prev_tool, f'%{tool}%'))

            if cursor.fetchone():
                notes.append(f"{prev_tool} + {tool}: documented combination")
            else:
                notes.append(f"{prev_tool} → {tool}: inferred sequence")

        return {'valid': valid, 'notes': notes}

    def _generate_workflow(self, tool_sequence: List[Dict]) -> str:
        """Generate human-readable workflow from tool sequence."""
        if not tool_sequence:
            return "No workflow generated"

        steps = []
        for i, item in enumerate(tool_sequence, 1):
            steps.append(f"{i}. {item['tool']}: {item['sub_goal']}")

        return "\n".join(steps)

    def alternatives(self, tool_name: str, goal: str = None) -> List[Dict]:
        """
        Find alternative tools/approaches for a given tool or goal.

        If goal provided: find other tools that achieve same goal
        If only tool: find tools with similar capabilities
        """
        alternatives = []

        if goal:
            # Find all tools that could achieve this goal
            all_matches = self.want_to(goal, k=10)
            alternatives = [m for m in all_matches if m['name'] != tool_name]
        else:
            # Use similar_to for capability-based alternatives
            similar = self.similar_to(tool_name, k=5)
            for s in similar:
                if 'error' not in s:
                    alternatives.append({
                        'name': s['tool'],
                        'category': s.get('category', 'unknown'),
                        'similarity': s.get('similarity', 0),
                        'description': s.get('description', '')
                    })

        return alternatives

    def optimize_for(self, goal: str, criteria: str = 'speed') -> Dict:
        """
        Recommend tools optimized for specific criteria.

        Criteria: speed, cost, safety, accuracy
        """
        OPTIMIZATION_CRITERIA = {
            'speed': {
                'prefer': ['Glob', 'Grep', 'Read'],
                'avoid': ['Task', 'WebSearch'],
                'tips': ['Use specific patterns', 'Limit search scope', 'Avoid agents for simple tasks']
            },
            'cost': {
                'prefer': ['Read', 'Edit', 'Glob', 'Grep', 'Bash'],
                'avoid': ['WebSearch', 'WebFetch', 'Task'],
                'tips': ['Batch operations', 'Cache results', 'Use local tools']
            },
            'safety': {
                'prefer': ['Read', 'Glob', 'Grep'],
                'avoid': ['Bash', 'Write', 'Edit'],
                'tips': ['Preview before write', 'Use read-only first', 'Validate inputs']
            },
            'accuracy': {
                'prefer': ['Grep', 'Read'],
                'avoid': [],
                'tips': ['Use regex for precision', 'Verify with Read', 'Cross-reference results']
            }
        }

        base_tools = self.want_to(goal, k=10)
        optimization = OPTIMIZATION_CRITERIA.get(criteria, OPTIMIZATION_CRITERIA['speed'])

        scored = []
        for tool in base_tools:
            score = tool.get('score', 0.5)
            if tool['name'] in optimization.get('prefer', []):
                score *= 1.5
            if tool['name'] in optimization.get('avoid', []):
                score *= 0.5
            scored.append({**tool, 'optimized_score': round(score, 3)})

        return {
            'goal': goal,
            'criteria': criteria,
            'recommendations': sorted(scored, key=lambda x: x['optimized_score'], reverse=True)[:5],
            'tips': optimization.get('tips', [])
        }

    def learn(self, topic: str) -> Dict:
        """
        Get learning resources for a topic.

        Returns related tools, examples, and suggested progression.
        """
        # Find relevant tools
        tools = self.want_to(topic, k=5)

        # Get examples for each tool
        examples = []
        cursor = self.conn.cursor()

        for tool in tools[:3]:
            cursor.execute("""
                SELECT e.title, e.description
                FROM nodes t
                JOIN edges ed ON t.node_id = ed.source_node_id
                JOIN nodes e ON ed.target_node_id = e.node_id
                WHERE LOWER(t.name) = LOWER(?)
                  AND ed.edge_type = 'tool_has_example'
                LIMIT 2
            """, (tool['name'],))

            for row in cursor.fetchall():
                examples.append({
                    'tool': tool['name'],
                    'title': row['title'] or 'Example',
                    'description': row['description'][:100] if row['description'] else ''
                })

        # Build learning path
        path = self._build_learning_path(tools)

        return {
            'topic': topic,
            'tools': [{'name': t['name'], 'category': t.get('category', '')} for t in tools],
            'examples': examples[:5],
            'learning_path': path,
            'prerequisites': self._get_prerequisites(tools)
        }

    def _build_learning_path(self, tools: List[Dict]) -> List[str]:
        """Build progressive learning path from tools."""
        # Order by complexity (file ops → search → execution → meta)
        complexity_order = {
            'file_operations': 1,
            'search_navigation': 2,
            'execution': 3,
            'web': 4,
            'meta': 5
        }

        sorted_tools = sorted(tools,
            key=lambda t: complexity_order.get(t.get('category', ''), 3))

        return [f"Learn {t['name']}: {t.get('description', '')[:40]}..." for t in sorted_tools[:4]]

    def _get_prerequisites(self, tools: List[Dict]) -> List[str]:
        """Get prerequisites for a set of tools."""
        prerequisites = set()
        cursor = self.conn.cursor()

        for tool in tools:
            cursor.execute("""
                SELECT p.description
                FROM nodes t
                JOIN edges e ON t.node_id = e.source_node_id
                JOIN nodes p ON e.target_node_id = p.node_id
                WHERE LOWER(t.name) = LOWER(?)
                  AND e.edge_type = 'tool_has_prerequisite'
            """, (tool['name'],))

            for row in cursor.fetchall():
                if row['description']:
                    prerequisites.add(row['description'][:60])

        return list(prerequisites)[:5]

    def recommend(self, context: str) -> Dict:
        """
        AI-style recommendations based on current context.

        Combines intent classification, goal decomposition, and optimization.
        """
        # Classify what user is trying to do
        intents = self.classify_intent(context)

        # Get tools for each intent
        tools_by_intent = {}
        for intent in intents:
            matches = self.want_to(intent, k=3)
            if matches:
                tools_by_intent[intent] = matches

        # Generate recommendations
        recommendations = []
        for intent, tools in tools_by_intent.items():
            if tools:
                recommendations.append({
                    'intent': intent,
                    'recommended_tool': tools[0]['name'],
                    'confidence': tools[0].get('score', 0.5),
                    'reason': f"Best match for '{intent}' intent"
                })

        # Workflow suggestion for complex contexts
        workflow_suggestion = None
        if len(intents) > 1:
            workflow_suggestion = self.compose_for(context)

        return {
            'context': context,
            'detected_intents': intents,
            'recommendations': recommendations,
            'workflow_suggestion': workflow_suggestion
        }

    def compatible_with(self, tool_name: str) -> Dict:
        """
        Find tools compatible with the given tool.

        Uses tool_has_combination and tool_requires_tool edges.
        """
        cursor = self.conn.cursor()

        # Get combinations
        cursor.execute("""
            SELECT n.metadata
            FROM nodes t
            JOIN edges e ON t.node_id = e.source_node_id
            JOIN nodes n ON e.target_node_id = n.node_id
            WHERE LOWER(t.name) = LOWER(?)
              AND e.edge_type = 'tool_has_combination'
        """, (tool_name,))

        combinations = []
        for row in cursor.fetchall():
            meta = json.loads(row['metadata']) if row['metadata'] else {}
            if meta.get('with_tool'):
                combinations.append({
                    'tool': meta.get('with_tool'),
                    'pattern': meta.get('pattern', 'N/A'),
                    'rationale': meta.get('rationale', '')[:60]
                })

        # Get requirements (what this tool requires)
        cursor.execute("""
            SELECT n.name
            FROM nodes t
            JOIN edges e ON t.node_id = e.source_node_id
            JOIN nodes n ON e.target_node_id = n.node_id
            WHERE LOWER(t.name) = LOWER(?)
              AND e.edge_type = 'tool_requires_tool'
        """, (tool_name,))

        requires = [row['name'] for row in cursor.fetchall()]

        # Get what requires this tool
        cursor.execute("""
            SELECT n.name
            FROM nodes t
            JOIN edges e ON t.node_id = e.target_node_id
            JOIN nodes n ON e.source_node_id = n.node_id
            WHERE LOWER(t.name) = LOWER(?)
              AND e.edge_type = 'tool_requires_tool'
        """, (tool_name,))

        required_by = [row['name'] for row in cursor.fetchall()]

        return {
            'tool': tool_name,
            'compatible_tools': combinations,
            'requires': requires,
            'required_by': required_by
        }

    def debug_tool(self, tool_name: str, issue: str = None) -> Dict:
        """
        Troubleshooting help for tool issues.

        Insight #37: Debug as Limitation + Workaround Search
        """
        tool_info = self._get_tool_info(tool_name)
        if not tool_info:
            return {'error': f'Tool not found: {tool_name}'}

        result = {
            'tool': tool_name,
            'limitations': tool_info.get('limitations', []),
            'workarounds': []
        }

        # Get workarounds for each limitation
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.description as limitation, w.description as workaround
            FROM nodes t
            JOIN edges e1 ON t.node_id = e1.source_node_id
            JOIN nodes l ON e1.target_node_id = l.node_id
            LEFT JOIN edges e2 ON l.node_id = e2.source_node_id AND e2.edge_type = 'has_workaround'
            LEFT JOIN nodes w ON e2.target_node_id = w.node_id
            WHERE LOWER(t.name) = LOWER(?)
              AND e1.edge_type = 'tool_has_limitation'
        """, (tool_name,))

        for row in cursor.fetchall():
            if row['workaround']:
                result['workarounds'].append({
                    'issue': row['limitation'][:60],
                    'solution': row['workaround']
                })

        # Filter by specific issue if provided
        if issue:
            issue_lower = issue.lower()
            relevant = [l for l in result['limitations'] if issue_lower in l.lower()]
            relevant_workarounds = [w for w in result['workarounds']
                                    if issue_lower in w['issue'].lower()]

            result['relevant_limitations'] = relevant
            result['relevant_workarounds'] = relevant_workarounds

        return result

    def explore_smart(self, start_node: str, depth: int = 2) -> Dict:
        """
        Intelligent BFS exploration with importance ranking.

        Insight #38: Smart Exploration = Hub Detection
        Importance = connection_count / depth
        """
        cursor = self.conn.cursor()

        # Get start node
        start_id = self._resolve_node_id(start_node)
        if not start_id:
            return {'error': f'Node not found: {start_node}'}

        visited = {start_id: {'depth': 0, 'connections': 0}}
        queue = [(start_id, 0)]

        while queue:
            current, current_depth = queue.pop(0)
            if current_depth >= depth:
                continue

            # Get all connections
            cursor.execute("""
                SELECT target_node_id as neighbor, edge_type FROM edges WHERE source_node_id = ?
                UNION
                SELECT source_node_id as neighbor, edge_type FROM edges WHERE target_node_id = ?
            """, (current, current))

            connection_count = 0
            for row in cursor.fetchall():
                neighbor = row['neighbor']
                connection_count += 1

                if neighbor not in visited:
                    visited[neighbor] = {
                        'depth': current_depth + 1,
                        'connections': 0,
                        'via_edge': row['edge_type']
                    }
                    queue.append((neighbor, current_depth + 1))

            visited[current]['connections'] = connection_count

        # Convert to readable format and rank
        exploration = []
        for node_id, info in visited.items():
            cursor.execute("SELECT name, node_type, description FROM nodes WHERE node_id = ?", (node_id,))
            row = cursor.fetchone()
            if row:
                importance = info['connections'] / (info['depth'] + 1)
                exploration.append({
                    'name': row['name'],
                    'type': row['node_type'],
                    'description': row['description'][:80] if row['description'] else '',
                    'depth': info['depth'],
                    'connections': info['connections'],
                    'importance_score': round(importance, 2)
                })

        exploration.sort(key=lambda x: x['importance_score'], reverse=True)

        # Identify hubs (high connection count)
        hub_nodes = [e for e in exploration if e['connections'] >= 3]

        return {
            'start': start_node,
            'depth': depth,
            'total_nodes': len(exploration),
            'exploration': exploration[:20],
            'hub_nodes': hub_nodes[:5]
        }

    def roadmap(self, goal: str) -> Dict:
        """
        Generate structured learning roadmap for a complex goal.

        Builds dependency-ordered progression.
        """
        # Get all relevant tools
        tools = self.want_to(goal, k=10)

        # Build dependency graph
        tool_deps = {}
        for tool in tools:
            compatible = self.compatible_with(tool['name'])
            tool_deps[tool['name']] = compatible.get('requires', [])

        # Topological sort for learning order
        ordered = self._topological_sort(tool_deps)

        # Build roadmap
        roadmap_steps = []
        for i, tool_name in enumerate(ordered):
            tool_info = self._get_tool_info(tool_name)
            if tool_info:
                roadmap_steps.append({
                    'step': i + 1,
                    'tool': tool_name,
                    'description': tool_info['description'][:80] + '...',
                    'prerequisites': tool_deps.get(tool_name, []),
                    'examples_count': len(tool_info.get('use_cases', []))
                })

        # Determine learning curve
        curve = 'beginner' if len(roadmap_steps) <= 3 else \
                'intermediate' if len(roadmap_steps) <= 6 else 'advanced'

        return {
            'goal': goal,
            'total_steps': len(roadmap_steps),
            'roadmap': roadmap_steps,
            'learning_curve': curve
        }

    def _topological_sort(self, deps: Dict[str, List[str]]) -> List[str]:
        """Topological sort of tools based on dependencies."""
        in_degree = defaultdict(int)
        for tool in deps:
            in_degree[tool] = 0

        for tool, requirements in deps.items():
            for req in requirements:
                if req in deps:
                    in_degree[tool] += 1

        queue = [t for t in deps if in_degree[t] == 0]
        result = []

        while queue:
            tool = queue.pop(0)
            result.append(tool)

            for other, requirements in deps.items():
                if tool in requirements:
                    in_degree[other] -= 1
                    if in_degree[other] == 0 and other not in result:
                        queue.append(other)

        # Add any remaining (circular deps)
        for tool in deps:
            if tool not in result:
                result.append(tool)

        return result

    # =========================================================================
    # BACKWARDS COMPATIBILITY METHODS
    # =========================================================================

    def what_tool_for(self, goal: str) -> Optional[Dict]:
        """
        Original Pre-Day 2 method - now calls want_to() internally.
        Kept for backwards compatibility.
        """
        results = self.want_to(goal, k=1)
        return results[0] if results else None

    def why_not(self, tool_name: str, goal: str) -> Dict:
        """
        "Why can't I use X for Y?" -> limitations + workarounds.
        """
        tool_info = self._get_tool_info(tool_name)
        if not tool_info:
            return {'error': f"Tool not found: {tool_name}"}

        result = {
            'tool': tool_name,
            'goal': goal,
            'limitations': tool_info.get('limitations', []),
            'workarounds': []
        }

        # Get workarounds for this tool's limitations
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.node_id, l.description as limitation, w.description as workaround
            FROM nodes t
            JOIN edges e1 ON t.node_id = e1.source_node_id
            JOIN nodes l ON e1.target_node_id = l.node_id
            LEFT JOIN edges e2 ON l.node_id = e2.source_node_id AND e2.edge_type = 'has_workaround'
            LEFT JOIN nodes w ON e2.target_node_id = w.node_id
            WHERE t.node_type = 'tool'
              AND LOWER(t.name) = LOWER(?)
              AND e1.edge_type = 'tool_has_limitation'
        """, (tool_name,))

        for row in cursor.fetchall():
            if row['workaround']:
                result['workarounds'].append({
                    'limitation': row['limitation'],
                    'solution': row['workaround']
                })

        return result

    def list_tools(self) -> List[Dict]:
        """List all available tools with basic info."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, title, category, description
            FROM nodes
            WHERE node_type = 'tool'
            ORDER BY name
        """)

        return [dict(row) for row in cursor.fetchall()]


# =============================================================================
# CLI INTERFACE
# =============================================================================

def format_want_to_results(results: List[Dict]) -> str:
    """Format want_to results for CLI output."""
    if not results:
        return "No tools found for that goal."

    lines = [
        "",
        "=" * 60,
        "TOOLS FOR YOUR GOAL",
        "=" * 60,
        ""
    ]

    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['name']} ({r.get('match_type', 'unknown')})")
        lines.append(f"   Score: {r.get('score', 0):.2f}")
        lines.append(f"   {r['description'][:80]}...")

        if r.get('matched_keyword'):
            lines.append(f"   Matched: '{r['matched_keyword']}'")
        elif r.get('matched_keywords'):
            lines.append(f"   Matched: {', '.join(r['matched_keywords'][:3])}")
        elif r.get('matched_use_case'):
            lines.append(f"   Use case: {r['matched_use_case'][:60]}...")

        if r.get('use_cases'):
            lines.append(f"   Top use cases:")
            for uc in r['use_cases'][:2]:
                lines.append(f"     • {uc[:60]}...")

        lines.append("")

    return "\n".join(lines)


def format_can_it_results(result: Dict) -> str:
    """Format can_it results for CLI output."""
    lines = [
        "",
        "=" * 60,
        f"CAN CLAUDE CODE: {result['capability']}",
        "=" * 60,
        "",
        f"Answer: {'YES' if result['can'] else 'NO (with workarounds)' if result['workarounds'] else 'NO'}",
        ""
    ]

    if result['how']:
        lines.append("HOW:")
        for h in result['how'][:5]:
            lines.append(f"  • {h['tool']}: {h['use_case'][:60]}...")
        lines.append("")

    if result['limitations']:
        lines.append("LIMITATIONS:")
        for lim in result['limitations'][:3]:
            lines.append(f"  • [{lim['tool']}] {lim['description'][:60]}...")
        lines.append("")

    if result['workarounds']:
        lines.append("WORKAROUNDS:")
        for w in result['workarounds'][:3]:
            lines.append(f"  • {w['solution'][:70]}...")
        lines.append("")

    if result['related_tools']:
        lines.append(f"Related tools: {', '.join(result['related_tools'][:5])}")
        lines.append("")

    return "\n".join(lines)


def format_trace_results(result: Dict) -> str:
    """Format trace results for CLI output."""
    if not result['found']:
        return f"\nNo path found: {result.get('error', result.get('inference', 'Unknown'))}\n"

    lines = [
        "",
        "=" * 60,
        f"PATH: {result['from']} → {result['to']}",
        "=" * 60,
        "",
        f"Length: {result['path_length']} hop(s)",
        "",
        "Path:"
    ]

    for i, node in enumerate(result['path']):
        lines.append(f"  {i+1}. {node['name']} ({node['type']})")
        if i < len(result['edge_types']):
            lines.append(f"       ↓ {result['edge_types'][i]}")

    lines.append("")
    lines.append("Inference:")
    lines.append(f"  {result['inference']}")
    lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NLKE Intent-Driven Query Interface for Claude Code Tools KG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --want-to "read a file"
  %(prog)s --can-it "edit binary files"
  %(prog)s --trace Read Edit
  %(prog)s --similar-to Read
  %(prog)s --compose-for "refactor Python files"
  %(prog)s --optimize-for "search code" --criteria speed
  %(prog)s --learn "file manipulation"
  %(prog)s --roadmap "master CLI tools"
  %(prog)s --list

NLKE Query Patterns (Phase 1):
  --want-to      "I want to X" → find tools that achieve the goal
  --can-it       "Can Claude Code do X?" → yes/no + how + limitations
  --trace        Find path between two nodes (transitive inference)
  --why-not      "Why can't I use X for Y?" → limitations + workarounds

Extended Query Patterns (Phase 2):
  --similar-to     Find tools similar to TOOL (Jaccard similarity)
  --compose-for    Find multi-tool workflow for complex GOAL
  --alternatives   Find alternative tools/approaches
  --optimize-for   Optimize tool selection with --criteria
  --learn          Get learning resources for TOPIC
  --recommend      AI-style recommendations for CONTEXT
  --compatible-with Find tools compatible with TOOL
  --debug          Troubleshooting help for TOOL
  --explore-smart  Intelligent graph exploration from NODE
  --roadmap        Learning roadmap for GOAL
        """
    )

    # Phase 1 flags
    parser.add_argument('--want-to', metavar='GOAL',
                       help='Find tools for a goal: "I want to X"')
    parser.add_argument('--can-it', metavar='CAPABILITY',
                       help='Check if Claude Code can do something')
    parser.add_argument('--trace', nargs=2, metavar=('FROM', 'TO'),
                       help='Find path between two nodes')
    parser.add_argument('--why-not', nargs=2, metavar=('TOOL', 'GOAL'),
                       help='Why can\'t I use TOOL for GOAL')
    parser.add_argument('--list', action='store_true',
                       help='List all available tools')
    parser.add_argument('--k', type=int, default=5,
                       help='Number of results to return (default: 5)')

    # Phase 2 flags
    parser.add_argument('--similar-to', metavar='TOOL',
                       help='Find tools similar to TOOL')
    parser.add_argument('--compose-for', metavar='GOAL',
                       help='Find multi-tool composition for GOAL')
    parser.add_argument('--alternatives', metavar='TOOL',
                       help='Find alternative tools/approaches')
    parser.add_argument('--alt-goal', metavar='GOAL',
                       help='Goal for --alternatives (optional)')
    parser.add_argument('--optimize-for', metavar='GOAL',
                       help='Optimize tool selection for GOAL')
    parser.add_argument('--criteria', metavar='CRITERIA', default='speed',
                       help='Optimization criteria: speed|cost|safety|accuracy')
    parser.add_argument('--learn', metavar='TOPIC',
                       help='Get learning resources for TOPIC')
    parser.add_argument('--recommend', metavar='CONTEXT',
                       help='Get smart recommendations for CONTEXT')
    parser.add_argument('--compatible-with', metavar='TOOL',
                       help='Find tools compatible with TOOL')
    parser.add_argument('--debug', metavar='TOOL',
                       help='Troubleshooting help for TOOL')
    parser.add_argument('--issue', metavar='ISSUE',
                       help='Specific issue for --debug')
    parser.add_argument('--explore-smart', metavar='NODE',
                       help='Intelligent graph exploration from NODE')
    parser.add_argument('--depth', type=int, default=2,
                       help='Exploration depth for --explore-smart')
    parser.add_argument('--roadmap', metavar='GOAL',
                       help='Learning roadmap for GOAL')
    parser.add_argument('--db', metavar='PATH', default=None,
                       help=f'KG database path (default: {DB_PATH})')
    parser.add_argument('--json', action='store_true',
                       help='Machine-readable JSON output (all query types, not just --why-not)')

    args = parser.parse_args()

    # Check for any argument
    has_arg = any([
        args.want_to, args.can_it, args.trace, args.why_not, args.list,
        args.similar_to, args.compose_for, args.alternatives, args.optimize_for,
        args.learn, args.recommend, args.compatible_with, args.debug,
        args.explore_smart, args.roadmap
    ])

    if not has_arg:
        parser.print_help()
        return

    try:
        iq = IntentDrivenQuery(db_path=Path(args.db) if args.db else None)

        # Phase 1 flags
        if args.want_to:
            results = iq.want_to(args.want_to, k=args.k)
            print(json.dumps(results, indent=2) if args.json else format_want_to_results(results))

        if args.can_it:
            result = iq.can_it(args.can_it)
            print(json.dumps(result, indent=2) if args.json else format_can_it_results(result))

        if args.trace:
            result = iq.trace(args.trace[0], args.trace[1])
            print(json.dumps(result, indent=2) if args.json else format_trace_results(result))

        if args.why_not:
            result = iq.why_not(args.why_not[0], args.why_not[1])
            print(json.dumps(result, indent=2))

        if args.list:
            tools = iq.list_tools()
            if args.json:
                print(json.dumps(tools, indent=2))
            else:
                print("\n" + "=" * 60)
                print(f"AVAILABLE TOOLS ({len(tools)} total)")
                print("=" * 60 + "\n")
                for t in tools:
                    print(f"  {t['name']:15} ({t['category']})")
                    print(f"    {t['description'][:60]}...")
                    print()

        # Phase 2 flags
        if args.similar_to:
            results = iq.similar_to(args.similar_to, k=args.k)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print("\n" + "=" * 60)
                print(f"TOOLS SIMILAR TO: {args.similar_to}")
                print("=" * 60 + "\n")
                for r in results:
                    if 'error' in r:
                        print(f"Error: {r['error']}")
                    else:
                        print(f"  {r['tool']:15} (similarity: {r['similarity']:.3f})")
                        print(f"    Category: {r['category']}")
                        if r.get('shared_patterns'):
                            print(f"    Shared: {', '.join(r['shared_patterns'][:2])}")
                        print()

        if args.compose_for:
            result = iq.compose_for(args.compose_for)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("\n" + "=" * 60)
                print(f"WORKFLOW FOR: {result['goal']}")
                print("=" * 60 + "\n")
                print("Decomposition:")
                for sub in result['decomposition']:
                    print(f"  • {sub}")
                print("\nWorkflow:")
                print(result['workflow'])
                print(f"\nCompatible: {result['compatible']}")
                if result.get('compatibility_notes'):
                    for note in result['compatibility_notes']:
                        print(f"  • {note}")

        if args.alternatives:
            results = iq.alternatives(args.alternatives, args.alt_goal)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print("\n" + "=" * 60)
                print(f"ALTERNATIVES TO: {args.alternatives}")
                print("=" * 60 + "\n")
                for r in results[:5]:
                    name = r.get('name', r.get('tool', 'Unknown'))
                    print(f"  {name}")
                    if r.get('similarity'):
                        print(f"    Similarity: {r['similarity']:.3f}")
                    if r.get('description'):
                        print(f"    {r['description'][:60]}...")
                    print()

        if args.optimize_for:
            result = iq.optimize_for(args.optimize_for, args.criteria)
            print("\n" + "=" * 60)
            print(f"OPTIMIZED FOR: {result['goal']} (criteria: {result['criteria']})")
            print("=" * 60 + "\n")
            print("Recommendations:")
            for r in result['recommendations']:
                print(f"  {r['name']:15} (score: {r['optimized_score']:.3f})")
            print("\nTips:")
            for tip in result['tips']:
                print(f"  • {tip}")

        if args.learn:
            result = iq.learn(args.learn)
            print("\n" + "=" * 60)
            print(f"LEARNING: {result['topic']}")
            print("=" * 60 + "\n")
            print("Relevant Tools:")
            for t in result['tools']:
                print(f"  • {t['name']} ({t['category']})")
            if result.get('examples'):
                print("\nExamples:")
                for ex in result['examples'][:3]:
                    print(f"  [{ex['tool']}] {ex['title']}")
            if result.get('learning_path'):
                print("\nLearning Path:")
                for step in result['learning_path']:
                    print(f"  → {step}")

        if args.recommend:
            result = iq.recommend(args.recommend)
            print("\n" + "=" * 60)
            print(f"RECOMMENDATIONS FOR: {result['context'][:40]}...")
            print("=" * 60 + "\n")
            print(f"Detected Intents: {', '.join(result['detected_intents'])}")
            print("\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  {rec['recommended_tool']:15} ({rec['intent']})")
                print(f"    Confidence: {rec['confidence']:.2f}")

        if args.compatible_with:
            result = iq.compatible_with(args.compatible_with)
            print("\n" + "=" * 60)
            print(f"COMPATIBLE WITH: {result['tool']}")
            print("=" * 60 + "\n")
            if result.get('compatible_tools'):
                print("Works well with:")
                for c in result['compatible_tools']:
                    print(f"  • {c['tool']}: {c['pattern']}")
            if result.get('requires'):
                print(f"\nRequires: {', '.join(result['requires'])}")
            if result.get('required_by'):
                print(f"Required by: {', '.join(result['required_by'])}")

        if args.debug:
            result = iq.debug_tool(args.debug, args.issue)
            print("\n" + "=" * 60)
            print(f"DEBUG: {result.get('tool', args.debug)}")
            print("=" * 60 + "\n")
            if result.get('error'):
                print(f"Error: {result['error']}")
            else:
                print("Limitations:")
                for lim in result.get('limitations', [])[:5]:
                    print(f"  • {lim[:70]}...")
                if result.get('workarounds'):
                    print("\nWorkarounds:")
                    for w in result['workarounds'][:3]:
                        print(f"  Issue: {w['issue']}")
                        print(f"  Fix: {w['solution']}")
                        print()

        if args.explore_smart:
            result = iq.explore_smart(args.explore_smart, args.depth)
            print("\n" + "=" * 60)
            print(f"EXPLORATION FROM: {result.get('start', args.explore_smart)}")
            print("=" * 60 + "\n")
            if result.get('error'):
                print(f"Error: {result['error']}")
            else:
                print(f"Total nodes: {result['total_nodes']}, Depth: {result['depth']}")
                print("\nTop by Importance:")
                for e in result.get('exploration', [])[:10]:
                    print(f"  {e['name']:20} ({e['type']}) - score: {e['importance_score']}")
                if result.get('hub_nodes'):
                    print("\nHub Nodes (high connectivity):")
                    for h in result['hub_nodes']:
                        print(f"  • {h['name']} ({h['connections']} connections)")

        if args.roadmap:
            result = iq.roadmap(args.roadmap)
            print("\n" + "=" * 60)
            print(f"ROADMAP: {result['goal']}")
            print("=" * 60 + "\n")
            print(f"Learning Curve: {result['learning_curve']}")
            print(f"Total Steps: {result['total_steps']}\n")
            for step in result['roadmap']:
                print(f"Step {step['step']}: {step['tool']}")
                print(f"  {step['description']}")
                if step.get('prerequisites'):
                    print(f"  Requires: {', '.join(step['prerequisites'])}")
                print()

        iq.close()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run create_claude_code_kg.py first to create the database.")


if __name__ == "__main__":
    main()
