# SOPS/AGE Secrets Rotation Runbook

## Scope

Root owns the SOPS/AGE policy and deployment secret contract. Real encrypted secrets are environment-owned and must not be committed as plaintext.

## Required Files

- `.sops.yaml`
- `config/staging/secrets.yaml` encrypted with SOPS
- `config/prod/secrets.yaml` encrypted with SOPS
- `config/staging/secrets.example.yaml`
- `config/prod/secrets.example.yaml`

## Required GitHub Secrets

- `SOPS_AGE_KEY`: private AGE key used by deployment and migration workflows

## Generate an AGE Key

```powershell
age-keygen -o age.key
```

Copy the public key into `.sops.yaml` for the target environment. Store the private key in the GitHub environment secret `SOPS_AGE_KEY`.

## Create Encrypted Environment Secrets

```powershell
Copy-Item config/staging/secrets.example.yaml config/staging/secrets.yaml
sops --encrypt --in-place config/staging/secrets.yaml

Copy-Item config/prod/secrets.example.yaml config/prod/secrets.yaml
sops --encrypt --in-place config/prod/secrets.yaml
```

## Rotate the AGE Key

1. Add the new public key to `.sops.yaml`.
2. Re-encrypt each environment file.
3. Update `SOPS_AGE_KEY` in the matching GitHub environment.
4. Run deployment workflow dry-run validation.
5. Remove the old public key from `.sops.yaml` after the new key is verified.

```powershell
sops updatekeys config/staging/secrets.yaml
sops updatekeys config/prod/secrets.yaml
```

## Emergency Recovery

If the private key is lost, recover from a secure backup of the AGE private key. If no backup exists, recreate secrets from the owning secret managers or operators, encrypt them with a new AGE key, and rotate all affected credentials.

## Verification

```powershell
sops --decrypt config/staging/secrets.yaml > $null
sops --decrypt config/prod/secrets.yaml > $null
```
