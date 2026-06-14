# AutoDL REST API — Instance Management

## Discovery (2026-06-03)

AutoDL provides a **Container Instance Pro API** at `https://api.autodl.com`.

Requirements: personal real-name verification or enterprise certification.
API Key: generated from AutoDL console → Account Security → API Token.

## Endpoints (documented on autodl.com/docs/container-instance-pro/api/)

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/instance/create` | POST | Create a new instance (GPU type, image UUID, region) |
| `/api/instance/detail` | GET/POST | Get instance details |
| `/api/instance/status` | GET | Get instance status |
| `/api/instance/list` | GET | List all instances |
| `/api/instance/start` | POST | Start (power on) an instance |
| `/api/instance/stop` | POST | Stop (shutdown) an instance |
| `/api/instance/release` | POST | Release (terminate) an instance |
| `/api/image/save` | POST | Save instance as a custom image |

## Auth

Bearer token in header:
```bash
curl -H "Authorization: Bearer $AUTODL_API_TOKEN" \
  https://api.autodl.com/api/instance/list
```

## In-instance monitoring API (runs inside the container)

```python
# GPU/CPU/Memory metrics from within any container:
url = 'http://127.0.0.1:2022/autopanel/v1/api/monitor/current'
response = requests.get(url)
data = response.json()['data']
# data['cpu_usage'], data['memory_usage'], data['gpu_list'][0]['utilization']
```

## Implementation status

- API Token: NOT YET OBTAINED (user needs to generate in AutoDL console)
- Instance UUID: known from current SSH connection (connect.westb.seetacloud.com:16786)
- SSH-based shutdown: works now via `sshpass ssh root@host "shutdown -h now"`
- Full API integration: pending token acquisition
