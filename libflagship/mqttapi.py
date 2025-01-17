import paho.mqtt.client as mqtt
import paho.mqtt
import ssl

from libflagship.util import enhex
from libflagship.mqtt import MqttMsg

class AnkerMQTTBaseClient:

    def __init__(self, printersn, mqtt, key):
        self._mqtt = mqtt
        self._printersn = printersn
        self._key = key
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_message = self._on_message
        self._mqtt.on_publish = self.on_publish

    # internal function
    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            raise IOError(f"could not connect: rc={rc} ({paho.mqtt.client.error_string(rc)})")
        mqtt = self._mqtt
        mqtt.subscribe(f"/phone/maker/{self.sn}/notice")
        mqtt.subscribe(f"/phone/maker/{self.sn}/command/reply")
        mqtt.subscribe(f"/phone/maker/{self.sn}/query/reply")
        self.on_connect(client, userdata, flags)

    # public api: override in subclass (if needed)
    def on_connect(self, client, userdata, flags):
        pass


    # public api: override in subclass (if needed)
    def on_publish(self, client, userdata, result):
        pass


    # internal function
    def _on_message(self, client, userdata, msg):
        pkt, tail = MqttMsg.parse(msg.payload, key=self._key)
        self.on_message(client, userdata, msg, pkt, tail)

    # public api: override in subclass
    def on_message(self, client, userdata, pkt, tail):
        raise NotImplemented


    @classmethod
    def login(cls, printersn, username, password, key, ca_certs="ankermake-mqtt.crt", verify=True):
        client = mqtt.Client()

        if verify:
            client.tls_set(ca_certs=ca_certs)
        else:
            client.tls_set(ca_certs=ca_certs, cert_reqs=ssl.CERT_NONE)
            client.tls_insecure_set(True)

        client.username_pw_set(username, password)

        return cls(printersn, client, key)

    def connect(self, server, port=8789, timeout=60):
        self._mqtt.connect(server, port, timeout)

    @property
    def sn(self):
        return self._printersn

    def send(client, topic, msg):
        raise NotImplemented

    def query(self, msg):
        return self.send(f"/device/maker/{self.sn}/query", msg)

    def command(self, msg):
        return self.send(f"/device/maker/{self.sn}/command", msg)

    def loop(self):
        self._mqtt.loop_forever()
