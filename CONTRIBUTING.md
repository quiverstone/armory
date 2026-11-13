# Contributing to Armory

Every pull request runs [`.github/workflows/standards.yaml`](.github/workflows/standards.yaml): cfn-lint, the template standards check, ruff and shellcheck. Run the same checks locally before you push:

```bash
pip install cfn-lint ruff
git ls-files -z '*/templates/*.yaml' | xargs -0 cfn-lint --
python .github/scripts/check-cfn-standards.py --repo armory
ruff check --config .trunk/configs/ruff.toml . && ruff format --check --config .trunk/configs/ruff.toml .
git ls-files -z '*.sh' | xargs -0 shellcheck
```

## CloudFormation templates

- **Files** are `.yaml` (never `.yml`, `.json` or `.template`), named in lowercase with hyphens, under `<service>/templates/`.
- **Section order:** `AWSTemplateFormatVersion`, `Description`, `Metadata`, `Parameters`, `Mappings`, `Conditions`, `Resources`, `Outputs`.
- **Logical names** use a type prefix and PascalCase:

  | Section    | Prefix | Example                                                   |
  | ---------- | ------ | --------------------------------------------------------- |
  | Parameters | `p`    | `pVpcCidr`                                                |
  | Resources  | `r`    | `rS3BucketCentralLog` (`r<ResourceType><Description>`)    |
  | Conditions | `c`    | `cCreateKmsKey`                                           |
  | Outputs    | `o`    | `oBucketArn`                                              |
  | Mappings   | `m`    | `mRegionMap`                                              |
  | Metadata   | `meta` | `metaTemplateInfo`                                        |

- **Parameters** have a `Description`, a `Default` where one is safe, and `AllowedValues` or `AllowedPattern` with a `ConstraintDescription`. Nothing environment-specific is hardcoded: account IDs, org IDs, CIDRs, emails and names are parameters (or SSM parameters such as `/automation/reference/org/account/Audit`).
- **Resources** that support tags carry `GitHub: quiverstone/armory`. Stateful resources (S3 buckets, KMS keys, DynamoDB tables, RDS, ElastiCache, ECR) set `DeletionPolicy` and `UpdateReplacePolicy`. Use `DependsOn` only when CloudFormation cannot infer the order.
- **Outputs** have a `Description` and `Export.Name: !Sub ${AWS::StackName}-<oName>`.
- **IAM:** least privilege. No `Policies` on roles and no `AWS::IAM::Policy`: use `AWS::IAM::ManagedPolicy` or AWS managed policies. Add explicit `Deny` statements for guardrails (for example `aws:SecureTransport` on bucket policies). Use `${AWS::Partition}` in ARNs.
- **Secrets** are never parameters or literals. Generate them with `AWS::SecretsManager::Secret` `GenerateSecretString` and reference them with `{{resolve:secretsmanager:...}}`, or read them from Parameter Store.
- **Network:** security group rules name specific ports and source CIDRs or security groups. `0.0.0.0/0` is only acceptable as a parameter default for public load balancers, never for databases or caches.
- **Renaming a logical ID replaces the resource** on the next stack update, and retained resources are left behind. Plan the migration before you rename.

## Scripts

- **Python 3.11+**, formatted and linted with ruff (`.trunk/configs/ruff.toml`). Use boto3 paginators, catch `botocore.exceptions.ClientError`, and never use `eval`.
- **Settings come from environment variables:** optional ones with a default (`os.environ.get("ROLE_NAME", "OrganizationAccountAccessRole")`), required ones with `os.environ["NAME"]`, and lists or structured data from a file named by a variable (`ACCOUNTS_FILE`, `ALTERNATE_CONTACTS_FILE`). Commit a `*.example.json` next to a script that needs one, and list the variables in the script's docstring.
- **Shell scripts** start with `#!/usr/bin/env bash` and `set -euo pipefail`, quote every expansion, and pass shellcheck. Destructive scripts show what they will change and ask for confirmation first.
- **Never commit credentials**, account lists or client data. Trunk runs trufflehog on every pull request.
