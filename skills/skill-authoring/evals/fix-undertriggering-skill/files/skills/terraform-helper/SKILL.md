---
name: terraform-helper
description: Helps with Terraform.
---

# Terraform helper

1. Run `terraform fmt -recursive`.
2. Run `terraform validate`.
3. Run `terraform plan -out tfplan` and summarize resource changes, highlighting any destroy or replace actions.
4. Never run `terraform apply` without the user confirming the plan summary.
5. For state moves use `terraform state mv`, and back up state first with `terraform state pull > backup.tfstate`.
