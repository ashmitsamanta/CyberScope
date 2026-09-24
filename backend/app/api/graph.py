from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from app.database import get_db
from app.schemas.graph import GraphData
from app.services.graph_service import graph_service

router = APIRouter(prefix="/graph", tags=["Fraud Graph"])


@router.get("", response_model=GraphData)
def get_fraud_graph(
    db: Session = Depends(get_db),
    limit: int = Query(150, ge=10, le=500)
):
    """Returns overview graph with top nodes and active edges."""
    return graph_service.get_full_graph(db, limit=limit)


@router.get("/case/{case_id}", response_model=GraphData)
def get_case_subgraph(
    case_id: int,
    db: Session = Depends(get_db),
    hops: int = Query(2, ge=1, le=4)
):
    """Extracts graph subgraph relevant to a specific case."""
    return graph_service.get_case_graph(db, case_id=case_id, hops=hops)


@router.get("/entity/{entity_id}", response_model=GraphData)
def get_entity_neighborhood(
    entity_id: int,
    db: Session = Depends(get_db),
    hops: int = Query(2, ge=1, le=3)
):
    """Expands graph around an entity up to k-hops."""
    return graph_service.get_neighborhood(db, entity_id=entity_id, hops=hops)


@router.get("/shortest-path")
def find_shortest_path(
    source_id: int = Query(..., description="Source entity ID"),
    target_id: int = Query(..., description="Target entity ID"),
    db: Session = Depends(get_db)
):
    """Finds shortest investigative path between two entities."""
    path = graph_service.find_shortest_path(db, source_id, target_id)
    if not path:
        return {"found": False, "path": [], "message": "No direct or multi-hop path found"}
    return {"found": True, "path": path, "hops": len(path) - 1}


@router.get("/circular-flows")
def detect_circular_flows(db: Session = Depends(get_db)):
    """Detects cycles in fund movement (A -> B -> C -> A)."""
    cycles = graph_service.detect_circular_flows(db)
    return {"cycles_count": len(cycles), "cycles": cycles}


@router.get("/shared-infrastructure")
def get_shared_infrastructure(db: Session = Depends(get_db)):
    """Finds infrastructure nodes connected to 2 or more distinct cases."""
    shared = graph_service.find_shared_infrastructure(db)
    return {"count": len(shared), "shared_infrastructure": shared}
