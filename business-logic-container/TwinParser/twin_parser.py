import logging
from shapely.geometry import Point, Polygon

class Roi:
    def __init__(self, message) -> None:
        self.label = message["label"]
        self.color = message["color"]
        self.coordinates=[]
        for (x,y) in message["coordinates"]:
            self.coordinates.append((x,y))
        self.polygon = Polygon(self.coordinates)

    def __str__(self):
        return f"ROI ({self.label}, {self.color}): {self.coordinates}"

    def contains(self, pt):
        x, y = pt
        return self.polygon.contains(Point(x,y))

class Sensor:
    # TODO: Need to handle 'type' and 'subtype'. For now, we are assuming that we will
    # only get endpoint for RTSP streams
    def __init__(self) -> None:
        self.name = ""
        self.sensor_type = ""
        self.subtype = ""
        self.endpoint = ""
        self.regions_of_interest = None

    def from_json(self, message):
        self.name = message["name"]
        self.sensor_type = message["kind"]["type"]
        self.subtype = message["kind"]["subtype"]
        self.endpoint = message["endpoint"]
        self.regions_of_interest = [Roi(msg) for msg in message["regionsOfInterest"]]

class Twin:
    sensor_count = 0
    sensors= {}
    _instance = None

    @classmethod
    def get_instance(cls):
        """Static access method. """
        if cls._instance is None:
            logging.info("Creating new instance of Twin()")
            cls._instance = cls.__new__(cls)
        return cls._instance

    def parse_sensors(self, ada_skill):
        sensors = ada_skill["sensors"]
        self.sensor_count = len(sensors)
        self.sensors.clear()

        print(f"Number of sensors: {self.sensor_count}")
        if self.sensor_count < 1:
            logging.error(f"There must be at least one sensor defined")
        else:
            # Parse the sensors element
            logging.info("Parsing sensors")
            for i in range(self.sensor_count):
                sensor = Sensor()
                sensor.from_json(sensors[i])
                self.sensors[sensor.name] = sensor
