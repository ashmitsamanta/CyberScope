import abc
import networkx as nx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.entity import Entity
from app.models.relationship import Relationship
from app.models.transaction import Transaction
from app.models.case import Case
from app.analyzers.graph_analyzer import GraphAnalyzer


class IGraphService(abc.ABC):
    """Abstract interface for graph storage and analytics engine."""

    @abc.abstractmethod
    def sync_from_db(self, db: Session) -> None:
        pass

    @abc.abstractmethod
    def get_case_graph(self, db: Session, case_id: int, hops: int = 2) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def get_neighborhood(self, db: Session, entity_id: int, hops: int = 2) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def find_shortest_path(self, db: Session, source_id: int, target_id: int) -> Optional[List[Dict[str, Any]]]:
        pass

    @abc.abstractmethod
    def detect_circular_flows(self, db: Session) -> List[Dict[str, Any]]:
        pass


class NetworkXGraphService(IGraphService):
    """
    In-memory graph implementation using NetworkX.
    Provides fast, deterministic execution without external daemon dependency.
    """

    def __init__(self):
        self.analyzer = GraphAnalyzer()
        self._is_synced = False

    def sync_from_db(self, db: Session, force: bool = False) -> None:
        """Loads all entities, relationships, and transactions into graph."""
        if self._is_synced and not force:
            return

        entities = db.query(Entity).all()
        relationships = db.query(Relationship).all()
        transactions = db.query(Transaction).all()

        ent_dicts = [e.to_dict() for e in entities]
        rel_dicts = [r.to_dict() for r in relationships]
        tx_dicts = [t.to_dict() for t in transactions]

        self.analyzer.build_from_records(ent_dicts, rel_dicts, tx_dicts)
        self._is_synced = True

    def get_full_graph(self, db: Session, limit: int = 150) -> Dict[str, Any]:
        self.sync_from_db(db)
        nodes = []
        for n, data in list(self.analyzer.graph.nodes(data=True))[:limit]:
            nodes.append({
                "id": n,
                "numeric_id": data.get("numeric_id", 0),
                "label": data.get("label", n),
                "entity_type": data.get("entity_type", "UNKNOWN"),
                "risk_score": data.get("risk_score", 0.0),
                "metadata": data.get("meta_data", {})
            })

        node_ids = set(n["id"] for n in nodes)
        edges = []
        for u, v, data in self.analyzer.graph.edges(data=True):
            if u in node_ids and v in node_ids:
                edges.append({
                    "id": data.get("id", f"{u}_{v}"),
                    "source": u,
                    "target": v,
                    "relationship_type": data.get("relationship_type", "CONNECTED_TO"),
                    "confidence": data.get("confidence", 1.0),
                    "amount": data.get("amount"),
                    "metadata": data.get("meta_data", {})
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": self.analyzer.graph.number_of_nodes(),
                "total_edges": self.analyzer.graph.number_of_edges(),
            }
        }

    def get_case_graph(self, db: Session, case_id: int, hops: int = 2) -> Dict[str, Any]:
        """
        Retrieves graph associated with a case.
        Finds the CASE entity for this case and returns its neighborhood.
        """
        self.sync_from_db(db)
        case_rec = db.query(Case).filter(Case.id == case_id).first()
        if not case_rec:
            return {"nodes": [], "edges": [], "stats": {}}

        # Find entity representing this case
        case_ent = db.query(Entity).filter(
            Entity.entity_type == "CASE",
            Entity.normalized_value == case_rec.case_number
        ).first()

        center_node = f"e-{case_ent.id}" if case_ent else None

        # If no explicit case entity or disconnected, gather entities directly linked via relationships or transactions
        if not center_node or not self.analyzer.graph.has_node(center_node):
            # Gather entities with case_id in transactions or indicators
            tx_entities = db.query(Transaction).filter(Transaction.case_id == case_id).all()
            ent_ids = set()
            for tx in tx_entities:
                ent_ids.add(tx.sender_entity_id)
                ent_ids.add(tx.receiver_entity_id)
            if not ent_ids:
                return {"nodes": [], "edges": [], "stats": {}}
            first_ent = list(ent_ids)[0]
            center_node = f"e-{first_ent}"

        subgraph_data = self.analyzer.get_neighborhood(center_node, max_hops=hops, max_nodes=100)
        return {
            "nodes": subgraph_data["nodes"],
            "edges": subgraph_data["edges"],
            "stats": {
                "nodes_count": len(subgraph_data["nodes"]),
                "edges_count": len(subgraph_data["edges"]),
                "hops": hops,
            }
        }

    def get_neighborhood(self, db: Session, entity_id: int, hops: int = 2) -> Dict[str, Any]:
        self.sync_from_db(db)
        center_node = f"e-{entity_id}"
        subgraph_data = self.analyzer.get_neighborhood(center_node, max_hops=hops)
        return {
            "nodes": subgraph_data["nodes"],
            "edges": subgraph_data["edges"],
            "stats": {
                "nodes_count": len(subgraph_data["nodes"]),
                "edges_count": len(subgraph_data["edges"]),
                "hops": hops
            }
        }

    def find_shortest_path(self, db: Session, source_id: int, target_id: int) -> Optional[List[Dict[str, Any]]]:
        self.sync_from_db(db)
        return self.analyzer.find_shortest_path(f"e-{source_id}", f"e-{target_id}")

    def detect_circular_flows(self, db: Session) -> List[Dict[str, Any]]:
        self.sync_from_db(db)
        return self.analyzer.detect_circular_flows()

    def find_shared_infrastructure(self, db: Session) -> List[Dict[str, Any]]:
        """
        Finds infrastructure entities (PHONE, DOMAIN, UPI_ID, DEVICE, IP_ADDRESS)
        that are connected to 2 or more distinct cases.
        """
        self.sync_from_db(db)
        infra_types = ("PHONE", "DOMAIN", "UPI_ID", "DEVICE", "IP_ADDRESS")
        shared_list = []

        # Find all CASE entities
        case_nodes = {
            n: data.get("label")
            for n, data in self.analyzer.graph.nodes(data=True)
            if data.get("entity_type") == "CASE"
        }

        undirected = self.analyzer.graph.to_undirected(as_view=True)
        for n, data in self.analyzer.graph.nodes(data=True):
            if data.get("entity_type") in infra_types:
                # Find connected cases within 2 hops
                connected_cases = set()
                neighbors = nx.single_source_shortest_path_length(undirected, n, cutoff=2)
                for neighbor_id in neighbors:
                    if neighbor_id in case_nodes:
                        connected_cases.add(case_nodes[neighbor_id])

                if len(connected_cases) >= 2:
                    shared_list.append({
                        "node_id": n,
                        "numeric_id": data.get("numeric_id", 0),
                        "entity_type": data.get("entity_type"),
                        "value": data.get("label"),
                        "connected_case_count": len(connected_cases),
                        "connected_cases": list(connected_cases),
                        "risk_score": data.get("risk_score", 0.0),
                    })

        return sorted(shared_list, key=lambda x: x["connected_case_count"], reverse=True)


# Global singleton instance
graph_service = NetworkXGraphService()
