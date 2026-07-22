MATCHER = {
    "mint_id": "mint_t_test", "provenance": ["FIX-003", "FIX-005"], "confidence": 0.75,
    "statement": "A spindle with no tunes edge inherits its sibling's dye-bath tuning.",
    "signature_sql": "SELECT s.strand_id FROM strands s WHERE s.strand_kind='spindle' AND NOT EXISTS (SELECT 1 FROM ties t WHERE t.tie_from = s.strand_id AND t.tie_kind='tunes')",
    "confirm": [{"kind": "sql_exists", "sql": "SELECT 1 FROM ties WHERE tie_kind='tunes' LIMIT 1"}],
    "fix": {"edge_kind": "tunes",
            "pairs_sql": "SELECT s.strand_id, 'dye_bath_2' FROM strands s WHERE s.strand_kind='spindle' AND NOT EXISTS (SELECT 1 FROM ties t WHERE t.tie_from=s.strand_id AND t.tie_kind='tunes')",
            "properties_template": {"rationale": "sibling tuning anchor"}},
}
