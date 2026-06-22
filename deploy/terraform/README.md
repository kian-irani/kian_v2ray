# KIAN V2Ray — Terraform (Infrastructure as Code)

Provision a VPS **and** run the KIAN installer in one `terraform apply`. The
example uses **Hetzner Cloud**, but the only KIAN-specific part is the cloud-init
in `user_data` — swap the `provider` + `resource` blocks for DigitalOcean, Vultr,
AWS EC2, etc. and keep the same `kian_payload`.

## Usage

```bash
cd deploy/terraform

# 1) get the install payload from the web generator or the Kv2m app
#    (the base64 string after `export KIAN_PAYLOAD=` in the install command)
export TF_VAR_kian_payload='PASTE_BASE64_PAYLOAD'

# 2) your provider token
export TF_VAR_hcloud_token='YOUR_HETZNER_TOKEN'

# 3) (optional) enable the web panel / extra protocols
export TF_VAR_enable_panel=true
export TF_VAR_extra_env='KIAN_EXTRA_PROTOCOLS=1'

terraform init
terraform apply
```

`terraform output server_ip` prints the new server's IP. The installer runs
automatically via cloud-init; SSH in and `kian-v2ray status` to confirm.

## Privacy note

Keys are still generated **client-side** (in the web page / app) — Terraform only
passes the opaque base64 payload through. Keep your `*.tfstate` private (it holds
the payload + provider token); use a remote backend with encryption for teams.

## Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `hcloud_token` | — | Provider API token (sensitive) |
| `kian_payload` | — | Base64 payload from the generator (sensitive) |
| `server_type` | `cx22` | 2 vCPU / 4 GB |
| `location` | `nbg1` | Hetzner region |
| `image` | `ubuntu-24.04` | Any recent Ubuntu |
| `enable_panel` | `false` | Deploy the web panel too |
| `extra_env` | `""` | e.g. `KIAN_EXTRA_PROTOCOLS=1` |
