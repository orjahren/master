#!/usr/bin/env python

# Copyright (c) 2018-2020 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Follow leading vehicle scenario:

The scenario realizes a common driving behavior, in which the
user-controlled ego vehicle follows a leading car driving down
a given road. At some point the leading car has to slow down and
finally stop. The ego vehicle has to react accordingly to avoid
a collision. The scenario ends either via a timeout, or if the ego
vehicle stopped close enough to the leading vehicle
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
                                                                      PedestrianWalk,
                                                                      SetTrafficLightState,
                                                                      ChangeAutoPilot)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import (InTriggerDistanceToVehicle,
                                                                               InTriggerDistanceToNextIntersection,
                                                                               DriveDistance,
                                                                               StandStill,
                                                                               TriggerDistanceToLocation)
from srunner.scenariomanager.timer import TimeOut
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_waypoint_in_distance, get_location_in_distance_from_wp, get_crossing_point, get_next_traffic_light


class FollowLeadingVehicle(BasicScenario):
    """
    This class holds a complex "Follow a leading vehicle" scenario, enhancing
    the basic scenario with:
    - A parked vehicle on the side of the road, potentially narrowing the path.
    - A pedestrian crossing the road in front of the leading vehicle.
    - A dynamic vehicle that is on autopilot, adding to general traffic.
    - A traffic light that turns red as the leading vehicle approaches, forcing
      a more abrupt stop.

    This is a single ego vehicle scenario.
    """

    timeout = 180  # Increased timeout for added complexity

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=180):
        """
        Setup all relevant parameters and create scenario.

        If randomize is True, the scenario parameters are randomized.
        """
        self._map = CarlaDataProvider.get_map()
        self._leading_vehicle_spawn_distance = 25  # Distance from ego trigger point
        self._leading_vehicle_speed = 10  # m/s
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._leading_actor_max_brake = 1.0
        self._leading_actor_stop_in_front_intersection = 10 # Stop closer to intersection

        # New actor parameters (distances relative to ego trigger point)
        self._parked_vehicle_distance = self._leading_vehicle_spawn_distance + 30
        self._pedestrian_crossing_distance = self._leading_vehicle_spawn_distance + 45
        self._pedestrian_speed = 1.0 # m/s
        self._dynamic_vehicle_distance = self._leading_vehicle_spawn_distance + 15
        self._dynamic_vehicle_speed = 12 # m/s

        self._parked_vehicle_offset = 3.0 # Meters to the side of the lane
        self._traffic_light_state_change_trigger_distance = self._leading_actor_stop_in_front_intersection + 5 # When leading vehicle is this far from intersection, turn light red

        # Internal actor references
        self._leading_vehicle = None
        self._parked_vehicle = None
        self._pedestrian = None
        self._dynamic_vehicle = None
        self._traffic_light = None
        self._next_intersection_waypoint = None

        self.timeout = timeout

        super(ComplexFollowLeadingVehicle, self).__init__("ComplexFollowLeadingVehicle",
                                                          ego_vehicles,
                                                          config,
                                                          world,
                                                          debug_mode,
                                                          criteria_enable=criteria_enable)

        if randomize:
            self._leading_vehicle_speed = random.uniform(8, 12)
            self._pedestrian_speed = random.uniform(0.8, 1.5)
            self._dynamic_vehicle_speed = random.uniform(10, 15)
            self._leading_vehicle_spawn_distance = random.uniform(20, 30)
            self._parked_vehicle_distance = self._leading_vehicle_spawn_distance + random.uniform(25, 35)
            self._pedestrian_crossing_distance = self._leading_vehicle_spawn_distance + random.uniform(40, 50)
            self._dynamic_vehicle_distance = self._leading_vehicle_spawn_distance + random.uniform(10, 20)


    def _initialize_actors(self, config):
        """
        Custom initialization for all actors.
        """
        # 1. Leading Vehicle
        leading_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._leading_vehicle_spawn_distance)
        leading_vehicle_transform = leading_vehicle_waypoint.transform
        leading_vehicle_transform.location.z += 0.5 # Avoid z-fighting with road
        self._leading_vehicle = CarlaDataProvider.request_new_actor('vehicle.nissan.patrol', leading_vehicle_transform)
        self.other_actors.append(self._leading_vehicle)

        # Determine the target intersection and its traffic light for the leading vehicle to stop
        self._traffic_light = CarlaDataProvider.get_next_traffic_light(self._leading_vehicle, False)
        if self._traffic_light:
            self._next_intersection_waypoint = CarlaDataProvider.get_map().get_waypoint(self._traffic_light.get_transform().location)
        else:
            # Fallback if no traffic light found, find the next junction waypoint
            curr_wp = leading_vehicle_waypoint
            junction_wp = None
            while True:
                next_wps = curr_wp.next(5.0) # Look 5 meters ahead
                if not next_wps: # End of road or invalid
                    break
                for nw in next_wps:
                    if nw.is_junction:
                        junction_wp = nw
                        break
                if junction_wp:
                    break
                curr_wp = next_wps[0] # Continue along the first path

            self._next_intersection_waypoint = junction_wp if junction_wp else get_waypoint_in_distance(leading_vehicle_waypoint, 100)[0]


        # 2. Parked Vehicle
        parked_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._parked_vehicle_distance)
        # Offset to the right of the lane
        parked_vehicle_offset_waypoint = get_location_in_distance_from_wp(parked_vehicle_waypoint, self._parked_vehicle_offset, False)
        parked_vehicle_transform = carla.Transform(parked_vehicle_offset_waypoint.location, parked_vehicle_waypoint.transform.rotation)
        parked_vehicle_transform.location.z += 0.5
        self._parked_vehicle = CarlaDataProvider.request_new_actor('vehicle.tesla.model3', parked_vehicle_transform)
        self._parked_vehicle.set_simulate_physics(False) # Parked, no physics needed
        self.other_actors.append(self._parked_vehicle)

        # 3. Pedestrian
        pedestrian_spawn_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._pedestrian_crossing_distance)
        pedestrian_start_location, pedestrian_end_location = get_crossing_point(pedestrian_spawn_waypoint)
        pedestrian_transform = carla.Transform(pedestrian_start_location, carla.Rotation())
        pedestrian_transform.location.z += 0.5 # Pedestrians are usually higher than 0 z
        self._pedestrian = CarlaDataProvider.request_new_actor('walker.pedestrian.0001', pedestrian_transform)
        self.other_actors.append(self._pedestrian)

        # 4. Dynamic Vehicle (adding general traffic complexity)
        dynamic_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._dynamic_vehicle_distance)
        # Spawn in current lane or an adjacent one
        if random.random() < 0.5 and dynamic_vehicle_waypoint.get_left_lane():
            dynamic_vehicle_waypoint = dynamic_vehicle_waypoint.get_left_lane()
        dynamic_vehicle_transform = dynamic_vehicle_waypoint.transform
        dynamic_vehicle_transform.location.z += 0.5
        self._dynamic_vehicle = CarlaDataProvider.request_new_actor('vehicle.audi.a2', dynamic_vehicle_transform)
        self._dynamic_vehicle.set_autopilot(True, CarlaDataProvider.get_traffic_manager_port())
        self.other_actors.append(self._dynamic_vehicle)


    def _create_behavior(self):
        """
        Creates the enhanced behavior tree for the complex scenario.
        """
        # Initial actor placement
        sequence = py_trees.composites.Sequence("ComplexFollowLeadingVehicle Scenario")
        sequence.add_child(ActorTransformSetter(self._leading_vehicle, self._leading_vehicle.get_transform()))
        sequence.add_child(ActorTransformSetter(self._parked_vehicle, self._parked_vehicle.get_transform()))
        sequence.add_child(ActorTransformSetter(self._pedestrian, self._pedestrian.get_transform()))
        sequence.add_child(ActorTransformSetter(self._dynamic_vehicle, self._dynamic_vehicle.get_transform()))

        # --- Leading Vehicle Driving Behavior ---
        leading_vehicle_driving = py_trees.composites.Parallel(
            "LeadingVehicleDrivingToIntersection", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE
        )
        leading_vehicle_driving.add_child(WaypointFollower(self._leading_vehicle, self._leading_vehicle_speed))
        # Trigger when leading vehicle is close enough to its intended stop point (next intersection)
        leading_vehicle_driving.add_child(InTriggerDistanceToLocation(
            self._leading_vehicle, self._next_intersection_waypoint.transform.location,
            self._leading_actor_stop_in_front_intersection + 10 # Trigger to initiate braking sequence
        ))

        # --- Pedestrian Crossing Behavior ---
        pedestrian_cross_atomic = py_trees.composites.Sequence("Pedestrian Crossing Sequence")
        # Trigger pedestrian to cross when leading vehicle is sufficiently close
        pedestrian_crossing_trigger = TriggerDistanceToLocation(
            self._leading_vehicle,
            self._pedestrian.get_location(),
            distance=15 # Trigger when leading vehicle is 15m from pedestrian's spawn point
        )
        _, pedestrian_end_location = get_crossing_point(self._map.get_waypoint(self._pedestrian.get_location()))
        pedestrian_cross_atomic.add_child(pedestrian_crossing_trigger)
        pedestrian_cross_atomic.add_child(PedestrianWalk(self._pedestrian,
                                                          pedestrian_end_location.x,
                                                          pedestrian_end_location.y,
                                                          self._pedestrian_speed))
        pedestrian_cross_atomic.add_child(StandStill(self._pedestrian, name="PedestrianStops", duration=2)) # Stand still after crossing

        # --- Traffic Light Control Behavior ---
        traffic_light_behavior = py_trees.composites.Sequence("Traffic Light Control")
        if self._traffic_light:
            traffic_light_approach_trigger = TriggerDistanceToLocation(
                self._leading_vehicle, self._next_intersection_waypoint.transform.location,
                distance=self._traffic_light_state_change_trigger_distance
            )
            traffic_light_behavior.add_child(traffic_light_approach_trigger)
            traffic_light_behavior.add_child(SetTrafficLightState(self._traffic_light, carla.TrafficLightState.Red))
            traffic_light_behavior.add_child(TimeOut(5)) # Stay red for 5 seconds
            traffic_light_behavior.add_child(SetTrafficLightState(self._traffic_light, carla.TrafficLightState.Green))
        else:
            traffic_light_behavior.add_child(py_trees.behaviours.Success("No Traffic Light to Control")) # Placeholder if no traffic light

        # --- Combine all dynamic elements leading up to the stop ---
        mid_scenario_complexities = py_trees.composites.Parallel(
            "MidScenarioComplexities", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL
        )
        mid_scenario_complexities.add_child(leading_vehicle_driving) # Leading vehicle drives
        mid_scenario_complexities.add_child(pedestrian_cross_atomic) # Pedestrian crosses
        mid_scenario_complexities.add_child(traffic_light_behavior) # Traffic light changes


        # --- Leading Vehicle Final Stop ---
        leading_vehicle_stop_condition = InTriggerDistanceToLocation(
            self._leading_vehicle, self._next_intersection_waypoint.transform.location,
            self._leading_actor_stop_in_front_intersection
        )
        leading_vehicle_final_stop = py_trees.composites.Sequence("LeadingVehicleFinalStop")
        leading_vehicle_final_stop.add_child(leading_vehicle_stop_condition)
        leading_vehicle_final_stop.add_child(StopVehicle(self._leading_vehicle, self._leading_actor_max_brake))


        # --- End Condition for Ego Vehicle ---
        end_condition = py_trees.composites.Parallel("Waiting for Ego End Position",
                                                     policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        end_condition.add_child(InTriggerDistanceToVehicle(
            self._leading_vehicle, self.ego_vehicles[0], distance=10, name="FinalDistanceToLeading"))
        end_condition.add_child(StandStill(self.ego_vehicles[0], name="EgoStandStill", duration=2))

        # --- Build the full behavior tree ---
        sequence.add_child(mid_scenario_complexities) # All parallel challenges (LV driving, pedestrian, traffic light)
        sequence.add_child(leading_vehicle_final_stop) # Leading vehicle stops based on condition
        sequence.add_child(end_condition)             # Ego must stop behind
        sequence.add_child(ActorDestroy(self._leading_vehicle))
        sequence.add_child(ActorDestroy(self._parked_vehicle))
        sequence.add_child(ActorDestroy(self._pedestrian))
        sequence.add_child(ActorDestroy(self._dynamic_vehicle)) # Clean up dynamic vehicle

        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []

        collision_ego_leading = CollisionTest(self.ego_vehicles[0], self._leading_vehicle, name="EgoLeadingCollision")
        collision_ego_parked = CollisionTest(self.ego_vehicles[0], self._parked_vehicle, name="EgoParkedCollision")
        collision_ego_pedestrian = CollisionTest(self.ego_vehicles[0], self._pedestrian, name="EgoPedestrianCollision")
        collision_ego_dynamic = CollisionTest(self.ego_vehicles[0], self._dynamic_vehicle, name="EgoDynamicCollision")
        collision_leading_pedestrian = CollisionTest(self._leading_vehicle, self._pedestrian, name="LeadingPedestrianCollision")

        criteria.append(collision_ego_leading)
        criteria.append(collision_ego_parked)
        criteria.append(collision_ego_pedestrian)
        criteria.append(collision_ego_dynamic)
        criteria.append(collision_leading_pedestrian)

        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()