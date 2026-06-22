# KIAN V2Ray — Infrastructure as Code (roadmap phase 7).
#
# Provisions a VPS (Hetzner Cloud here as a worked example) and runs the KIAN
# installer over cloud-init, so a server goes from zero → ready with one
# `terraform apply`. The provider block is intentionally swappable: the only
# KIAN-specific part is the cloud-init in `user_data`, which works on any
# Ubuntu host (DigitalOcean, Vultr, AWS, bare metal, …).
#
#   cd deploy/terraform
#   export TF_VAR_hcloud_token=...   # your provider token
#   export TF_VAR_kian_payload=...   # base64 KIAN_PAYLOAD from the web page/app
#   terraform init && terraform apply
#
# The payload is exactly what the web generator / Kv2m app produce — keys are
# still made client-side, never in Terraform state beyond the opaque blob.

terraform {
  required_version = ">= 1.3"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "kian_payload" {
  description = "Base64 KIAN_PAYLOAD from the web generator / Kv2m app"
  type        = string
  sensitive   = true
}

variable "server_name"  { type = string  default = "kian-v2ray" }
variable "server_type"  { type = string  default = "cx22" }       # 2 vCPU / 4GB
variable "location"     { type = string  default = "nbg1" }
variable "image"        { type = string  default = "ubuntu-24.04" }
variable "enable_panel" { type = bool    default = false }
variable "extra_env"    { type = string  default = "" }            # e.g. "KIAN_EXTRA_PROTOCOLS=1"

provider "hcloud" {
  token = var.hcloud_token
}

locals {
  panel_env = var.enable_panel ? "KIAN_PANEL=1 " : ""
  cloud_init = <<-EOT
    #cloud-config
    package_update: true
    runcmd:
      - export KIAN_PAYLOAD='${var.kian_payload}'
      - ${local.panel_env}${var.extra_env} bash -c 'curl -fsSL https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main/install.sh -o /tmp/k.sh && KIAN_PAYLOAD="$KIAN_PAYLOAD" ${local.panel_env}${var.extra_env} bash /tmp/k.sh'
  EOT
}

resource "hcloud_server" "kian" {
  name        = var.server_name
  server_type = var.server_type
  location    = var.location
  image       = var.image
  user_data   = local.cloud_init

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
}

output "server_ip" {
  description = "Public IPv4 — use this as the server IP when generating configs"
  value       = hcloud_server.kian.ipv4_address
}

output "next_steps" {
  value = "Server up at ${hcloud_server.kian.ipv4_address}. The installer ran via cloud-init; SSH in and run `kian-v2ray status` to verify."
}
