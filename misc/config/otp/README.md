# Jasmin OTP Bootstrap

Use these snippets to provision a minimal Jasmin topology for OTP traffic. Run
the commands through `jcli` (telnet on port 1401 inside the Jasmin container).

> Tip:	`docker compose -f docker-compose.otp.yml exec jasmin jcli` connects locally.

## 1. Create an OTP group and HTTP user

```
group -a
gid OTP
ok

user -a
username otp_api
password otp_api_secret
gid OTP
mt_messaging_cred authorization http_send yes
mt_messaging_cred authorization smpp_send no
mt_messaging_cred throughput 200
mt_messaging_cred filter MT True
mt_messaging_cred http_throughput 200
balance 100
early_decrement_balance_percent 50
ok
```

## 2. Create a UserFilter for routing

```
filter -a
type UserFilter
fid otp_api_filter
uid otp_api
ok
```

## 3. Add SMPP client connectors

```
smppccm -a
cid mtn_primary
host smpp.your-operator.local
port 2775
username YOUR_SMPP_SYSTEMID
password YOUR_SMPP_PASSWORD
bind transceiver
proto_version 3.4
log_level INFO
ok

smppccm -1 mtn_primary start   # start connector
```

Duplicate the block above to describe a secondary connector (e.g. `mtn_backup`) that can be used for failover/LCR later.

## 4. Provision MT routes

```
mtrouter -a
type StaticMTRoute
order 100
connector smppc(mtn_primary)
filters otp_api_filter
rate 0.02
ok

mtrouter -a
type DefaultRoute
order 1000
connector smppc(mtn_primary)
ok
```

Persist the configuration once everything is in place:

```
mtrouter -p
smppccm -p
user -p
group -p
filter -p
```

## 5. Configure DLR thrower target

Set the default DLR callback to the API gateway handler (already wired in `docker-compose.otp.yml`):

```
dlr-thrower -u
dlr_http_url http://api-gateway:8080/v1/webhooks/dlr
ok
```

The API gateway acknowledges each DLR with `ACK/Jasmin` and forwards the payload to the billing-service (`PATCH /v1/messages/{id}`), so message statuses stay in sync with operator feedback.

## 6. Monitoring

`docker-compose.otp.yml` now ships with Prometheus (`http://localhost:9090`) and Grafana (`http://localhost:3000`, admin/admin). Default dashboards live in `docker/grafana/dashboards` and include Jasmin throughput, RabbitMQ depth, and OTP API latency. Both the billing service and the API gateway expose `/metrics` thanks to the shared FastAPI instrumentor.

