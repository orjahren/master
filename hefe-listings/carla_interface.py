import carla

CARLA_HOST = "carla"
CARLA_PORT = 2000


def get_carla_is_up() -> bool:
    """
    Check if the CARLA simulator is up and running.
    This function attempts to connect to the CARLA server and returns True if successful, otherwise False.
    """
    print("Running carla integration check to see if it is up...")
    try:
        client = carla.Client(CARLA_HOST, CARLA_PORT)
        client.get_world()
        return True
    except Exception as e:
        print(f"CARLA connection failed: {e}")
        return False


def spawn_vehicle(vehicle_type: str, location: carla.Location) -> carla.Vehicle:
    """
    Spawn a vehicle in the CARLA world at the specified location.

    :param vehicle_type: The type of vehicle to spawn (e.g., 'vehicle.tesla.model3').
    :param location: The location where the vehicle should be spawned.
    :return: The spawned vehicle object.
    """
    client = carla.Client(CARLA_HOST, CARLA_PORT)
    world = client.get_world()

    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.filter(vehicle_type)[0]

    vehicle = world.spawn_actor(vehicle_bp, carla.Transform(location))
    return vehicle


def get_vehicle_location(vehicle: carla.Vehicle) -> carla.Location:
    """
    Get the current location of a vehicle in the CARLA world.

    :param vehicle: The vehicle object.
    :return: The current location of the vehicle.
    """
    return vehicle.get_location()


def spawn_some_vehicles(vehicle_types: list, locations: list) -> list:
    """
    Spawn multiple vehicles in the CARLA world at specified locations.

    :param vehicle_types: A list of vehicle types to spawn.
    :param locations: A list of carla.Location objects where vehicles should be spawned.
    :return: A list of spawned vehicle objects.
    """
    if len(vehicle_types) != len(locations):
        raise ValueError(
            "vehicle_types and locations must have the same length.")

    vehicles = []
    for vehicle_type, location in zip(vehicle_types, locations):
        vehicle = spawn_vehicle(vehicle_type, location)
        vehicles.append(vehicle)

    return vehicles


def test_spawn_some_vehicles():
    vehicle_types = ['vehicle.tesla.model3', 'vehicle.audi.a2']
    locations = [carla.Location(x=0, y=0, z=0), carla.Location(x=1, y=1, z=0)]
    vehicles = spawn_some_vehicles(vehicle_types, locations)
    assert len(vehicles) == 2
    assert get_vehicle_location(vehicles[0]) == locations[0]
    assert get_vehicle_location(vehicles[1]) == locations[1]


def set_map(map_name: str):
    """
    Set the CARLA world to a specific map.

    :param map_name: The name of the map to set (e.g., 'Town01').
    """
    client = carla.Client(CARLA_HOST, CARLA_PORT)
    world = client.get_world()
    world = client.load_world(map_name)
    return world


if __name__ == "__main__":
    if get_carla_is_up():
        print("CARLA is up and running.")
        # test_spawn_some_vehicles()
    else:
        print("CARLA is not reachable.")
