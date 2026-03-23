"""
Causal Knowledge Graph — Simulates the SAP HANA Cloud Knowledge Graph Engine.
Stores error-cause-fix relationships as directed edges in a NetworkX DiGraph
to enable causal reasoning and downstream impact verification.
"""

import networkx as nx
import json


class CausalKnowledgeGraph:
    """
    A directed graph representing causal relationships in the SAP landscape.
    Nodes = entities/errors/states, Edges = causal links with metadata.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_default_graph()

    def _build_default_graph(self):
        """Pre-populate the graph with known SAP causal chains."""

        # ── Material-related causal chain ──────────────────────────
        self.graph.add_edge(
            "Material not in MDG",
            "MATMAS IDoc failure",
            relation="causes",
            description="Missing material master in MDG hub prevents IDoc replication.",
        )
        self.graph.add_edge(
            "MATMAS IDoc failure",
            "PO creation failure",
            relation="causes",
            description="Without material master, purchase orders cannot reference the material.",
        )
        self.graph.add_edge(
            "Material not in MDG",
            "MDG replication timeout",
            relation="causes",
            description="Replication attempts for non-existent material cause repeated timeouts.",
        )

        # ── Vendor-related causal chain ────────────────────────────
        self.graph.add_edge(
            "Vendor not in MDG",
            "ORDERS05 IDoc failure",
            relation="causes",
            description="Missing vendor master prevents purchase order IDoc processing.",
        )
        self.graph.add_edge(
            "ORDERS05 IDoc failure",
            "PO creation failure",
            relation="causes",
            description="IDoc failure blocks downstream PO document posting.",
        )

        # ── Configuration-related causal chain ─────────────────────
        self.graph.add_edge(
            "Plant-POrg assignment missing",
            "BAPI_PO_CREATE1 error",
            relation="causes",
            description="Plant not assigned to purchasing org blocks BAPI PO creation.",
        )
        self.graph.add_edge(
            "BAPI_PO_CREATE1 error",
            "PO creation failure",
            relation="causes",
            description="BAPI error prevents purchase order from being created.",
        )

        # ── UoM-related causal chain ───────────────────────────────
        self.graph.add_edge(
            "Unit of measure missing",
            "MATMAS IDoc incomplete",
            relation="causes",
            description="Missing UoM in T006 table prevents complete IDoc processing.",
        )

        # ── Duplicate key chain ────────────────────────────────────
        self.graph.add_edge(
            "Duplicate PO key in EKKO",
            "ABAP DBSQL_SQL_ERROR dump",
            relation="causes",
            description="Duplicate key in EKKO table causes SQL error short dump.",
        )

        # ── Fix relationships (what resolves what) ─────────────────
        fixes = {
            "Create material in MDG": ["Material not in MDG"],
            "Create vendor in MDG": ["Vendor not in MDG"],
            "Assign plant to purchasing org": ["Plant-POrg assignment missing"],
            "Add unit of measure to T006": ["Unit of measure missing"],
            "Delete duplicate PO entry in EKKO": ["Duplicate PO key in EKKO"],
        }
        for fix, causes in fixes.items():
            for cause in causes:
                self.graph.add_edge(
                    fix,
                    cause,
                    relation="resolves",
                    description=f"Applying '{fix}' resolves the root cause '{cause}'.",
                )

    # ── Query methods ──────────────────────────────────────────────

    def get_root_cause(self, error_node: str) -> list[str]:
        """Trace back to all root causes of a given error node."""
        root_causes = []
        for predecessor in self.graph.predecessors(error_node):
            edge_data = self.graph.get_edge_data(predecessor, error_node)
            if edge_data and edge_data.get("relation") == "causes":
                # Check if this predecessor has its own causes
                upstream = self.get_root_cause(predecessor)
                if upstream:
                    root_causes.extend(upstream)
                else:
                    root_causes.append(predecessor)
        return root_causes if root_causes else [error_node]

    def get_downstream_impact(self, node: str) -> list[dict]:
        """Find all downstream effects of a given node."""
        impacts = []
        for successor in self.graph.successors(node):
            edge_data = self.graph.get_edge_data(node, successor)
            if edge_data and edge_data.get("relation") == "causes":
                impacts.append({
                    "affected": successor,
                    "description": edge_data.get("description", ""),
                })
                impacts.extend(self.get_downstream_impact(successor))
        return impacts

    def get_fix_for_cause(self, cause_node: str) -> str | None:
        """Find the fix that resolves a given root cause."""
        for predecessor in self.graph.predecessors(cause_node):
            edge_data = self.graph.get_edge_data(predecessor, cause_node)
            if edge_data and edge_data.get("relation") == "resolves":
                return predecessor
        return None

    def get_graph_data(self) -> dict:
        """Export graph as JSON-serializable dict for visualization."""
        nodes = list(self.graph.nodes)
        edges = [
            {
                "source": u,
                "target": v,
                "relation": d.get("relation", "unknown"),
                "description": d.get("description", ""),
            }
            for u, v, d in self.graph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    def query_causal_chain(self, error_description: str) -> dict:
        """
        Given an error description, find the best matching node,
        trace its root cause, downstream impact, and recommended fix.
        """
        # Simple fuzzy matching: find the node whose name best matches
        best_node = None
        best_score = 0
        error_lower = error_description.lower()

        for node in self.graph.nodes:
            node_lower = node.lower()
            # Count common words
            node_words = set(node_lower.split())
            error_words = set(error_lower.split())
            score = len(node_words & error_words)
            if score > best_score:
                best_score = score
                best_node = node

        if not best_node or best_score == 0:
            return {
                "matched_node": None,
                "root_causes": [],
                "downstream_impact": [],
                "recommended_fix": None,
                "message": "No matching node found in the causal knowledge graph.",
            }

        root_causes = self.get_root_cause(best_node)
        downstream = self.get_downstream_impact(best_node)
        fix = None
        for rc in root_causes:
            fix = self.get_fix_for_cause(rc)
            if fix:
                break

        return {
            "matched_node": best_node,
            "root_causes": root_causes,
            "downstream_impact": downstream,
            "recommended_fix": fix,
            "message": f"Causal analysis complete for '{best_node}'.",
        }


# Singleton instance
causal_kg = CausalKnowledgeGraph()
