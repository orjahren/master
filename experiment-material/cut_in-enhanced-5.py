```python
#!/usr/bin/env python

# Copyright (c) 2019-2020 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Cut in scenario:

The scenario realizes a driving behavior on the highway.
The user-controlled ego vehicle is driving straight and keeping its velocity at a constant level.
Another car is cutting just in front, coming from left or right lane.

The ego vehicle may need to brake to avoid a collision.
"""

import random
import py_trees
import carla

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter,
                                                                      LaneChange,
                                                                      WaypointFollower,
                                                                      AccelerateToCatchUp,
                                                                      KeepVelocity) # Added KeepVelocity for background traffic
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import InTriggerDistanceToVehicle, DriveDistance
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_waypoint_in_distance # Added for spawning background traffic


class CutIn(BasicScenario):

    """
    The ego vehicle is driving on a highway and another car is cutting in just in front.
    This is a single ego vehicle scenario, now enhanced with more complexity due to
    adverse weather, challenging time of day, and additional background traffic.
    """

    timeout = 1200

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=600):

        self.timeout = timeout
        self._map = CarlaDataProvider.get_map()
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)

        self._velocity = 40  # Default velocity for cut-in vehicle
        self._delta_velocity = 10 # Default delta velocity for cut-in acceleration
        self._trigger_distance = 30 # Default distance for cut-in trigger

        # --- ENHANCEMENT: More detailed randomization for key parameters ---
        if randomize:
            self._velocity = random.uniform(25, 55) # Slightly wider range for cut-in vehicle speed
            self._trigger_distance = random.uniform(15, 45) # Slightly wider range for cut-in trigger distance
            self._delta_velocity = random.uniform(8, 18) # Randomize acceleration aggressiveness of cut-in car
            self._background_traffic_speed_variation = random.uniform(0.8, 1.2) # For background traffic speed
        else:
            self._background_traffic_speed_variation = 1.0


        # get direction from config name
        self._config = config
        self._direction = None
        self._transform_visible = None # This is for initial spawn location (above map)

        self.number_of_background_vehicles = 3 # --- ENHANCEMENT: Number of additional background vehicles ---
        self.background_vehicles = [] # List to store background vehicles

        super(CutIn, self).__init__("CutIn",
                                    ego_vehicles,
                                    config,
                                    world,
                                    debug_mode,
                                    criteria_enable=criteria_enable)

        # --- ENHANCEMENT: Add adverse weather and time of day ---
        self._setup_environment()


    def _setup_environment(self):
        """
        Sets up the environment with adverse weather and challenging time of day.
        This significantly decreases driveability by reducing visibility and grip.
        """
        # Randomize weather parameters for more variations and challenge
        weather_params = carla.WeatherParameters(
            cloudiness=random.uniform(70, 100),
            precipitation=random.uniform(50, 90), # Rain
            precipitation_deposits=random.uniform(50, 90), # Puddles
            wind_intensity=random.uniform(0.5, 1.5), # Stronger wind
            fog_density=random.uniform(20, 50), # Moderate fog
            wetness=random.uniform(50, 90), # Wet roads
            sun_altitude_angle=random.uniform(-10, 10) # Dusk/Dawn or low sun
        )
        self.world.set_weather(weather_params)

        # Force challenging time of day (night or very low sun angle)
        if random.random() < 0.6: # 60% chance of night
            self.world.set_weather(carla.WeatherParameters(
                sun_altitude_angle=-90.0,
                cloudiness=random.uniform(80, 100),
                precipitation=random.uniform(60, 100),
                precipitation_deposits=random.uniform(60, 100),
                wetness=random.uniform(70, 100),
                fog_density=random.uniform(30, 60),
                moon_intensity=random.uniform(0.1, 0.5) # Dim moonlight
            ))
        else: # Dusk/dawn with challenging conditions
            self.world.set_weather(carla.WeatherParameters(
                sun_altitude_angle=random.uniform(-20, 20),
                cloudiness=random.uniform(70, 100),
                precipitation=random.uniform(30, 70),
                precipitation_deposits=random.uniform(30, 70),
                wetness=random.uniform(30, 70),
                fog_density=random.uniform(10, 40)
            ))

    def _initialize_actors(self, config):

        # direction of lane, on which other_actor is driving before lane change
        if 'LEFT' in self._config.name.upper():
            self._direction = 'left'

        if 'RIGHT' in self._config.name.upper():
            self._direction = 'right'

        # add actors from xml file (this is the cutting-in vehicle)
        for actor in config.other_actors:
            vehicle = CarlaDataProvider.request_new_actor(actor.model, actor.transform)
            self.other_actors.append(vehicle)
            # Initially disable physics. It will be enabled by ActorTransformSetter when it drops.
            vehicle.set_simulate_physics(enabled=False)

        # transform visible: This places the cutting-in car high above the map initially
        other_actor_transform = self.other_actors[0].get_transform()
        self._transform_visible = carla.Transform(
            carla.Location(other_actor_transform.location.x,
                           other_actor_transform.location.y,
                           other_actor_transform.location.z + 105), # Spawn high above
            other_actor_transform.rotation)

        # --- ENHANCEMENT: Spawn background traffic to increase complexity ---
        self._spawn_background_traffic()

    def _spawn_background_traffic(self):
        """
        Spawns additional background vehicles to increase traffic density and complexity.
        These vehicles will follow simple driving behaviors.
        """
        ego_waypoint = self._map.get_waypoint(self.ego_vehicles[0].get_location())

        available_vehicle_blueprints = CarlaDataProvider.get_filtered_traffic_actor_blueprints(
            'vehicle.*',
            rolename='background'
        )
        if not available_vehicle_blueprints:
            return # No blueprints available, skip spawning background traffic

        spawn_points = []

        # Background vehicle 1: On ego's lane, behind ego
        wp_behind_ego = get_waypoint_in_distance(ego_waypoint, -random.uniform(25, 45), False)
        if wp_behind_ego and wp_behind_ego.lane_id == ego_waypoint.lane_id:
            spawn_points.append(wp_behind_ego.transform)

        # Background vehicle 2: On ego's lane, ahead of ego (further away, possibly slower)
        wp_ahead_ego = get_waypoint_in_distance(ego_waypoint, random.uniform(60, 100), False)
        if wp_ahead_ego and wp_ahead_ego.lane_id == ego_waypoint.lane_id:
            spawn_points.append(wp_ahead_ego.transform)

        # Background vehicle 3: On an adjacent lane, adding general highway traffic
        # This car will be on the lane opposite to where the cut-in is coming from,
        # making the driving environment more dense and limiting escape routes.
        if self._direction == 'left': # Cut-in from left, add traffic on right lane
            adjacent_lane_wp = ego_waypoint.get_right_lane()
        else: # Cut-in from right, add traffic on left lane
            adjacent_lane_wp = ego_waypoint.get_left_lane()

        if adjacent_lane_wp:
            # Place it slightly behind or abreast of ego
            wp_adj_lane = get_waypoint_in_distance(adjacent_lane_wp, random.uniform(-10, 20), False)
            if wp_adj_lane:
                spawn_points.append(wp_adj_lane.transform)

        # Spawn the vehicles
        for i in range(min(self.number_of_background_vehicles, len(spawn_points))):
            bp = random.choice(available_vehicle_blueprints)
            transform = spawn_points[i]
            # Adjust Z to prevent spawning issues if ground isn't perfectly flat
            transform.location.z += 0.5

            vehicle = CarlaDataProvider.request_new_actor(bp.id, transform)
            if vehicle:
                self.background_vehicles.append(vehicle)
                self.other_actors.append(vehicle) # Add to general other_actors for cleanup and criteria checks
                vehicle.set_simulate_physics(enabled=True) # Background vehicles should have physics


    def _create_behavior(self):
        """
        Order of sequence:
        - car_visible: spawn cut-in car at a visible transform (above map)
        - just_drive: drive until in trigger distance to ego_vehicle
        - accelerate: accelerate to catch up distance to ego_vehicle
        - lane_change: change the lane
        - endcondition: drive for a defined distance

        --- ENHANCEMENT: Integrate background traffic behaviors ---
        """

        # --- Cut-in vehicle behavior (Original logic, now wrapped in a sequence) ---
        cut_in_behavior_sequence = py_trees.composites.Sequence("CutInBehavior")

        # car_visible: Teleport cut-in car high above, then let it drop (physics enabled by setter)
        car_visible = ActorTransformSetter(self.other_actors[0], self._transform_visible, physics_enabled=True)
        cut_in_behavior_sequence.add_child(car_visible)

        # just_drive: Wait until cut-in car is close enough to ego
        just_drive_parallel = py_trees.composites.Parallel(
            "DrivingStraightUntilTrigger", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)

        # The actual driving behavior for the cutting-in car
        cut_in_car_driving = WaypointFollower(self.other_actors[0], self._velocity)
        just_drive_parallel.add_child(cut_in_car_driving)

        # Trigger condition: When the cut-in car is within trigger distance to ego
        trigger_distance_condition = InTriggerDistanceToVehicle(
            self.other_actors[0], self.ego_vehicles[0], self._trigger_distance)
        just_drive_parallel.add_child(trigger_distance_condition)
        cut_in_behavior_sequence.add_child(just_drive_parallel)

        # accelerate: Accelerate to match/catch up with ego
        accelerate = AccelerateToCatchUp(self.other_actors[0], self.ego_vehicles[0], throttle_value=1,
                                         delta_velocity=self._delta_velocity, trigger_distance=5, max_distance=500)
        cut_in_behavior_sequence.add_child(accelerate)

        # lane_change: Perform the actual cut-in
        if self._direction == 'left':
            lane_change = LaneChange(
                self.other_actors[0], speed=None, direction='right', distance_same_lane=5, distance_other_lane=300)
            cut_in_behavior_sequence.add_child(lane_change)
        else: # self._direction == 'right'
            lane_change = LaneChange(
                self.other_actors[0], speed=None, direction='left', distance_same_lane=5, distance_other_lane=300)
            cut_in_behavior_sequence.add_child(lane_change)

        # endcondition: Drive for a defined distance after cut-in
        endcondition = DriveDistance(self.other_actors[0], 200)
        cut_in_behavior_sequence.add_child(endcondition)


        # --- Background traffic behavior (Parallel to the main cut-in logic) ---
        # All background vehicles will just keep driving straight.
        background_traffic_behavior = py_trees.composites.Parallel(
            "BackgroundTraffic", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL
        )
        # Ensure we only add behavior for actually spawned background vehicles
        if self.background_vehicles:
            initial_ego_speed_kph = CarlaDataProvider.get_velocity(self.ego_vehicles[0]).length() * 3.6 # Get ego's initial speed in km/h
            for i, b_vehicle in enumerate(self.background_vehicles):
                # Calculate a slightly varied speed for each background vehicle
                # Ensure a minimum reasonable speed for traffic flow
                b_speed = max(initial_ego_speed_kph * self._background_traffic_speed_variation, 20)
                background_traffic_behavior.add_child(
                    KeepVelocity(b_vehicle, target_velocity=b_speed)
                )

        # --- Overall behavior tree: Cut-in behavior and background traffic run in parallel ---
        # The scenario completes when the primary cut-in behavior finishes.
        root = py_trees.composites.Parallel("OverallScenario", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(cut_in_behavior_sequence)
        if self.background_vehicles: # Only add if there are background vehicles
            root.add_child(background_traffic_behavior)

        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria is created, which is later used in the parallel behavior tree.
        """
        criteria = []

        # Collision criteria for the ego vehicle with *any* other actor (including new background traffic)
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)

        return criteria

    def __del__(self):
        """
        Remove all actors after deletion.
        """
        self.remove_all_actors()
```