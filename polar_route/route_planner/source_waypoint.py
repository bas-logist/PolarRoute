from polar_route.route_planner.routing_info import RoutingInfo
from polar_route.route_planner.waypoint import Waypoint
import numpy as np
import logging
import heapq

# Module logger
logger = logging.getLogger(__name__)


class SourceWaypoint(Waypoint):
    """
        Class derived from Waypoint that contains extra information for any source waypoint (routing information to
        other cellboxes and any visited cellboxes)

        Attributes:
            visited_nodes: set<int>: a set containing the indices of the visited nodes
            routing_table: dict<cellbox_indx, Routing_Info>: a dict that contains the routing information to reach
            cellbox_indx, works a routing table to reach the different cellboxes from this source waypoint
    """

    def __init__(self, source, end_wps):
        """
            Initializes a SourceWaypoint object from a Waypoint object
            Args:
                source(Waypoint): an object that encapsulates the latitude, longitude, name and cellbox_id information
                end_wps (list <Waypoint>): list of the end waypoints
        """
        super().__init__(source.get_latitude(), source.get_longitude(), name=source.get_name())
        self.cellbox_indx = source.get_cellbox_indx()
        self.end_wps = end_wps
        self.visited_nodes = set()
        self.routing_table = dict()
        # add routing information to itself, empty list of segments as distance = 0
        self.routing_table[self.cellbox_indx] = RoutingInfo(self.cellbox_indx, [])

        # Cache of the current best-known objective function cost to reach each node,
        # keyed by cellbox index. Used by the Dijkstra search loop (route_planner.py) to
        # avoid recomputing costs by recursively walking the routing table's parent chain
        # (via get_obj) on every iteration. Only valid for the single objective function
        # used by that search (each SourceWaypoint is only ever searched with one
        # objective function over its lifetime).
        self._cost_cache = {self.cellbox_indx: 0.0}
        # Order in which each node was first discovered, used as a heap tie-breaker so that,
        # among nodes with equal cost, the earliest-discovered one is preferred - matching the
        # original linear-scan implementation's behaviour of picking the first (in insertion
        # order) minimum-cost node from the routing table.
        self._discovery_order = {self.cellbox_indx: 0}
        self._next_discovery_order = 1
        # Priority queue of (cost, discovery_order, node_id) entries, used to find the
        # cheapest not-yet-visited node in O(log n) instead of scanning `routing_table`
        # linearly. Stored on the SourceWaypoint itself (rather than as a local variable in
        # the search loop) so it persists correctly across multiple calls that reuse this
        # same object - e.g. bidirectional search reuses the same forward `wp` across
        # several destination waypoints, and the same backward `bwd_wp` across several
        # source waypoints sharing a destination. Entries are never eagerly removed when
        # superseded by a cheaper one; `peek_min_unvisited`/`pop_min_unvisited` lazily skip
        # over stale entries (already visited, or superseded by a cheaper recorded cost).
        self._heap = [(0.0, 0, self.cellbox_indx)]

    def update_routing_table(self, indx, routing_info):
        """
        Updates the source waypoint's routing table for a particular node with the given routing info
        Args:
            indx (str): the index of the cell to update
            routing_info (RoutingInfo): the routing info to be added
        """
        self.routing_table[indx] = routing_info

    def get_cached_cost(self, indx):
        """
        Returns the current best-known objective function cost to reach the given node, as
        maintained incrementally by `set_cached_cost`. Returns `np.inf` if the node hasn't been
        discovered yet.
        Args:
            indx (str): the index of the cell to look up
        """
        return self._cost_cache.get(str(indx), np.inf)

    def set_cached_cost(self, indx, cost):
        """
        Records the current best-known objective function cost to reach the given node,
        assigns it a discovery order the first time it's set, and pushes it onto the
        priority queue so it will be considered by `peek_min_unvisited`/`pop_min_unvisited`.
        Args:
            indx (str): the index of the cell to update
            cost (float): the new best-known cost to reach this cell
        """
        indx = str(indx)
        if indx not in self._discovery_order:
            self._discovery_order[indx] = self._next_discovery_order
            self._next_discovery_order += 1
        self._cost_cache[indx] = cost
        heapq.heappush(self._heap, (cost, self._discovery_order[indx], indx))

    def get_discovery_order(self, indx):
        """
        Returns the order in which the given node was first discovered (assigned by
        `set_cached_cost`), used as a heap tie-breaker.
        Args:
            indx (str): the index of the cell to look up
        """
        return self._discovery_order[str(indx)]

    def peek_min_unvisited(self):
        """
        Returns (indx, cost) of the cheapest not-yet-visited node currently known, without
        removing it, so it remains available if this frontier ends up not being expanded this
        round (e.g. the other direction's frontier is cheaper this iteration in bidirectional
        search). Lazily discards stale entries from the front of the heap along the way: ones
        for nodes already visited, or superseded by a since-improved (cheaper) cost.
        Returns:
            (indx, cost): (-1, np.inf) if there are no remaining unvisited candidates.
        """
        while self._heap:
            cost, _, indx = self._heap[0]
            if self.is_visited(indx) or cost > self.get_cached_cost(indx):
                heapq.heappop(self._heap)
                continue
            return indx, cost
        return -1, np.inf

    def pop_min_unvisited(self):
        """
        Removes and returns (indx, cost) of the cheapest not-yet-visited node, as found by
        `peek_min_unvisited`. Call this once the caller has committed to expanding this node
        (i.e. it's about to be marked visited).
        Returns:
            (indx, cost): (-1, np.inf) if there are no remaining unvisited candidates.
        """
        indx, cost = self.peek_min_unvisited()
        if indx != -1:
            heapq.heappop(self._heap)
        return indx, cost

    def visit(self, cellbox_indx):
        """
        Marks the input cellbox as visited by adding its index to the set of visited nodes
        Args:
            cellbox_indx (str): the index of the visited cellbox
        """
        self.visited_nodes.add(cellbox_indx)

    def is_visited(self, indx):
        """
        Check if the node with the given index has been visited
        Args:
            indx (int): the index of the node to check
        """
        return str(indx) in self.visited_nodes
    

    def is_all_cells_visited(self,cells):
        """
        Check if all cells have been visited
        Args:
            cells (list): List of cellbox id's to check against
        Returns:
            True if all have been visited and False if not
        """
        if len(cells) == 0:
            return True
        for cell in cells:
            if cell not in self.visited_nodes:
                return False
        return True


    def is_all_visited(self):
        """
        Check if all associated destination waypoints have been visited
        Returns:
            True if all have been visited and False if not

        """
        for wp in self.end_wps:
            if str(wp.get_cellbox_indx()) not in self.visited_nodes:
                return False
        return True

    def get_routing_info(self, _id):
        if _id not in self.routing_table.keys():
            self.routing_table[_id] = RoutingInfo(-1, None) # indicating inaccessible node and returns infinity obj
        return self.routing_table[_id]

    def get_path_nodes(self, _id):
        """
        Gets all nodes on the path from the source waypoint to the node at _id
        """
        if _id not in self.routing_table.keys():
            return []
        else:
            node_id = _id
            path_index = list()
            while node_id != self.cellbox_indx:
                node_indices = self.routing_table[node_id].get_path_nodes()
                path_index.insert(0, node_indices[1])
                node_id = node_indices[0]

            path_index.insert(0, self.cellbox_indx)


            return path_index

    def log_routing_table(self):
        logger.debug(f'Routing table of {self.cellbox_indx} source waypoint:')
        for x in self.routing_table.keys():
            logger.debug(f"To {x}, through node_idx: {self.routing_table[x].get_node_index()}")

    def log_detailed_routing_info(self):
        logger.debug(f'Routing table of {self.cellbox_indx} source waypoint:')
        for x in self.routing_table.keys():
            logger.debug(f"To {x}, through node_idx: {self.routing_table[x].get_node_index()}")
            logger.debug("using segments >> ")
            for s in self.routing_table[x].get_path():
                logger.debug(s.to_str())

    def get_obj(self, node_indx, obj):
        """
        Get the value of the objective function up to the specified node index
        Args:
            node_indx (str): the index along the path to calculate the value up to
            obj (str): the variable name corresponding to the objective function

        Returns:
            obj_value (float): the value of the objective function at the specified index along the route

        """
        if node_indx not in self.routing_table.keys():
            # This info means the node is inaccessible so the value of the objective function is infinity
            obj_value = np.inf
            return obj_value
        
        obj_value = 0
        # Sum segment values recursively until the source waypoint is reached
        for segment in self.routing_table[node_indx].get_path():
            obj_value += getattr(segment, obj)

        through_indx = self.routing_table[node_indx].node_indx
        # Search recursively and sum up the remaining segments until we reach the source waypoint
        while through_indx != self.cellbox_indx:
                for segment in self.routing_table[through_indx].get_path():
                        obj_value += getattr(segment, obj)
                through_indx = self.routing_table[through_indx].node_indx 
 
        return obj_value
