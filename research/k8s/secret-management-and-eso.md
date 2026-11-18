# Kubernetes Secret Management and ESO Feasibility

**Researched:** 2026-11-17
**Scope:** Grafana credentials for `project-101-basic-model-serving`, with Docker Desktop Kubernetes as the currently reachable cluster and Azure/AKS as a possible future target.

## Summary

For the current Grafana deployment, the simplest fit is a SOPS-encrypted Kubernetes Secret manifest using age. It keeps the resource declarative and allows the encrypted manifest to live in Git without committing a plaintext password.

External Secrets Operator (ESO) is feasible, but it does not replace a secret provider: ESO synchronizes values from a provider into ordinary Kubernetes Secrets. For a future AKS deployment, Azure Key Vault with Microsoft Entra Workload Identity is the strongest fit if Azure is the target platform. For Docker Desktop alone, adopting ESO just to supply one Grafana password adds an operator and a provider dependency without eliminating the need for a secure bootstrap identity.

No credentials were generated, no provider was selected, and no cluster resources were changed as part of this research.

## Current project context

- Grafana expects a Secret named `grafana-credentials` with keys `admin-user` and `admin-password`; see [`grafana.yaml`](../../projects/project-101-basic-model-serving/monitoring/kubernetes/grafana/grafana.yaml).
- The monitoring Kustomize configuration generates Grafana provisioning ConfigMaps but does not currently define that Secret; see [`monitoring/kustomization.yaml`](../../projects/project-101-basic-model-serving/monitoring/kustomization.yaml).
- The deployment guide currently instructs users to create the Grafana Secret imperatively before applying Kustomize; see [Step 7: Deploy Grafana](../../projects/project-101-basic-model-serving/docs/DEPLOYMENT.md). That instruction should be replaced if the project adopts a declarative-only secret workflow.
- Kubernetes Secret `data` values are base64 encoded, not encrypted. Kubernetes documents that Secrets are stored unencrypted in etcd by default unless encryption at rest is configured; see [Kubernetes Secret good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/) and [Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/).

## ESO architecture and implications

ESO adds Kubernetes custom resources:

1. A `SecretStore` describes how ESO authenticates to a provider.
2. An `ExternalSecret` selects provider values and maps them to a Kubernetes Secret.
3. ESO reconciles that native Secret as provider values change.

ESO itself runs as an in-cluster deployment and depends on its CustomResourceDefinitions. Its installation can be managed declaratively, but it is an additional cluster component to install and maintain; see the [ESO getting started guide](https://external-secrets.io/latest/introduction/getting-started/).

The application can continue to reference `grafana-credentials` unchanged. The ESO [API overview](https://external-secrets.io/latest/introduction/overview/) notes that ESO creates ordinary Kubernetes Secrets, that `SecretStore` credentials may themselves be referenced from Kubernetes Secrets, and that the controller has elevated privileges. Use least-privilege provider access and restrict who can create or use stores and external secrets.

ESO therefore improves centralized sourcing, rotation, and reconciliation; it does **not** by itself encrypt Kubernetes Secret data in etcd or remove the final Secret from the cluster.

## Provider options

| Provider | Feasibility and fit |
|---|---|
| **Azure Key Vault** | Best fit if the eventual workload runs on AKS. ESO supports Key Vault through `SecretStore`/`ClusterSecretStore`. Its provider documentation recommends Workload Identity; on AKS this avoids storing a long-lived Azure client secret in Kubernetes. AKS Standard requires the OIDC issuer and Workload Identity to be enabled and configured. On Docker Desktop, AKS federation is not automatically available; ESO also supports service-principal authentication, but that requires a client secret or certificate bootstrap credential. Sources: [ESO Azure Key Vault provider](https://external-secrets.io/latest/provider/azure-key-vault/) and [AKS Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview). |
| **HashiCorp Vault** | A viable cross-platform learning provider. ESO supports Vault KV v1/v2 and multiple authentication methods, including Kubernetes-native auth and AppRole; see [ESO Vault provider docs](https://external-secrets.io/latest/provider/hashicorp-vault/). A local Vault instance can exercise the ESO flow with Docker Desktop, but adds Vault deployment, storage, bootstrap/authentication, and lifecycle work. Vault's dev server is explicitly for experimentation, stores data in memory, and uses insecure defaults; see [Vault dev server mode](https://developer.hashicorp.com/vault/docs/concepts/dev-server). |
| **AWS Secrets Manager / Google Cloud Secret Manager** | Good choices when the organization already operates in those clouds. ESO has dedicated [AWS](https://external-secrets.io/latest/provider/aws-secrets-manager/) and [Google Cloud](https://external-secrets.io/latest/provider/google-secrets-manager/) providers and documents identity-based auth patterns. They add cloud IAM and identity configuration and are not an obvious fit without an existing AWS/GCP environment. |
| **Kubernetes Secret provider** | ESO can read from a local or remote Kubernetes cluster; see [ESO Kubernetes provider docs](https://external-secrets.io/latest/provider/kubernetes/). Reading a Secret from another namespace or cluster can support controlled synchronization, but using it as the source for this same cluster does not create an external trust boundary or remove the source Secret. It is not a meaningful secret-manager replacement here. |
| **Other hosted providers** | ESO also integrates with third-party secret-management services. Prefer a provider already approved and operated by the team rather than introducing a new service just for Grafana. The [ESO overview](https://external-secrets.io/latest/introduction/overview/) describes the provider/store abstraction. |

### Azure Key Vault with AKS

For a production AKS path, the intended design would be:

- Store the Grafana admin credential in Azure Key Vault.
- Give ESO a narrowly scoped Microsoft Entra identity using AKS Workload Identity and grant only the needed Key Vault read permission.
- Define the Kubernetes service account, `SecretStore`, and `ExternalSecret` declaratively. The `ExternalSecret` would materialize `grafana-credentials` in `monitoring`.
- Define Azure-side identity, federation, and role assignments with the team's approved declarative IaC (for example Terraform or Bicep).

ESO labels Workload Identity as its recommended Azure Key Vault authentication method. AKS Workload Identity uses the cluster's OIDC issuer and federated identity; AKS Standard clusters need this configured. This avoids an Azure client secret in the workload, although the synced Grafana Secret still exists in Kubernetes and remains subject to cluster RBAC and encryption-at-rest settings.

### Docker Desktop

Docker Desktop is suitable for trying ESO, but does not provide AKS's Entra federation automatically. The documented service-principal method can connect to Key Vault, but its client secret/certificate has to be provided to ESO through a Kubernetes Secret. That reintroduces a bootstrap credential and weakens the benefit for a single local Grafana password.

If the goal is specifically to learn ESO locally, a lab Vault KV store is a plausible provider. Keep its credentials and persistence explicitly lab-scoped, use declarative manifests, and do not treat a local Vault development configuration as production security. If the goal is simply to deploy Grafana locally, SOPS + age is less infrastructure.

## Options for the Grafana credential

### Recommended now: SOPS + age

Define a Kubernetes Secret manifest with the required name, namespace, and keys; encrypt the sensitive fields with SOPS and age; commit only the encrypted file; keep the age private key outside the repository. Decrypt the file to standard input and use `kubectl apply -f -`, then apply the monitoring Kustomize configuration. This remains a declarative Kubernetes apply flow without an ESO controller or plaintext Secret committed to Git.

SOPS supports YAML and age encryption; see the [SOPS documentation](https://getsops.io/docs/). SOPS protects the repository copy, not the Secret after it is stored by Kubernetes, so cluster encryption at rest and least-privilege RBAC remain separate requirements.

### Simpler local-only alternative: Kustomize `secretGenerator`

Kustomize can generate a Secret from a file, literal, or environment file; see [Kustomize `secretGenerator`](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/secretgenerator/). A gitignored local credentials file is convenient for one developer, but it leaves the value in plaintext on disk and makes deployments dependent on local state. It is less suitable when the checked-in configuration should be the reproducible source of truth.

## Recommendation

1. **For Docker Desktop and this single Grafana credential:** use SOPS + age. Do not introduce ESO unless the goal is to learn or validate ESO.
2. **For a future AKS deployment:** use Azure Key Vault with ESO and Microsoft Entra Workload Identity, with Azure resources provisioned declaratively.
3. **For an ESO learning exercise on Docker Desktop:** use a dedicated lab Vault KV provider, or Azure Key Vault with a securely managed service-principal bootstrap credential. The Vault option is cloud-independent but brings extra local infrastructure; the Azure option is closer to the AKS target but requires the bootstrap secret.
4. Do not use the same-cluster Kubernetes Secret provider as the backing store for this credential; it adds synchronization, not meaningful secret isolation.

Provider selection and deployment are pending user approval. Any ESO controller, provider identity, SecretStore, ExternalSecret, or Grafana Secret changes should be represented declaratively and reviewed before application.

## Sources

- [Kubernetes Secrets good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [Kubernetes encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [SOPS documentation](https://getsops.io/docs/)
- [Kustomize Secret generator](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/secretgenerator/)
- [External Secrets Operator API overview](https://external-secrets.io/latest/introduction/overview/)
- [ESO getting started and installation](https://external-secrets.io/latest/introduction/getting-started/)
- [ESO: Azure Key Vault](https://external-secrets.io/latest/provider/azure-key-vault/)
- [ESO: HashiCorp Vault](https://external-secrets.io/latest/provider/hashicorp-vault/)
- [Vault dev server mode](https://developer.hashicorp.com/vault/docs/concepts/dev-server)
- [ESO: AWS Secrets Manager](https://external-secrets.io/latest/provider/aws-secrets-manager/)
- [ESO: Google Cloud Secret Manager](https://external-secrets.io/latest/provider/google-secrets-manager/)
- [ESO: Kubernetes provider](https://external-secrets.io/latest/provider/kubernetes/)
- [Microsoft Entra Workload ID on AKS](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
