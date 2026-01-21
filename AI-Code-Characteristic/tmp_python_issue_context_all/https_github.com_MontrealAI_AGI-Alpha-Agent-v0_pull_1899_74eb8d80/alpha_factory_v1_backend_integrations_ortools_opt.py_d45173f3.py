# SPDX-License-Identifier: Apache-2.0
"""
Lightweight wrapper around Google OR-Tools with safe fall-backs.

Used by:
    • ManufacturingAgent  – job-shop / flow-shop scheduling
    • SupplyChainAgent    – vehicle-routing / MILP network flow
"""

from __future__ import annotations

import logging
from typing import Dict, List, Sequence, Tuple

_LOG = logging.getLogger("alpha_factory.ortools")
_LOG.addHandler(logging.NullHandler())

# --------------------------------------------------------------------- #
#  Optional import – we NEVER raise ImportError at module import time   #
# --------------------------------------------------------------------- #
try:
    from ortools.sat.python import cp_model
    from ortools.constraint_solver import routing_enums_pb2, pywrapcp

    _ORTOOLS_OK = True
except ModuleNotFoundError:  # stripped container or slim CPU build
    _ORTOOLS_OK = False
    cp_model = None
    pywrapcp = None


# ===================================================================== #
#  Public helpers                                                       #
# ===================================================================== #
def schedule_jobshop(
    jobs: List[List[Tuple[str, int]]],  # [(machine, duration), …] per job
    horizon: int,
) -> Dict[Tuple[int, str], Tuple[int, int]]:
    """
    Solve a minimal-makespan job-shop problem.

    Returns
    -------
    dict
        Keys are ``(job_id, machine)`` pairs, values are ``(start, end)``.
        On fallback mode a greedy schedule is returned instead.
    """
    if _ORTOOLS_OK:
        return _solve_jobshop_ortools(jobs, horizon)

    _LOG.warning("OR-Tools missing – using greedy fallback schedule")
    return _solve_jobshop_greedy(jobs)


def solve_vrp(
    distance_matrix: Sequence[Sequence[int]],
    demands: Sequence[int],
    vehicle_cap: int,
) -> List[List[int]]:
    """
    Capacitated Vehicle-Routing (single depot @ index 0).

    Returns
    -------
    List of routes, each a list of location indices.  
    In fallback mode we create one vehicle per demand.
    """
    if _ORTOOLS_OK:
        return _solve_vrp_ortools(distance_matrix, demands, vehicle_cap)

    _LOG.warning("OR-Tools missing – using naive VRP fallback")
    return [[0, i, 0] for i in range(1, len(distance_matrix))]


# ===================================================================== #
#  Internal – OR-Tools back-ends                                        #
# ===================================================================== #
def _solve_jobshop_ortools(
    jobs: List[List[Tuple[str, int]]],
    horizon: int,
) -> Dict[Tuple[int, str], Tuple[int, int]]:
    model = cp_model.CpModel()
    task_vars: Dict[Tuple[int, str], Tuple[cp_model.IntVar, cp_model.IntVar, cp_model.IntervalVar]] = {}

    machine_to_intervals: Dict[str, List[cp_model.IntervalVar]] = {}

    for j_id, job in enumerate(jobs):
        prev_end = None
        for m_name, duration in job:
            start = model.NewIntVar(0, horizon, f"start_{j_id}_{m_name}")
            end = model.NewIntVar(0, horizon, f"end_{j_id}_{m_name}")
            interval = model.NewIntervalVar(start, duration, end, f"int_{j_id}_{m_name}")
            task_vars[(j_id, m_name)] = (start, end, interval)

            machine_to_intervals.setdefault(m_name, []).append(interval)

            if prev_end is not None:  # job precedence
                model.Add(start >= prev_end)
            prev_end = end

    # One machine at a time
    for ivals in machine_to_intervals.values():
        model.AddNoOverlap(ivals)

    # Objective: minimise overall makespan
    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, [v[1] for v in task_vars.values()])
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        _LOG.warning("CP-SAT did not find a solution – falling back to greedy")
        return _solve_jobshop_greedy(jobs)

    return {
        key: (int(solver.Value(var[0])), int(solver.Value(var[1])))
        for key, var in task_vars.items()
    }


def _solve_vrp_ortools(
    distance_matrix: Sequence[Sequence[int]],
    demands: Sequence[int],
    vehicle_cap: int,
) -> List[List[int]]:
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_cb(from_i: int, to_i: int) -> int:
        return distance_matrix[int(manager.IndexToNode(from_i))][int(manager.IndexToNode(to_i))]

    transit_callback = routing.RegisterTransitCallback(distance_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback)

    def demand_cb(from_i: int) -> int:
        return demands[int(manager.IndexToNode(from_i))]

    demand_callback = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback,
        0,
        [vehicle_cap],
        True,
        "Capacity",
    )

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    solution = routing.SolveWithParameters(search_params)

    if solution is None:
        _LOG.warning("VRP solver failed – falling back to naive routing")
        return [[0, i, 0] for i in range(1, len(distance_matrix))]

    route: List[List[int]] = [[]]
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route[0].append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route[0].append(0)
    return route


# ===================================================================== #
#  Internal – greedy fall-backs                                         #
# ===================================================================== #
def _solve_jobshop_greedy(
    jobs: List[List[Tuple[str, int]]],
) -> Dict[Tuple[int, str], Tuple[int, int]]:
    time_at_machine: Dict[str, int] = {}
    schedule: Dict[Tuple[int, str], Tuple[int, int]] = {}

    for j_id, ops in enumerate(jobs):
        current_time = 0
        for m_name, dur in ops:
            current_time = max(current_time, time_at_machine.get(m_name, 0))
            schedule[(j_id, m_name)] = (current_time, current_time + dur)
            time_at_machine[m_name] = current_time + dur
            current_time += dur

    return schedule
