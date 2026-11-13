# AI programmatic-access permission sets

IAM Identity Center permission sets for AI tooling (for example `kiro-cli` or other agents) that gets temporary, approved access through [AWS TEAM](https://aws-samples.github.io/iam-identity-center-team/) (Temporary Elevated Access Management).

Each template creates one `AWS::SSO::PermissionSet` in the Identity Center instance you pass as `pInstanceArn`. Sessions default to one hour (`PT1H`) because elevation is meant to be short-lived. Account assignments are left to TEAM, so a set does nothing until a request is approved.

## Templates

| Template                         | Set name                  | Tier                       | Access                                                                                                             |
| -------------------------------- | ------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `ai-ps-readonly.yaml`            | `ai-readonly`             | read-only                  | `ReadOnlyAccess` + `ViewOnlyAccess`. The default starting point.                                                   |
| `ai-ps-bedrock-ro.yaml`          | `ai-bedrock-ro`           | read-only                  | `AmazonBedrockLimitedAccess` + `ReadOnlyAccess`.                                                                   |
| `ai-ps-network-ro.yaml`          | `ai-network-ro`           | read-only                  | VPC and Route 53 read, plus Transit Gateway, Direct Connect, ELB, Network Manager and Reachability Analyzer reads.  |
| `ai-ps-security-auditor.yaml`    | `ai-security-auditor`     | read-only                  | `SecurityAudit` + `ReadOnlyAccess` + Security Hub, GuardDuty, Config, Access Analyzer and Inspector reads.          |
| `ai-ps-cost-analyst.yaml`        | `ai-cost-analyst`         | read-only                  | Cost Explorer, CUR / Data Exports, Budgets, Savings Plans and pricing reads. Optional read of one report bucket.     |
| `ai-ps-infra-readonly-plan.yaml` | `ai-infra-readonly-plan`  | scoped-read-plus-plan      | `ReadOnlyAccess` + create and describe CloudFormation change sets. Executing change sets and stack changes are denied. |
| `ai-ps-data-analyst.yaml`        | `ai-data-analyst`         | scoped-read-plus-query     | Athena, Glue, Lake Formation and Redshift Data API queries + `ReadOnlyAccess`. Writes only to Athena result buckets. |
| `ai-ps-observability.yaml`       | `ai-observability`        | read-plus-diagnostic-write | Metrics, logs and traces read, Logs Insights and Live Tail, and dashboards whose names start with `pDashboardPrefix`. |
| `ai-ps-diagnostics-ssm.yaml`     | `ai-diagnostics-ssm`      | scoped-operate             | Session Manager shell and Run Command (`AWS-RunShellScript`, `AWS-RunPowerShellScript`) on instances + `ReadOnlyAccess`. |
| `ai-ps-bedrock-developer.yaml`   | `ai-bedrock-developer`    | builder-guardrailed        | `AmazonBedrockFullAccess` + `ReadOnlyAccess`, PassRole to Bedrock only, destructive-action Deny.                    |
| `ai-ps-sagemaker-ml.yaml`        | `ai-sagemaker-ml`         | builder-guardrailed        | `AmazonSageMakerFullAccess` + `ReadOnlyAccess`, PassRole to SageMaker only, destructive-action Deny.                |
| `ai-ps-developer-nonprod.yaml`   | `ai-developer-nonprod`    | builder-guardrailed        | `PowerUserAccess` + destructive-action Deny. Assign to non-production accounts only.                               |
| `ai-ps-operator-guardrailed.yaml`| `ai-operator-guardrailed` | operator-guardrailed       | `AdministratorAccess` + Deny on identity, organization, audit, KMS, data-store and network teardown.               |

## Deploying

Deploy each template in the management account (or the Identity Center delegated administrator account):

```bash
INSTANCE_ARN=$(aws sso-admin list-instances --query 'Instances[0].InstanceArn' --output text)

aws cloudformation deploy \
  --stack-name ai-ps-readonly \
  --template-file identity-center/templates/ai/ai-ps-readonly.yaml \
  --parameter-overrides pInstanceArn="$INSTANCE_ARN" pOwner=platform-team@example.com
```

Common parameters:

| Parameter             | Default                        | Purpose                                          |
| --------------------- | ------------------------------ | ------------------------------------------------ |
| `pInstanceArn`        | required                       | Identity Center instance ARN                     |
| `pSessionDuration`    | `PT1H`                         | Session length, `PT1H` to `PT12H`                |
| `pEnvironment`        | `all`                          | `Environment` tag                                |
| `pProject`            | `aws-ai-team-permission-sets`  | `Project` tag                                    |
| `pOwner`              | `owner@example.com`            | `Owner` tag: set it to the owning team's address |
| `pCostCenter`         | `unassigned`                   | `CostCenter` tag                                 |
| `pDataClassification` | varies by set                  | `DataClassification` tag                         |

Set-specific parameters: `pCostReportBucketName` (cost analyst), `pAthenaResultsBucketPattern` (data analyst) and `pDashboardPrefix` (observability).

## Before you grant these

- **Higher tiers can still escalate.** The guardrail sets use Deny lists. An `AdministratorAccess` or `PowerUserAccess` session can still reach privileged roles, for example by assuming a role that trusts the account or by passing a privileged role to EC2 or Lambda. Use SCPs and permissions boundaries in the target accounts as the real control, and keep TEAM approval for these sets.
- **`ReadOnlyAccess` reads data, not just configuration.** It includes actions such as `s3:GetObject`, DynamoDB item reads and `ssm:GetParameter`. Use `ai-readonly` with `ViewOnlyAccess` only, or add a Deny, if the tool should see metadata only.
- **`ai-diagnostics-ssm` is shell access.** Session Manager and `AWS-RunShellScript` run any command on any managed instance. Scope it with instance tags before you grant it to production accounts.
