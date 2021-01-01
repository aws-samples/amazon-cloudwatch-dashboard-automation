<a href="https://aws.amazon.com/blogs/aws/cloudwatch-dashboards-create-use-customized-metrics-views/">Amazon CloudWatch Dashboards</a> are a great way to monitor your AWS resources. During peak events when you are expecting high traffic, monitoring your AWS resources helps you stay ahead of any issues that might arise. You might want a customized and automated dashboard that can be used during a seasonal event, important releases, holidays, and other dates important to operations.Setting up a dashboard can be a repetitive process. A dashboard can be difficult to manage and keep up to date. In this blog post, we show you how to use tagging, the cross-account and cross-Region functionality in Amazon CloudWatch, and a Lambda function triggered by <a href="https://aws.amazon.com/eventbridge/">Amazon EventBridge</a> to create a dashboard automatically.
<h2><strong>Solution overview </strong></h2>
For purposes of this post, we have a monitoring account where the CloudWatch dashboard  resides. We have accounts referred to as X, Y, and Z from which we collect data. Our objective is to have the CloudWatch dashboard contain aggregate metrics from all the accounts in the scope of the event. One dashboard in the monitoring account collects data from the other shared accounts. Any resources in the monitoring account can be included in the dashboard, too.

If you follow the steps in this post, you’ll set up CloudWatch data sharing in accounts X, Y, and Z. You’ll also set up CloudWatch in the monitoring account so you can view the shared data. Then, you’ll tag resources in all accounts. Lastly, you’ll create IAM roles in accounts X, Y, and Z that will be assumed by an IAM user in the monitoring account to check for tagged resources and collect data from these accounts. A Lambda function will apply the IAM policies. You’ll set a schedule in Amazon EventBridge to automate the running of the Lambda function to keep the dashboard up to date.

&nbsp;

<img class="alignnone size-full wp-image-15870" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/01/01/Automate-Customized-Cross-Account-and-Cross-Region-CloudWatch-Dashboard-Deployment-using-Tags-Vertical-1.jpg" alt="Figure 1: Solution architecture" width="971" height="1531" />

Figure 1: Solution architecture
<h2><strong>Solution steps and deployment</strong></h2>
<ol>
 	<li>In accounts X, Y, and Z, set up cross-account functionality in CloudWatch to share data with the monitoring account.</li>
 	<li>In the monitoring account, set up cross-account functionality in CloudWatch to access the shared data from accounts X, Y, and Z.</li>
 	<li>Tag your AWS resources.</li>
 	<li>In accounts X, Y, and Z, create an IAM role, <strong>AllowMonitoringAccountAccess</strong>, that provides access to the monitoring account.</li>
 	<li>In the monitoring account, create IAM policies <strong>(CrossAccountDashboardDiscoveryPolicy, CloudWatchDashboardCustomPolicy, </strong>and<strong> IAMCustomPolicy).</strong></li>
 	<li>In the monitoring account, create a Lambda function and update the IAM policy for the function.</li>
 	<li>In the monitoring account, configure <a href="https://aws.amazon.com/eventbridge/">Amazon EventBridge</a>.</li>
</ol>
<h2>Step 1: In accounts X, Y, and Z, set up cross-account functionality in CloudWatch to share data with the monitoring account</h2>
Cross-account functionality is integrated with <a href="https://aws.amazon.com/organizations/">AWS Organizations</a> to help efficiently build your cross-account dashboards. In this blog post, we do not use AWS Organizations. Because cross-Region functionality is now built in to CloudWatch, no further action is required.
<ol>
 	<li>Sign in to accounts X, Y, and Z.</li>
 	<li>In the CloudWatch console, choose <strong>Settings</strong>, and then under <strong>Cross-account cross-region</strong>, choose <strong>Configure</strong>.</li>
 	<li>Under <strong>Share your CloudWatch</strong> <strong>data</strong>, choose <strong>Share data</strong>.</li>
 	<li>Under <strong>Sharing</strong>, choose <strong>Specific accounts</strong>, and then choose <strong>Add account</strong>. Enter the monitoring account ID.</li>
 	<li>Under <strong>Permissions</strong>, keep the defaults.</li>
 	<li>Under <strong>Create CloudFormation Stack</strong>, choose <strong>Launch CloudFormation template</strong>.</li>
 	<li>On the confirmation page, type <code class="lang-js">Confirm</code>, and then choose <strong>Launch template</strong>.</li>
 	<li>Select the <strong>I acknowledge</strong> check box, and then choose Create stack.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Cross-Account-Cross-Region.html#enable-cross-account-cross-Region">Enable Cross-Account Functionality in CloudWatch</a> in the Amazon CloudWatch User Guide.
<h2>Step 2: In the monitoring account, set up cross-account functionality in CloudWatch to access the shared data from accounts X, Y, and Z</h2>
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the CloudWatch console, choose <strong>Settings</strong>, and then under <strong>Cross-account cross-region</strong>, choose <strong>Configure</strong>.</li>
 	<li>Under <strong>View cross-account cross-region</strong>, choose <strong>Enable</strong>.</li>
 	<li>Under <strong>Enable account selector</strong>, choose <strong>Custom account selector</strong>, and then enter the accounts you will be monitoring.  Example: 012345678912 My account label, 987654321012 My other account</li>
 	<li>Choose <strong>Enable</strong>.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Cross-Account-Cross-Region.html#enable-cross-account-cross-Region">Enable Cross-Account Functionality in CloudWatch</a> in the Amazon CloudWatch User Guide.
<h2>Step 3: Tag your AWS resources</h2>
<ol>
 	<li>Sign in to each account and tag the resources you would like to monitor. In this blog post, we cover the following AWS services and resources: <a href="https://aws.amazon.com/ec2/">Amazon EC2</a>, <a href="https://aws.amazon.com/rds/">Amazon RDS</a>, <a href="https://aws.amazon.com/lambda/">AWS Lambda</a>, <a href="https://aws.amazon.com/elasticache/">Amazon ElastiCache</a>, <a href="https://aws.amazon.com/elasticloadbalancing/classic-load-balancer/">Classic Load Balancer</a>, <a href="https://aws.amazon.com/elasticloadbalancing/application-load-balancer/">Application Load Balancer</a>, <a href="https://aws.amazon.com/elasticloadbalancing/network-load-balancer/">Network Load Balancer</a>.</li>
 	<li>For the tag key, use<code class="lang-json">event</code>. For the tag value, use<code class="lang-json">specialevent</code>. If you decide to customize the tagging, be sure to update lines 12 and 13 of the Lambda function code.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html">Tagging AWS resources</a> in the AWS General Reference.
<h2>Step 4: In accounts X, Y, and Z, create the AllowMonitoringAccountAccess role to provide access to the monitoring account</h2>
Sign in to accounts X, Y, and Z and create an IAM role that allows the monitoring account access to view the resources.
<ol>
 	<li>Sign in to accounts X, Y, and Z.</li>
 	<li>In the IAM console, choose <strong>Roles</strong>, and then choose <strong>Create role</strong>.</li>
 	<li>Choose <strong>Another AWS account</strong>, and then enter the account ID of the monitoring account.</li>
 	<li>Choose <strong>Next: Permissions</strong>.</li>
 	<li>Search for and choose the following policies: <strong>CloudWatchReadOnlyAccess</strong> and <strong>ResourceGroupsandTagEditorReadOnlyAccess</strong></li>
 	<li>Choose Next: <strong>Tags</strong>.</li>
 	<li>Choose Next: <strong>Review</strong>.</li>
 	<li>For the role name, enter <code class="lang-json">AllowMonitoringAccountAccess</code>. For the role description, enter<code class="lang-json">Role will allow read-only access to the monitoring account for building a CloudWatch dashboard</code>.</li>
 	<li>Review the role, and then choose <strong>Create role</strong>.</li>
 	<li>Perform these steps for accounts X, Y, and Z. In each account, find the role you created and copy its ARN. You need it in Step 5.
<ul>
 	<li>Example Account X: arn:aws:iam::012345678912:role/AllowMonitoringAccountAccess</li>
 	<li>Example Account Y: arn:aws:iam::987654321012:role/AllowMonitoringAccountAccess</li>
 	<li>Example Account Z: arn:aws:iam::123456789123:role/AllowMonitoringAccountAccess</li>
</ul>
</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user.html">Creating a role to delegate permissions to an IAM user</a> in the IAM User Guide.
<h2>Step 5: Create CrossAccountDashboardDiscoveryPolicy, CloudWatchDashboardCustomPolicy, and IAMCustomPolicy in the monitoring account</h2>
In this step, you create three IAM policies in the monitoring account. You attach these policies to the Lambda function in Step 6.

To create <strong>CrossAccountDashboardDiscoveryPolicy</strong>:
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the IAM console, choose <strong>Policies</strong>, and then choose <strong>Create policy</strong>.</li>
 	<li>Choose the JSON tab. Edit the following template with the ARNs you collected in Step 4.
Here is an example policy for one account:
<pre><code class="lang-json">{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": [
                "arn:aws:iam::012345678912:role/AllowMonitoringAccountAccess"
            ]
        }
    ]
}
</code></pre>
Here is an example policy for more than one account:
<pre><code class="lang-json">{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": [
                "arn:aws:iam::012345678912:role/AllowMonitoringAccountAccess",
                "arn:aws:iam::987654321012:role/AllowMonitoringAccountAccess",
                "arn:aws:iam::123456789123:role/AllowMonitoringAccountAccess"
            ]
        }
    ]
}</code></pre>
</li>
 	<li>Choose <strong>Review Policy</strong>, and on the <strong>Review policy</strong> page, enter a name <code>CrossAccountDashboardDiscoveryPolicy</code> and optional description.</li>
 	<li>Choose <strong>Create policy</strong>.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create-console.html">Creating IAM policies</a> in the IAM User Guide.

To create the <strong>CloudWatchDashboardCustomPolicy</strong>:
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the IAM console, choose <strong>Policies</strong>, and then choose <strong>Create policy</strong>.</li>
 	<li>Choose the <strong>JSON</strong> tab, and then paste the following template. Replace the placeholder account number with the account number for your monitoring account.
<pre><code class="lang-json">{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "cloudwatch:PutDashboard",
            "Resource": "arn:aws:cloudwatch::000111222333:dashboard/*"
        }
    ]
}</code></pre>
</li>
 	<li>Choose <strong>Review Policy</strong>, and on the <strong>Review policy</strong> page, enter a name <code>CloudWatchDashboardCustomPolicy</code> and an optional description.</li>
 	<li>Choose <strong>Create policy</strong>.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create-console.html">Creating IAM policies</a> in the IAM User Guide.

To create the <strong>IAMCustomPolicy</strong>:
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the IAM console, choose Policies, and then choose Create policy.</li>
 	<li>Choose the JSON tab.</li>
 	<li>Edit the following template with the account number of your monitoring account and then paste it into the field on the JSON tab.
<pre><code class="lang-json">{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetPolicyVersion",
                "iam:GetPolicy"
            ],
            "Resource": "arn:aws:iam::000111222333:policy/CrossAccountDashboardDiscoveryPolicy"
        }
    ]
}</code></pre>
</li>
 	<li>Choose <strong>Review Policy</strong>, and on the <strong>Review policy</strong> page, enter a name <code>IAMCustomPolicy</code> and an optional description.</li>
 	<li>Choose <strong>Create policy</strong>.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create-console.html">Creating IAM policies</a> in the IAM User Guide.
<h2>Step 6: Create a Lambda function and update the IAM policy for the function in the monitoring account</h2>
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the AWS Lambda console, choose <strong>Functions</strong>, and then choose <strong>Create a function</strong>.</li>
 	<li>Leave <strong>Author from scratch</strong> selected. For <strong>Function name</strong>, enter <code>AutomateCloudWatchDashboards</code>. For <strong>Runtime</strong>, choose <strong>Python 3.8</strong>.</li>
 	<li>Expand <strong>Change default execution role</strong>, make a note of the IAM role that will be created for this Lambda function (for example, <strong>AutomateCloudWatchDashboards-role-91t3fwgj</strong>), and then choose <strong>Create function</strong>.</li>
 	<li>Under <strong>Basic Settings</strong>, choose <strong>Edit</strong>. Update <strong>Timeout</strong> to <strong>15 seconds</strong>, and then choose <strong>Save</strong>.</li>
 	<li>Copy and paste the content of file <code>cwautomatedashboard.py</code> located at <a href="https://github.com/aws-samples/amazon-cloudwatch-dashboard-automation">GitHub</a>, and then choose Deploy.</li>
 	<li>In the IAM console, update the IAM role created by the Lambda function (for example, <strong>AutomateCloudWatchDashboards-role-91t3fwgj</strong>), and then attach the following IAM polices. <strong>Note</strong>: There will already be one managed policy, <strong>AWSLambdaBasicExecutionRole-****</strong>, attached to this role.
<strong>CrossAccountDashboardDiscoveryPolicy</strong>, <strong>CloudWatchDashboardCustomPolicy</strong>, <strong>IAMCustomPolicy</strong>, and <strong>ResourceGroupsandTagEditorReadOnlyAccess</strong></li>
 	<li>In the AWS Lambda console, choose <strong>Lambda function</strong>. Choose <strong>AutomateCloudWatchDashboards</strong>, and then choose <strong>Test</strong>.</li>
 	<li>For <strong>Configure test event</strong>, enter a name for the event, and then choose <strong>Create</strong>.</li>
 	<li>Choose <strong>Test</strong> and confirm the function ran successfully.
Note: The Lambda function looks for resources in us-east-1, us-east-2, us-west-1, and us-west-2. You can edit Region information in line 14 of the Lambda function.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/lambda/latest/dg/getting-started-create-function.html">Create a Lambda function with the console</a> in the AWS Lambda Developer Guide.
<h2>Step 7: Configure EventBridge in the monitoring account</h2>
In the monitoring account where the Lambda function is located, add a trigger for EventBridge (CloudWatch Events) to make the Lambda function run every 5 minutes. If you make add or remove tags, the CloudWatch dashboard will be automatically updated at regular intervals. You can customize the trigger time to your requirements.
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the AWS Lambda console, choose <strong>Functions</strong>.</li>
 	<li>Choose <strong>AutomateCloudWatchDashboards</strong>.</li>
 	<li>In the <strong>Designer</strong> section, choose <strong>Add trigger</strong>, and then choose a trigger of EventBridge (CloudWatch Events).</li>
 	<li>Under <strong>Rule</strong>, choose <strong>Create a new rule</strong>.</li>
 	<li>For <strong>Rule name</strong>, enter <code>EventBridgeAutomateCloudWatchDashboards</code>. For <strong>Rule type</strong>, choose <strong>Schedule expression</strong>. You can enter the expression that best fits your use case. In this post, we use every 5 minutes.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/eventbridge/latest/userguide/run-lambda-schedule.html">Schedule AWS Lambda Functions Using EventBridge</a> in the Amazon EventBridge User Guide.
<h2>Conclusion</h2>
In this blog post, we walked through the steps to configure Amazon CloudWatch to share data with the monitoring account. We showed you how to create the IAM roles and polices that are required to provide access to collect data. This solution solves the problem of manually managing and updating a CloudWatch dashboard. By using tags and the automation of EventBridge and Lambda, the work is done for you.

After the solution has been deployed and all the resources we want to monitor have been tagged, here are two example CloudWatch dashboards:

<img class="alignnone size-full wp-image-15855" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2020/12/31/CWDashboardExample1.png" alt="Figure 2: Example dashboard" width="1910" height="1910" />

<em>Figure 2: Example dashboard</em>

<img class="alignnone size-full wp-image-15856" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2020/12/31/CWDashboardExample2.png" alt="Figure 3: Second example dashboard" width="3793" height="1810" />

<em>Figure 3: Second example dashboard</em>

<hr />

&nbsp;
<h3>About the Authors</h3>
<img class="alignleft wp-image-453 size-thumbnail" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/01/01/Salman-Ahmed.png" alt="" width="150" height="150" />
Salman Ahmed is a Technical Account Manager for AWS Enterprise Support. He has been working with cloud technologies for 10+ years. Salman works with Enterprise Support customers to help them with design, implementation and supporting cloud infrastructure.

<img class="alignleft wp-image-453 size-thumbnail" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/01/01/Mike-Gomez.png" alt="" width="150" height="150" />
Mike Gomez is an Enterprise Support Lead for AWS Enterprise Support.
<div class="tag-list"></div>



## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

