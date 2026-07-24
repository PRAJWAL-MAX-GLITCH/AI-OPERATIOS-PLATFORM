"""
Workflow Engine Tests
=====================
"""
import pytest
from app.services.workflows.core.engine import DAGParser

class TestDAGParser:
    def test_parse_valid_dag(self):
        dag_def = {
            "tasks": [
                {"id": "t1", "type": "taskA"},
                {"id": "t2", "type": "taskB"}
            ],
            "edges": [
                {"from": "t1", "to": "t2"}
            ]
        }
        
        graph = DAGParser.parse_dag(dag_def)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        
        # Test get_ready_tasks
        ready = DAGParser.get_ready_tasks(graph, set())
        assert ready == ["t1"]
        
        ready = DAGParser.get_ready_tasks(graph, {"t1"})
        assert ready == ["t2"]

    def test_parse_cyclic_dag(self):
        dag_def = {
            "tasks": [
                {"id": "t1", "type": "taskA"},
                {"id": "t2", "type": "taskB"}
            ],
            "edges": [
                {"from": "t1", "to": "t2"},
                {"from": "t2", "to": "t1"}
            ]
        }
        
        with pytest.raises(ValueError, match="cyclic"):
            DAGParser.parse_dag(dag_def)
