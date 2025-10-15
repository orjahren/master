#!/usr/bin/env python

# Copyright (c) 2018-2020 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Enhanced Follow leading vehicle scenario:

The scenario realizes a common driving behavior, in which the
user-controlled ego vehicle follows a leading car driving down
a given road. This enhanced version introduces more complexity:
1. A pedestrian crosses the road in front of the leading vehicle, forcing it
   to react and slow down/stop unexpectedly.
2. A parked vehicle partially obstructs the road near the final stopping point,
   decreasing visibility and narrowing the path.
At some point, the leading car has to slow down and
finally stop. The ego vehicle has to react accordingly to avoid
a collision and navigate the increased complexity. The scenario ends either via a timeout, or if the ego
vehicle stopped close enough to the leading vehicle.
"""

import random

import py_trees

import carla

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter,
                                                                      ActorDestroy,
                                                                      KeepVelocity,
                                                                      StopVehicle,
                                                                      WaypointFollower,
                                                                      WalkToLocation)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import (InTriggerDistanceToVehicle,
                                                                               InTriggerDistanceToNextIntersection,
                                                                               DriveDistance,
                                                                               StandStill)
from srunner.scenariomanager.timer import TimeOut
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_waypoint_in_distance


class FollowLeadingVehicle(BasicScenario):

    """
    This class holds everything required for a complex "Follow a leading vehicle"
    scenario involving two vehicles, a pedestrian, and a parked car. (Traffic Scenario 2)

    This is a single ego vehicle scenario, with enhanced complexity.
    """

    timeout = 180            # Increased timeout of scenario in seconds for more complexity

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=60):
        """
        Setup all relevant parameters and create scenario

        If randomize is True, the scenario parameters are randomized
        """

        self._map = CarlaDataProvider.get_map()
        self._first_vehicle_location = 25 # Distance of leading vehicle from ego's trigger point
        self._first_vehicle_speed = 10
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._other_actor_max_brake = 1.0
        self._other_actor_stop_in_front_intersection = 20 # Distance from intersection for leading vehicle to stop
        self._leading_vehicle_transform = None # Store leading vehicle's initial transform

        # New parameters for added complexity
        self._pedestrian_start_distance = self._first_vehicle_location + 15 # Pedestrian appears 15m ahead of leading car's start
        self._parked_vehicle_distance = self._first_vehicle_location + 30 # Parked car appears 30m ahead of leading car's start
        self._parked_vehicle_lateral_offset = 3.0 # Offset from center of lane for parked car

        # Timeout of scenario in seconds
        self.timeout = timeout if timeout else self.timeout

        super(FollowLeadingVehicle, self).__init__("FollowVehicleComplex", # Changed scenario name
                                                   ego_vehicles,
                                                   config,
                                                   world,
                                                   debug_mode,
                                                   criteria_enable=criteria_enable)

        if randomize:
            self._ego_other_distance_start = random.randint(4, 8)
            # Further randomization of speeds, distances, pedestrian timing could be added here.

    def _initialize_actors(self, config):
        """
        Custom initialization of leading vehicle, pedestrian, and parked vehicle.
        """
        # 1. Leading Vehicle
        waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._first_vehicle_location)
        transform = waypoint.transform
        transform.location.z += 0.5
        first_vehicle = CarlaDataProvider.request_new_actor('vehicle.nissan.patrol', transform)
        self.other_actors.append(first_vehicle)
        self._leading_vehicle_transform = transform # Store for potential ActorTransformSetter later if needed

        # 2. Pedestrian
        ped_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._pedestrian_start_distance)

        # Calculate pedestrian spawn point on the right sidewalk (relative to vehicle's forward direction)
        ped_spawn_location = ped_waypoint.transform.location
        # Move pedestrian to the right of the lane, assuming 1.0m for sidewalk
        ped_spawn_location += ped_waypoint.transform.get_right_vector() * (ped_waypoint.lane_width / 2.0 + 1.0)
        ped_spawn_location.z += 0.5 # Adjust Z to be on the ground

        ped_transform = carla.Transform(ped_spawn_location, ped_waypoint.transform.rotation)
        pedestrian = CarlaDataProvider.request_new_actor('walker.pedestrian.0001', ped_transform)
        self.other_actors.append(pedestrian)

        # 3. Parked Vehicle
        parked_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._parked_vehicle_distance)
        # Parked vehicle on the side of the road, slightly obstructing vision/lane
        parked_transform = carla.Transform(
            carla.Location(parked_waypoint.transform.location.x,
                           parked_waypoint.transform.location.y + self._parked_vehicle_lateral_offset, # Offset to the side
                           parked_waypoint.transform.location.z + 0.1), # Ensure it's on the ground
            parked_waypoint.transform.rotation
        )
        parked_vehicle = CarlaDataProvider.request_new_actor('vehicle.volkswagen.t2', parked_transform)
        parked_vehicle.set_autopilot(False) # Ensure it doesn't move
        parked_vehicle.set_simulate_physics(False) # Optional, prevents accidental movement
        self.other_actors.append(parked_vehicle)


    def _create_behavior(self):
        """
        The scenario defined after is an enhanced "follow leading vehicle" scenario.
        It integrates a pedestrian crossing and a parked vehicle.
        """

        # 1. Leading vehicle drives, potentially reacting to pedestrian
        leading_vehicle_driving = py_trees.composites.Parallel(
            "LeadingVehicleDrivingAndPedestrianCrossing",
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)

        # Leading vehicle follows waypoints
        leading_vehicle_follower = WaypointFollower(self.other_actors[0], self._first_vehicle_speed) # self.other_actors[0] is leading vehicle
        
        # Pedestrian crosses the road (self.other_actors[1])
        # Calculate target location for pedestrian on the left sidewalk
        ped_waypoint_for_crossing, _ = get_waypoint_in_distance(self._reference_waypoint, self._pedestrian_start_distance)
        ped_target_location = ped_waypoint_for_crossing.transform.location
        # Move pedestrian to the left of the lane, assuming 1.0m for sidewalk
        ped_target_location -= ped_waypoint_for_crossing.transform.get_right_vector() * (ped_waypoint_for_crossing.lane_width / 2.0 + 1.0)
        ped_target_location.z += 0.5

        pedestrian_cross_behavior = WalkToLocation(self.other_actors[1], ped_target_location)
        
        # Introduce a delay for pedestrian to start crossing AFTER leading vehicle has started moving.
        pedestrian_start_sequence = py_trees.composites.Sequence("PedestrianStartSequence")
        pedestrian_start_sequence.add_child(TimeOut(5)) # Wait 5 seconds after scenario start
        pedestrian_start_sequence.add_child(pedestrian_cross_behavior)

        # Leading vehicle drives while the pedestrian sequence is active.
        # Carla's AI for vehicles should automatically react to the pedestrian.
        leading_vehicle_driving.add_child(leading_vehicle_follower)
        leading_vehicle_driving.add_child(pedestrian_start_sequence)

        # Wait for leading vehicle to be close to the intersection to decide to stop (its final stop)
        leading_vehicle_at_intersection_trigger = InTriggerDistanceToNextIntersection(
            self.other_actors[0], self._other_actor_stop_in_front_intersection
        )
        
        # Sequence for the leading vehicle's overall journey: drive, reach intersection, then stop
        leading_vehicle_overall_journey = py_trees.composites.Sequence("LeadingVehicleJourney")
        leading_vehicle_overall_journey.add_child(leading_vehicle_driving) # Includes pedestrian interaction
        leading_vehicle_overall_journey.add_child(leading_vehicle_at_intersection_trigger)
        leading_vehicle_overall_journey.add_child(StopVehicle(self.other_actors[0], self._other_actor_max_brake)) # Stops at intersection

        # 2. End condition for Ego Vehicle
        # The ego vehicle must stop close enough to the leading vehicle and stand still.
        endcondition = py_trees.composites.Parallel("Waiting for end position",
                                                    policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        endcondition_part1 = InTriggerDistanceToVehicle(self.other_actors[0], # Leading vehicle
                                                        self.ego_vehicles[0],
                                                        distance=10, # Reduced distance for tighter following
                                                        name="FinalDistance")
        endcondition_part2 = StandStill(self.ego_vehicles[0], name="StandStill", duration=2) # Increased duration for stand still
        endcondition.add_child(endcondition_part1)
        endcondition.add_child(endcondition_part2)

        # Build overall behavior tree
        sequence = py_trees.composites.Sequence("ComplexFollowVehicleBehavior")
        sequence.add_child(leading_vehicle_overall_journey)
        sequence.add_child(endcondition)
        
        # Clean up all actors at the end
        sequence.add_child(ActorDestroy(self.other_actors[0], name="DestroyLeadingVehicle"))
        sequence.add_child(ActorDestroy(self.other_actors[1], name="DestroyPedestrian"))
        sequence.add_child(ActorDestroy(self.other_actors[2], name="DestroyParkedVehicle")) # self.other_actors[2] is parked vehicle

        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []

        collision_criterion = CollisionTest(self.ego_vehicles[0])
        # Additional criteria could be added here, e.g.,
        #   - OffRoadTest: if the parked car forces the ego off the road.
        #   - RunningRedLightTest: if there's an intersection with a traffic light.
        #   - DrivenDistanceTest: to ensure progress.

        criteria.append(collision_criterion)

        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()