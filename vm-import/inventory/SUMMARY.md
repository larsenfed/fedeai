# VM Inventory Summary

## VM connection
- Project: `agile-future-490715-j4`
- Zone: `us-central1-f`
- Instance: `instance-20260427-101420`
- Connect command:
  - `gcloud compute ssh --project=agile-future-490715-j4 --zone=us-central1-f instance-20260427-101420`

## Services discovered
- System service: `openclaw-gateway.service` in `/etc/systemd/system/`
- User service: `openclaw-gateway.service` in `/home/federico_larsen/.config/systemd/user/`

## Service status observed
- System service was crash-looping with:
  - `systemctl --user unavailable: Failed to connect to bus: Permission denied`
- User service was healthy and running.
- Action applied:
  - Disabled/stopped system-level service.
  - Kept user-level service running.

## Imported artifacts
- VM backup archive:
  - `vm-import/backups/openclaw-home-20260429-132118.tgz`
- Service inventory:
  - `vm-import/inventory/openclaw-gateway.service.txt`
  - `vm-import/inventory/openclaw-gateway.journal.txt`
