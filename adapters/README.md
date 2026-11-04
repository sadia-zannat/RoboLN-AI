# Controller adapters

`http_device.py` is an executable Raspberry Pi / other Python controller bridge using only Python's standard library. Supply a measurement file from your real sensor producer. It checks `/api/device/status`, rejects an origin mismatch and uses TLS certificate verification. It never drives GPIO or invents readings. For software tests, enroll SIMULATION and use `--expected-mode SIMULATION`.

`esp32_micropython.py` is a transport adapter for an ESP32 MicroPython firmware that supplies a certificate-validating SSL context and calibrated sensor packets. It is syntax-checked but **not executed on an ESP32**. MicroPython TLS/API support varies by firmware. A board-specific sensor driver, Wi-Fi provisioning, time synchronization and validated CA trust store remain hardware integration tasks. No guessed pin or ADC calibration is shipped.

## Packet contract

POST `/api/device/telemetry`, `Authorization: Bearer <one-time device token>`:

- `packet_id`: unique string (1–64 letters, digits, `_` or `-`).
- `observed_at`: timezone-aware ISO 8601 timestamp from the device's synchronized clock.
- `measurements`: up to 32 `{name, value, unit}` records; finite numeric values.
- `event`: optional text, up to 500 characters. Plant images belong in Build evidence, not telemetry numbers.

Recognized units: `soil_moisture` `%`, `temperature` `degC`, `humidity` `%`, `battery_voltage` `V`, `irrigation_flow` `L/min`, `pump_state` `bool` (0 or 1), `uptime` `s`, `distance` `cm`, `battery_percent` `%`. Custom sensor names require explicit units; their physical validity is not certified. Raw ADC counts should use a distinct name such as `soil_moisture_raw` and unit `count`. Never label uncalibrated raw counts as moisture percent.

Timestamps must advance, be no more than 24h old or 30s ahead. Maximum one packet per second per device; 10,000 packets per device. Device origin is fixed at enrollment. Stale after 60 seconds by either observed or received time. Use the UI to revoke a lost token and enroll a replacement.

## Raspberry Pi / Python bridge

Set `ROBOLN_API_URL` and `ROBOLN_DEVICE_TOKEN` in the controller environment, then run:

```sh
python adapters/http_device.py --expected-mode LIVE_REAL --input /path/to/actual-sensor-packet.json
```

The input must come from your own sensor producer or an explicitly enrolled software simulation. There is no actuator executor. All reviewed control requests remain HOLD. Disconnecting power and independent hardware emergency stop must work without this service.
