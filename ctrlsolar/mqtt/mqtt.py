from typing import Optional, Callable, Any
import json
import paho.mqtt.client as mqtt
import logging
from ctrlsolar.mqtt.abstract import Sensor, Consumer

logger = logging.getLogger(__name__)
class Mqtt:
    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 1883,
    ):
        self.broker = host
        self.port = port
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.subscriptions = {}
        self.client.on_message = self._on_message
        if username is not None:
            self.client.username_pw_set(username, password)

    def connect(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = True):
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)

        self.client.publish(topic, payload, qos=qos, retain=retain)
        return

    def disconnect(self):
        self.client.disconnect()

    def subscribe(self, topic: str, callback: Callable[[str], None]):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
            self.client.subscribe(topic)

        self.subscriptions[topic].append(callback)

    def _on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode()
        for cb in self.subscriptions.get(topic, []):
            cb(payload)


class MqttSensor(Sensor):
    def __init__(
        self,
        topic: str,
        filter: Optional[list[Callable]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.topic = topic
        self.filter = filter
        mqtt = get_mqtt()
        mqtt.subscribe(topic, self._on_message)

    def _on_message(self, payload: str):
        if self.filter is not None:
            for cc in self.filter:
                payload = cc(payload)

        self._buffer.append(payload)
        return

    def get(self):
        if not self._buffer:
            return None

        message = self._buffer[-1]
        return message


class MqttConsumer(Consumer):
    def __init__(self, topic: str):
        self.mqtt = get_mqtt()
        self.topic = topic

    def set(self, value: str | int | float):
        self.mqtt.publish(self.topic, value)
        return

# Mqtt singleton to be used
_mqtt: Mqtt | None = None

def set_mqtt(client: Mqtt) -> None:
    global _mqtt
    if _mqtt is not None:
        raise RuntimeError("MQTT singleton already initialized!")
    
    _mqtt = client
    return 
    
def get_mqtt() -> Mqtt:
    if _mqtt is None:
        raise RuntimeError("MQTT singleton not initialized yet!")
    
    return _mqtt