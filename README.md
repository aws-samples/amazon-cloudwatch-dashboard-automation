Amazon CloudWatch Dashboards are a great way to monitor your AWS resources. During peak events when you are expecting high traffic, monitoring your AWS resources helps you stay ahead of any issues that might arise. You might want a customized and automated dashboard that can be used during a seasonal event, important releases, holidays, and other dates important to operations.Setting up a dashboard can be a repetitive process. A dashboard can be difficult to manage and keep up to date. In this blog post, we show you how to use tagging, the cross-account and cross-Region functionality in Amazon CloudWatch, and a Lambda function triggered by Amazon EventBridge to create a dashboard automatically.

## Solution overview 

For purposes of this post, we have a monitoring account where the CloudWatch dashboard  resides. We have accounts referred to as X, Y, and Z from which we collect data. Our objective is to have the CloudWatch dashboard contain aggregate metrics from all the accounts in the scope of the event. One dashboard in the monitoring account collects data from the other shared accounts. Any resources in the monitoring account can be included in the dashboard, too.

If you follow the steps in this post, you’ll set up CloudWatch data sharing in accounts X, Y, and Z. You’ll also set up CloudWatch in the monitoring account so you can view the shared data. Then, you’ll tag resources in all accounts. Lastly, you’ll create IAM roles in accounts X, Y, and Z that will be assumed by an IAM user in the monitoring account to check for tagged resources and collect data from these accounts. A Lambda function will apply the IAM policies. You’ll set a schedule in Amazon EventBridge to automate the running of the Lambda function to keep the dashboard up to date.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

