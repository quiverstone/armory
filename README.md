# Quiverstone Armory

![review](https://github.com/quiverstone/armory/actions/workflows/trunk.yaml/badge.svg)
![standards](https://github.com/quiverstone/armory/actions/workflows/standards.yaml/badge.svg)

Public, ready-to-use AWS CloudFormation templates, policies and scripts from [Quiverstone](https://quiverstone.io).
They back our blog posts and are shared with consulting, professional services and SaaS customers.

Everything here is free to use under the [LICENSE](LICENSE). Review each template before you deploy it to your own accounts.

## Using the templates

Every file is published at the same path it has in this repo:

| Use                                   | URL                                                                     |
| ------------------------------------- | ----------------------------------------------------------------------- |
| Browser, `curl`, `wget`, blog links   | `https://armory.quiverstone.io/<path>`                                  |
| CloudFormation `TemplateURL`          | `https://s3.us-east-2.amazonaws.com/armory.quiverstone.io/<path>`       |
| AWS CLI                               | `s3://armory.quiverstone.io/<path>`                                     |

CloudFormation only accepts S3 URLs for `TemplateURL`, so use the S3 form there. Because the bucket name contains dots, always use the path-style S3 URL shown above, not `armory.quiverstone.io.s3.amazonaws.com`.

Example: deploy the IAM password policy straight from the bucket.

```bash
aws cloudformation create-stack --stack-name iam-password-policy \
  --template-url https://s3.us-east-2.amazonaws.com/armory.quiverstone.io/iam/templates/iam-settings-password-policy.yaml
```

Download the foundation template set:

```bash
curl -fsSL https://armory.quiverstone.io/foundation/scripts/foundation-sync-curl.sh | bash
```

## Hosting

- **Bucket:** `armory.quiverstone.io` in `us-east-2`, created from [`s3/templates/bucket-asset-hosting.yaml`](s3/templates/bucket-asset-hosting.yaml). It is public-read.
- **Domain:** `armory.quiverstone.io` is served by CloudFront in front of the bucket. Pass the distribution ID to the bucket stack as `pDistributionId`.
- **Publishing:** [`.github/workflows/sync-resources.yaml`](.github/workflows/sync-resources.yaml) syncs the repo to the bucket root. It assumes the role in the `PA_DELIVER` secret and invalidates CloudFront when the `CLOUDFRONT_DISTRIBUTION_ID` repository variable is set.

## Layout

Resources are grouped by AWS service, then by type:

```text
<service>/
├── templates/   CloudFormation templates (.yaml only)
├── scripts/     Python (boto3) and shell scripts
└── policies/    JSON policy documents (SCPs, RCPs)
```

A subfolder inside `templates/` groups the parts of one solution, for example `iam/templates/github/`.

| Directory        | Contents                                                                      |
| ---------------- | ----------------------------------------------------------------------------- |
| `account/`       | Account contact information                                                   |
| `automation/`    | Foundational GitHub automation                                                |
| `backup/`        | Organization AWS Backup KMS key                                               |
| `billing/`       | Cost and Usage Report bucket, budget alerts and reports                       |
| `cloudformation/`| Stack termination protection                                                  |
| `config/`        | AWS Config: organization and Control Tower deployments, cleanup script        |
| `control-tower/` | Control Tower KMS key, security event alerting                                |
| `ec2/`           | EBS encryption and public-sharing block, application ALB                      |
| `foundation/`    | Scripts that download the foundation template set                             |
| `identity-center/` | AI programmatic-access permission sets for AWS TEAM ([details](identity-center/templates/ai/README.md)) |
| `iam/`           | Password policy, CloudFormation and support roles, Access Analyzer, GitHub OIDC |
| `organizations/` | Organization foundation StackSet, SCPs and RCPs                               |
| `s3/`            | Shared asset and service log buckets                                          |
| `security-hub/`  | Delegation of security services to the audit account                         |
| `ssm/`           | SSM document public-sharing block                                             |
| `vpc/`           | Default VPC, endpoints, flow logs, default VPC removal                        |

## Template standards

Every template follows the Quiverstone CloudFormation standard, checked in CI:

- `.yaml` files only, with sections in the order `AWSTemplateFormatVersion`, `Description`, `Metadata`, `Parameters`, `Mappings`, `Conditions`, `Resources`, `Outputs`.
- Logical names are prefixed `p` (parameters), `r<ResourceType>` (resources), `c` (conditions), `o` (outputs), `m` (mappings) and `meta` (metadata).
- Every taggable resource carries the tag `GitHub: quiverstone/armory`, and every output is exported as `${AWS::StackName}-<oName>`.
- No hardcoded account IDs, secrets or open security groups. Values you need to change are parameters with constraints.

Scripts take their settings from environment variables, documented at the top of each script.

## Contributing

- Put new files in `<service>/templates/`, `<service>/scripts/` or `<service>/policies/`.
- Use the AWS service name in lowercase with hyphens (`control-tower`, `security-hub`).
- Nothing client-specific goes here: no account IDs, org IDs, client names or internal role names. That material belongs in the private `arsenal` repo.
- Follow [CONTRIBUTING.md](CONTRIBUTING.md) and run its checks before opening a pull request.
