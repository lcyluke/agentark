# WeChat Video Delivery Reference

## How to send training demo videos to the user on WeChat

### Primary method: HTTP link (most reliable)
1. Deploy video to backend static directory (`data/training_animations/`)
2. Ensure backend is listening on `0.0.0.0` (not `127.0.0.1`)
3. Send URLs as plain text links: `http://<LAN_IP>:8000/training_animations/smash_demo.mp4`
4. User must be on same WiFi as the backend server

### Secondary method: MEDIA: syntax
- `MEDIA:/absolute/path/to/file.mp4` in the agent response
- Works inconsistently on WeChat — sometimes renders as clickable file, sometimes does not
- If user says "I can't click it", fall back to HTTP links

### What does NOT work
- GIF files embedded in WeChat messages (do not play inline)
- `send_message` with `target="origin"` — "origin" is not a valid target. Use `weixin:<chat_id>` instead

### WeChat mini-program video component
```wxml
<video src="http://192.168.0.103:8000/training_animations/smash_demo.mp4"
       controls autoplay loop
       object-fit="contain"
       show-mute-btn="{{true}}">
</video>
```
Note: For production release, the src must use HTTPS domain (not LAN IP).
For development, use LAN IP with DevTools' "不校验合法域名" setting enabled.
