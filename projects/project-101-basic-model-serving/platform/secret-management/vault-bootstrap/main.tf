terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "5.9.0"
    }
  }
}

provider "vault" {
  address = "http://127.0.0.1:8200"
}

locals {
  kubernetes_auth_role = jsondecode(file("${path.module}/kubernetes-auth-role.json"))
}

resource "vault_mount" "secret" {
  path = "secret"
  type = "kv"

  options = {
    version = "2"
  }
}

resource "vault_policy" "grafana_read" {
  name   = "grafana-read"
  policy = file("${path.module}/grafana-read.hcl")
}

resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
  path = "kubernetes"
}

resource "vault_kubernetes_auth_backend_config" "this" {
  backend         = vault_auth_backend.kubernetes.path
  kubernetes_host = "https://kubernetes.default.svc"
}

resource "vault_kubernetes_auth_backend_role" "grafana_eso" {
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "grafana-eso"
  bound_service_account_names      = local.kubernetes_auth_role.bound_service_account_names
  bound_service_account_namespaces = local.kubernetes_auth_role.bound_service_account_namespaces
  token_policies                   = local.kubernetes_auth_role.token_policies
  audience                         = local.kubernetes_auth_role.audience
  token_ttl                        = local.kubernetes_auth_role.token_ttl_seconds
  token_max_ttl                    = local.kubernetes_auth_role.token_max_ttl_seconds
}
