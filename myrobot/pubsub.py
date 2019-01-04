import paho.mqtt.client as mqtt

DEFAULT_MQTT_SERVER = "erik-Aspire-XC-705"


class PubSubClient:
    """Create a pubsub client that can send information over MQTT protocol.
    It is assumed that an MQTT-capable server is running to receive the data."""
    def __init__(self, server_host=DEFAULT_MQTT_SERVER):
        self.client = mqtt.Client()
        self.client.connect(server_host)

    def send_location(self, x, y):
        """Publishes location."""
        self.client.publish('location', "%f,%f" % (x, y))

    def send_free_space(self, distance):
        """Publishes free-space (as measured by e.g. sonar)."""
        self.client.publish('free_space', str(distance))
