# Adding Commands & New Technologies

## Table of Contents

1. [Adding a Single Command](#1-adding-a-single-command)
2. [Command Schema Reference](#2-command-schema-reference)
3. [Adding Multiple Commands](#3-adding-multiple-commands)
4. [Adding a New Technology](#4-adding-a-new-technology)
5. [User Custom Commands](#5-user-custom-commands)
6. [Writing Good Query Examples](#6-writing-good-query-examples)
7. [Risk Classification Guide](#7-risk-classification-guide)
8. [Validation & Testing](#8-validation--testing)
9. [Re-indexing After Changes](#9-re-indexing-after-changes)
10. [Full Example: Adding AWS CLI](#10-full-example-adding-aws-cli)

---

## 1. Adding a Single Command

Open the YAML file for the technology under `knowledge/<technology>/commands.yaml` and append a new entry:

```yaml
- id: kubernetes-get-events
  technology: kubernetes
  category: troubleshooting
  name: Get cluster events
  intent: get_events
  command: kubectl get events --sort-by=.lastTimestamp
  description: >
    List recent cluster events sorted by timestamp.
    Useful for troubleshooting pod startup failures and scheduling issues.
  tags:
    - kubernetes
    - events
    - troubleshooting
    - debug
  aliases:
    - show kubernetes events
    - cluster events
    - recent events
    - k8s events
  examples:
    - query: "show me recent kubernetes events"
    - query: "what events happened in the cluster"
    - query: "k8s events sorted by time"
  risk: safe
  documentation:
    url: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_get/
  verified_at: "2026-08-01"
```

That's it. After adding, [re-index](#9-re-indexing-after-changes) to make it searchable.

---

## 2. Command Schema Reference

Every command entry **must** have these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique identifier. Format: `<technology>-<short-description>` |
| `technology` | string | ✅ | Technology name (lowercase): `kubernetes`, `docker`, `git`, etc. |
| `category` | string | ✅ | Grouping within the technology: `pods`, `deployments`, `branches`, etc. |
| `name` | string | ✅ | Human-readable name shown in results |
| `intent` | string | ✅ | Machine-readable intent slug: `list_pods`, `restart_deployment` |
| `command` | string | ✅ | The actual shell command. Use `<placeholder>` for variables |
| `description` | string | ✅ | What the command does. 1-3 sentences |
| `tags` | list[string] | ✅ | Keywords for search matching (3-8 tags) |
| `aliases` | list[string] | ✅ | Natural language ways to ask for this command (3-8) |
| `examples` | list[object] | ✅ | Query examples: `- query: "how do I ..."` (2-5) |
| `risk` | string | ✅ | One of: `safe`, `warning`, `dangerous` |
| `documentation` | object | ✅ | `url:` pointing to official docs |
| `verified_at` | string | ✅ | Date verified against official docs: `"YYYY-MM-DD"` |

### Field Details

#### `id`
- Must be globally unique across all technologies
- Format: `<technology>-<short-kebab-description>`
- Examples: `kubernetes-get-pods`, `docker-logs`, `git-reset-soft`

#### `command`
- Use `<placeholder>` for user-supplied values
- Common placeholders: `<pod>`, `<deployment>`, `<container>`, `<namespace>`, `<file>`, `<path>`, `<port>`, `<user>`, `<host>`, `<branch>`, `<image>`, `<service>`, `<topic>`
- If the command contains colons or special YAML characters, wrap in quotes:
  ```yaml
  command: 'curl -H "Content-Type: application/json" <url>'
  ```

#### `intent`
- Use snake_case
- Should describe the action: `list_pods`, `restart_deployment`, `undo_commit`
- Multiple commands can share the same intent (e.g., several ways to list pods)

#### `risk`
- `safe` — Read-only, no side effects (get, list, describe, logs, status)
- `warning` — Modifies state but recoverable (apply, restart, stop, install)
- `dangerous` — Destructive or irreversible (delete namespace, force push, destroy)

---

## 3. Adding Multiple Commands

Just append more entries to the same YAML file. Each entry starts with `- id:`:

```yaml
# ... existing commands above ...

- id: docker-inspect-container
  technology: docker
  category: containers
  name: Inspect container details
  intent: inspect_container
  command: docker inspect <container>
  description: >
    Display detailed low-level information about a container
    including networking, mounts, and configuration.
  tags: [docker, inspect, container, details, config]
  aliases:
    - inspect container
    - container details
    - docker inspect
  examples:
    - query: "show container configuration details"
    - query: "inspect a docker container"
  risk: safe
  documentation:
    url: https://docs.docker.com/reference/cli/docker/inspect/
  verified_at: "2026-08-01"

- id: docker-cp-to-container
  technology: docker
  category: containers
  name: Copy file to container
  intent: copy_to_container
  command: docker cp <local_path> <container>:<container_path>
  description: >
    Copy a file or directory from the local filesystem into a running container.
  tags: [docker, copy, cp, file, container, transfer]
  aliases:
    - copy file to container
    - docker cp into container
  examples:
    - query: "copy a file into a docker container"
    - query: "transfer file to running container"
  risk: safe
  documentation:
    url: https://docs.docker.com/reference/cli/docker/container/cp/
  verified_at: "2026-08-01"
```

---

## 4. Adding a New Technology

### Step 1: Create the directory and YAML file

```bash
mkdir -p knowledge/ansible
touch knowledge/ansible/commands.yaml
```

### Step 2: Add commands to the YAML file

Start with a comment header and your first commands:

```yaml
# AlchemyCLI AI - Ansible Commands

- id: ansible-ping
  technology: ansible
  category: basics
  name: Ping all hosts
  intent: ping_hosts
  command: ansible all -m ping
  description: >
    Test connectivity to all hosts in the inventory using the ping module.
  tags: [ansible, ping, connectivity, test, hosts]
  aliases:
    - ansible ping
    - test ansible connectivity
    - ping all hosts
    - check if hosts are reachable
  examples:
    - query: "ping all ansible hosts"
    - query: "test connectivity to ansible hosts"
    - query: "check if my servers are reachable"
  risk: safe
  documentation:
    url: https://docs.ansible.com/ansible/latest/cli/ansible.html
  verified_at: "2026-08-01"

- id: ansible-playbook-run
  technology: ansible
  category: playbooks
  name: Run a playbook
  intent: run_playbook
  command: ansible-playbook <playbook>.yml
  description: >
    Execute an Ansible playbook against the configured inventory.
  tags: [ansible, playbook, run, execute, deploy]
  aliases:
    - run playbook
    - execute playbook
    - ansible-playbook
    - run ansible playbook
  examples:
    - query: "run an ansible playbook"
    - query: "execute a playbook"
    - query: "how do I run a playbook"
  risk: warning
  documentation:
    url: https://docs.ansible.com/ansible/latest/cli/ansible-playbook.html
  verified_at: "2026-08-01"

# Add 20-50+ more commands covering the technology thoroughly...
```

### Step 3: Register technology aliases in preprocessing

Edit `ml/src/alchemy_ml/preprocessing.py` and add entries to `TECHNOLOGY_ALIASES`:

```python
TECHNOLOGY_ALIASES: dict[str, str] = {
    # ... existing entries ...

    # Ansible
    "ansible": "ansible",
    "ansible-playbook": "ansible",
    "ansible-galaxy": "ansible",
    "ansible-vault": "ansible",
    "playbook": "ansible",
    "inventory": "ansible",
}
```

### Step 4: Add common typos (optional)

In the same file, add to `TYPO_CORRECTIONS`:

```python
TYPO_CORRECTIONS: dict[str, str] = {
    # ... existing entries ...
    "anisble": "ansible",
    "ansibel": "ansible",
    "ansbile": "ansible",
}
```

### Step 5: Add CLI shortcut (optional)

In `cli/src/alchemyai/cli.py`, add to `TECH_SHORTCUTS`:

```python
TECH_SHORTCUTS = {
    "kubernetes", "k8s", "docker", "git", "linux", "python",
    "go", "rust", "kafka", "terraform", "ansible",  # ← added
}
```

### Step 6: Validate, re-index, test

```bash
# Validate YAML
python scripts/validate_dataset.py

# Rebuild everything
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli dataset
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli embeddings
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli train

# Test it
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "run ansible playbook"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli ansible
```

---

## 5. User Custom Commands

Users can add personal or company-specific commands without modifying the project.

### Location

```
~/.config/alchemyai/commands/
```

### Create a custom file

```bash
mkdir -p ~/.config/alchemyai/commands
```

Create `~/.config/alchemyai/commands/company.yaml`:

```yaml
- id: company-deploy-staging
  technology: company
  category: deployment
  name: Deploy to staging
  intent: deploy_staging
  command: deploy-cli push --env staging --branch <branch>
  description: >
    Deploy the specified branch to the staging environment
    using the internal deployment CLI.
  tags: [deploy, staging, company, push]
  aliases:
    - deploy to staging
    - push to staging
    - staging deploy
  examples:
    - query: "deploy to staging"
    - query: "push my branch to staging"
  risk: warning
  documentation:
    url: https://internal-docs.company.com/deploy
  verified_at: "2026-08-01"

- id: company-vpn-connect
  technology: company
  category: network
  name: Connect to VPN
  intent: connect_vpn
  command: company-vpn connect --profile <profile>
  description: >
    Connect to the company VPN using a named profile.
  tags: [vpn, connect, network, company]
  aliases:
    - connect to vpn
    - start vpn
    - vpn connect
  examples:
    - query: "connect to the VPN"
    - query: "start VPN connection"
  risk: safe
  documentation:
    url: https://internal-docs.company.com/vpn
  verified_at: "2026-08-01"
```

### Key difference from project commands

- **No retraining needed** — custom commands are loaded at runtime
- **Indexed on the fly** — embeddings are generated when the engine starts
- You can create multiple files: `sre.yaml`, `personal.yaml`, `team.yaml`
- Custom commands appear in search results alongside built-in commands

---

## 6. Writing Good Query Examples

Each command should have **5-15 query variations** across aliases and examples.

### Include these query styles:

| Style | Example |
|-------|---------|
| Beginner | `"how do I restart a deployment"` |
| Experienced | `"kubectl rollout restart"` |
| Informal | `"restart my k8s deployment"` |
| Abbreviated | `"restart k8s deploy"` |
| Conceptual | `"how can I recreate pods for a deployment"` |
| Problem-based | `"my deployment is stuck, how do I restart it"` |

### Tips

- **Don't repeat the command** — users ask in natural language, not command syntax
- **Include technology abbreviations** — `k8s`, `tf`, `py`, `cargo`
- **Think about what the user is trying to solve**, not just what the command does
- **Include common misspellings** in aliases if relevant
- **Vary the sentence structure** — questions, statements, imperatives

### Bad examples ❌

```yaml
aliases:
  - kubectl rollout restart deployment   # Just the command itself
  - restart                              # Too vague
examples:
  - query: "restart"                     # Too vague, matches everything
```

### Good examples ✅

```yaml
aliases:
  - restart kubernetes deployment
  - restart k8s deployment
  - rollout restart
  - bounce a deployment
  - recreate deployment pods
examples:
  - query: "how do I restart a kubernetes deployment"
  - query: "restart k8s deploy"
  - query: "my deployment needs a restart"
  - query: "how can I recreate all pods in a deployment"
```

---

## 7. Risk Classification Guide

### `safe` — Read-only operations

No side effects. Can be run freely without consequences.

```yaml
# Examples:
kubectl get pods                    # safe
docker ps                          # safe
git status                         # safe
git log                            # safe
terraform show                     # safe
ls -la                             # safe
cat /etc/hosts                     # safe
```

### `warning` — State-modifying but recoverable

Changes state but can usually be undone or recovered from.

```yaml
# Examples:
kubectl apply -f manifest.yaml     # warning — modifies cluster
kubectl rollout restart deployment  # warning — restarts pods
docker stop <container>            # warning — stops container
docker rm <container>              # warning — removes container
git reset HEAD~1                   # warning — undoes commit
git merge <branch>                 # warning — merges branches
pip install <package>              # warning — installs software
terraform apply                    # warning — modifies infrastructure
systemctl restart <service>        # warning — restarts service
```

### `dangerous` — Destructive or irreversible

Data loss, service disruption, or actions that cannot be undone.

```yaml
# Examples:
kubectl delete namespace <ns>      # dangerous — deletes everything in namespace
docker system prune -a             # dangerous — removes ALL unused data
git push --force                   # dangerous — rewrites remote history
git reset --hard                   # dangerous — discards all changes
terraform destroy                  # dangerous — destroys infrastructure
rm -rf <path>                      # dangerous — deletes files permanently
DROP DATABASE <db>                 # dangerous — deletes database
```

### When in doubt

- If the command only **reads** data → `safe`
- If the command **changes** something but you can undo it → `warning`
- If the command **deletes** data or is **irreversible** → `dangerous`

---

## 8. Validation & Testing

### Validate YAML syntax and schema

```bash
python scripts/validate_dataset.py
```

This checks:
- Valid YAML syntax
- Required fields present (`id`, `technology`, `command`, `description`, `risk`)
- Valid risk values (`safe`, `warning`, `dangerous`)
- No duplicate IDs
- No empty commands or descriptions

### Test that your command is found

```bash
# Build and search
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli dataset
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli embeddings

# Search for your new command
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "your query here"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli --explain "your query here"
```

### Add a regression test

Append to `ml/tests/regression.jsonl`:

```json
{"query": "run ansible playbook", "expected": "ansible-playbook-run"}
```

Run regression tests:

```bash
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli regression
```

---

## 9. Re-indexing After Changes

### After adding commands to `knowledge/` (project-level)

```bash
# Rebuild dataset, embeddings, and classifier
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli dataset
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli embeddings
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli train
```

### After adding user custom commands (`~/.config/alchemyai/commands/`)

No rebuild needed — custom commands are indexed automatically at startup.

If the API server is running, reload it:

```bash
curl -X POST http://localhost:8000/api/v1/reload
```

### Quick reference

| What changed | What to rebuild |
|-------------|----------------|
| Added commands to `knowledge/` | `dataset` → `embeddings` → `train` |
| Added technology aliases in `preprocessing.py` | `dataset` → `embeddings` → `train` |
| Added user custom commands | Nothing (auto-loaded) |
| Changed ranking weights in config | Nothing (applied at runtime) |
| Changed training hyperparameters | `train` |

---

## 10. Full Example: Adding AWS CLI

Here's a complete walkthrough of adding a new technology from scratch.

### Step 1: Create the file

```bash
mkdir -p knowledge/aws
```

Create `knowledge/aws/commands.yaml`:

```yaml
# AlchemyCLI AI - AWS CLI Commands

- id: aws-s3-ls
  technology: aws
  category: s3
  name: List S3 buckets
  intent: list_s3_buckets
  command: aws s3 ls
  description: >
    List all S3 buckets in the current AWS account.
  tags: [aws, s3, buckets, list, storage]
  aliases:
    - list s3 buckets
    - show s3 buckets
    - aws s3 list
    - list my buckets
  examples:
    - query: "list my s3 buckets"
    - query: "show all S3 buckets"
    - query: "aws s3 ls"
  risk: safe
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/s3/ls.html
  verified_at: "2026-08-01"

- id: aws-s3-cp-upload
  technology: aws
  category: s3
  name: Upload file to S3
  intent: upload_to_s3
  command: aws s3 cp <local_file> s3://<bucket>/<key>
  description: >
    Upload a file from the local filesystem to an S3 bucket.
  tags: [aws, s3, upload, copy, file, transfer]
  aliases:
    - upload to s3
    - copy file to s3
    - aws s3 copy
    - push file to s3
  examples:
    - query: "upload a file to S3"
    - query: "copy file to s3 bucket"
    - query: "aws s3 upload"
  risk: safe
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/s3/cp.html
  verified_at: "2026-08-01"

- id: aws-s3-sync
  technology: aws
  category: s3
  name: Sync directory to S3
  intent: sync_s3
  command: aws s3 sync <local_dir> s3://<bucket>/<prefix>
  description: >
    Sync a local directory to an S3 bucket, uploading only changed files.
  tags: [aws, s3, sync, directory, upload, incremental]
  aliases:
    - sync to s3
    - s3 sync
    - sync directory to bucket
  examples:
    - query: "sync a folder to S3"
    - query: "upload directory to s3"
  risk: warning
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html
  verified_at: "2026-08-01"

- id: aws-ec2-describe-instances
  technology: aws
  category: ec2
  name: List EC2 instances
  intent: list_ec2_instances
  command: aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType]" --output table
  description: >
    List all EC2 instances showing instance ID, state, and type in a table format.
  tags: [aws, ec2, instances, list, servers, vms]
  aliases:
    - list ec2 instances
    - show ec2 instances
    - list aws servers
    - aws ec2 list
  examples:
    - query: "list my EC2 instances"
    - query: "show all AWS servers"
    - query: "what EC2 instances are running"
  risk: safe
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html
  verified_at: "2026-08-01"

- id: aws-ec2-stop-instance
  technology: aws
  category: ec2
  name: Stop EC2 instance
  intent: stop_ec2_instance
  command: aws ec2 stop-instances --instance-ids <instance_id>
  description: >
    Stop a running EC2 instance. The instance can be restarted later.
  tags: [aws, ec2, stop, instance, server]
  aliases:
    - stop ec2 instance
    - stop aws server
    - shut down instance
  examples:
    - query: "stop an EC2 instance"
    - query: "shut down my AWS server"
  risk: warning
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/ec2/stop-instances.html
  verified_at: "2026-08-01"

- id: aws-ec2-terminate-instance
  technology: aws
  category: ec2
  name: Terminate EC2 instance
  intent: terminate_ec2_instance
  command: aws ec2 terminate-instances --instance-ids <instance_id>
  description: >
    Permanently terminate an EC2 instance. This is irreversible and all
    data on instance storage will be lost.
  tags: [aws, ec2, terminate, delete, instance, destroy]
  aliases:
    - terminate ec2 instance
    - delete ec2 instance
    - destroy aws server
  examples:
    - query: "terminate an EC2 instance"
    - query: "delete an AWS server permanently"
  risk: dangerous
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/ec2/terminate-instances.html
  verified_at: "2026-08-01"

- id: aws-iam-whoami
  technology: aws
  category: iam
  name: Get current IAM identity
  intent: get_caller_identity
  command: aws sts get-caller-identity
  description: >
    Show the IAM user or role currently configured for the AWS CLI.
  tags: [aws, iam, identity, whoami, account, sts]
  aliases:
    - who am i aws
    - aws identity
    - current aws user
    - aws whoami
  examples:
    - query: "who am I in AWS"
    - query: "what AWS account am I using"
    - query: "show my AWS identity"
  risk: safe
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html
  verified_at: "2026-08-01"

- id: aws-s3-rb
  technology: aws
  category: s3
  name: Delete S3 bucket
  intent: delete_s3_bucket
  command: aws s3 rb s3://<bucket> --force
  description: >
    Delete an S3 bucket and all its contents. This is irreversible.
  tags: [aws, s3, delete, bucket, remove, destroy]
  aliases:
    - delete s3 bucket
    - remove s3 bucket
    - destroy s3 bucket
  examples:
    - query: "delete an S3 bucket"
    - query: "remove an s3 bucket and all its contents"
  risk: dangerous
  documentation:
    url: https://docs.aws.amazon.com/cli/latest/reference/s3/rb.html
  verified_at: "2026-08-01"
```

### Step 2: Register aliases

Edit `ml/src/alchemy_ml/preprocessing.py`:

```python
TECHNOLOGY_ALIASES: dict[str, str] = {
    # ... existing ...

    # AWS
    "aws": "aws",
    "aws-cli": "aws",
    "s3": "aws",
    "ec2": "aws",
    "iam": "aws",
    "lambda": "aws",
    "cloudformation": "aws",
    "eks": "aws",  # note: also mapped to kubernetes
    "rds": "aws",
    "dynamodb": "aws",
    "sqs": "aws",
    "sns": "aws",
    "cloudwatch": "aws",
}
```

### Step 3: Add CLI shortcut

Edit `cli/src/alchemyai/cli.py`:

```python
TECH_SHORTCUTS = {
    "kubernetes", "k8s", "docker", "git", "linux", "python",
    "go", "rust", "kafka", "terraform", "aws",
}
```

### Step 4: Validate and build

```bash
python scripts/validate_dataset.py
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli dataset
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli embeddings
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli train
```

### Step 5: Test

```bash
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "list my s3 buckets"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "who am i in aws"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "stop ec2 instance"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli aws
```

### Step 6: Add regression tests

Append to `ml/tests/regression.jsonl`:

```json
{"query": "list s3 buckets", "expected": "aws-s3-ls"}
{"query": "upload file to s3", "expected": "aws-s3-cp-upload"}
{"query": "stop ec2 instance", "expected": "aws-ec2-stop-instance"}
{"query": "who am i aws", "expected": "aws-iam-whoami"}
```

---

## Checklist for New Commands

- [ ] `id` is unique and follows `<technology>-<description>` format
- [ ] `command` uses `<placeholder>` notation for variables
- [ ] `command` is verified against official documentation
- [ ] `description` explains what the command does (1-3 sentences)
- [ ] `tags` has 3-8 relevant keywords
- [ ] `aliases` has 3-8 natural language variations
- [ ] `examples` has 2-5 query variations covering different phrasings
- [ ] `risk` is correctly classified (safe/warning/dangerous)
- [ ] `documentation.url` points to real official docs
- [ ] `verified_at` is set to the date you verified the command
- [ ] YAML validates: `python scripts/validate_dataset.py`
- [ ] Command is found by search after re-indexing

## Checklist for New Technologies

- [ ] All items from the command checklist above
- [ ] Created `knowledge/<technology>/commands.yaml`
- [ ] Added aliases in `ml/src/alchemy_ml/preprocessing.py`
- [ ] Added common typos in `TYPO_CORRECTIONS` (optional)
- [ ] Added CLI shortcut in `cli/src/alchemyai/cli.py`
- [ ] Minimum 20 commands covering the technology's core features
- [ ] Mix of safe, warning, and dangerous commands
- [ ] Regression tests added to `ml/tests/regression.jsonl`
- [ ] Full pipeline rebuilt: `dataset` → `embeddings` → `train`
