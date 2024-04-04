# robo-face
EW Demo

Run on the device with

```

docker pull ghcr.io/slint-ui/slint/torizon-robo-demo-arm64-vivante:latest

docker run  --user=torizon -v /run/udev:/run/udev -v /dev:/dev -v /tmp:/tmp --device-cgroup-rule='c 199:* rmw' --device-cgroup-rule='c 226:* rmw' --device-cgroup-rule='c 13:* rmw' --device-cgroup-rule='c 4:* rmw' ghcr.io/slint-ui/slint/torizon-robo-demo-arm64-vivante
```
