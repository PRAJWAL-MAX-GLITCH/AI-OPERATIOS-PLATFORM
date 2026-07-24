"""
Workflow Engine
===============
Core engine for parsing DAGs and resolving dependencies.
"""
from typing import List, Dict, Set, Any
import networkx as nx

class DAGParser:
    """Parses workflow definitions and computes execution order."""
    
    @staticmethod
    def parse_dag(dag_definition: Dict[str, Any]) -> nx.DiGraph:
        """
        Parses a JSON DAG definition into a NetworkX directed graph.
        Format: {"tasks": [{"id": "t1", "type": "task_type"}], "edges": [{"from": "t1", "to": "t2"}]}
        """
        graph = nx.DiGraph()
        
        for task in dag_definition.get("tasks", []):
            graph.add_node(task["id"], **task)
            
        for edge in dag_definition.get("edges", []):
            graph.add_edge(edge["from"], edge["to"])
            
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("The provided workflow contains cyclic dependencies.")
            
        return graph

    @staticmethod
    def get_ready_tasks(graph: nx.DiGraph, completed_tasks: Set[str]) -> List[str]:
        """
        Given a graph and a set of completed task IDs, returns tasks that have all dependencies met
        and are ready to be executed.
        """
        ready_tasks = []
        for node in graph.nodes:
            if node in completed_tasks:
                continue
                
            # Check if all predecessors are completed
            predecessors = list(graph.predecessors(node))
            if all(p in completed_tasks for p in predecessors):
                ready_tasks.append(node)
                
        return ready_tasks

    @staticmethod
    def topological_sort(graph: nx.DiGraph) -> List[str]:
        """Returns the topological sorting of the tasks."""
        return list(nx.topological_sort(graph))
