# Odyssey watcher

The watcher runs in GitHub Actions. An Amazon EventBridge Scheduler resource in
`us-east-1` dispatches the workflow every five minutes because GitHub's native
cron scheduler did not reliably enqueue the newly created workflow.

Infrastructure is managed by the `koby-odyssey-github-scheduler` CloudFormation
stack using [`aws-scheduler.yml`](aws-scheduler.yml). The GitHub credential is
stored separately in AWS Secrets Manager as `koby/odyssey/github-token`; it is
never committed to this repository or logged by the Lambda function.

Useful checks:

```sh
aws scheduler get-schedule \
  --profile support-internal \
  --name koby-odyssey-every-five-minutes

aws logs tail \
  --profile support-internal \
  /aws/lambda/koby-odyssey-github-dispatch \
  --since 30m
```
