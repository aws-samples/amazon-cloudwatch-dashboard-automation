In an earlier blog post, <a href="https://aws.amazon.com/blogs/mt/automate-customized-deployment-of-cross-account-cross-region-cloudwatch-dashboards-using-tags/" target="_blank" rel="noopener noreferrer">Automate customized deployment of cross-account/cross-region CloudWatch dashboards using tags</a>, we showed you how to implement Amazon CloudWatch dashboards for specific events with automation. This solution is great for seasonal events, holidays, important releases, and other use cases.

In this blog post, we will review a landing zone environment and share a solution that can help you improve operational visibility at scale while eliminating Day 2 repetitive configuration tasks and overhead. When working with governance at scale, resource tagging makes it easy to identify the application stack and provisioned resources for different use cases such as automation, cost optimization/visablity, and so on.

<code>AppName</code> is a common resource tag that’s used across business units. Its tag value is relevant to the designated application deployed in different AWS accounts in the landing zone. The solution described in this blog post will allow you to centralize observability functions in the central monitoring/operational AWS account and dynamically generate Amazon CloudWatch dashboards for each application stack based on the tagged resource values with the Lambda function triggered by Amazon EventBridge. The operational team will minimize the onboarding process of the new application stack for the different business units by adding the tag keys and values in AWS Systems Manager Parameter Store in a monitoring/operational AWS account.
<h2>Solution overview</h2>
In this solution, the CloudWatch dashboard resides in a monitoring account. We collect data from accounts referred to as X, Y, and Z. Our objective is to have the CloudWatch dashboard contain aggregate metrics from all member accounts in the landing zone. To provide per-application stack observability in the monitoring account, we are using cross-account dashboard functionality in Amazon CloudWatch, where aggregated data is presented from the defined member accounts. Any resources in the monitoring account can be included in the dashboard, too.

If you followed the steps in our previous blog post, you set up CloudWatch data sharing in accounts X, Y, and Z. You also set up CloudWatch in the monitoring account so you can view the shared data. Your application resources should be tagged with a tag key (for example, <code>AppName</code>) and a unique tag value (for example, <code>AppX</code>) in member accounts. The Lambda function used in this blog post supports the monitoring of the following AWS services and resources: <a href="https://aws.amazon.com/ec2/">Amazon EC2</a>, <a href="https://aws.amazon.com/rds/">Amazon RDS</a>, <a href="https://aws.amazon.com/lambda/">AWS Lambda</a>, <a href="https://aws.amazon.com/elasticache/">Amazon ElastiCache</a>, <a href="https://aws.amazon.com/elasticloadbalancing/classic-load-balancer/">Classic Load Balancer</a>, <a href="https://aws.amazon.com/elasticloadbalancing/application-load-balancer/">Application Load Balancer</a>, <a href="https://aws.amazon.com/elasticloadbalancing/network-load-balancer/">Network Load Balancer</a>. This solution uses resources (IAM roles and policies) configured in the previous blog post.

<img class="aligncenter size-full wp-image-22605" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/08/03/Implement-Operations-Observability-with-Landing-Zone-Environments.png" alt="Operational or Monitoring Account where the Lambda function is deployed and there are 3 member accounts (X,Y,Z) and all accounts contains AWS resources. The Lambda function assumes a role and looks through resources within member accounts to capture the data that is required to output the CloudWatch Dashboard in the Operational or Monitoring Account." width="951" height="1537" />
<p style="text-align: center;"><em>Figure 1: Solution architecture</em></p>

<h2>Solution steps and deployment</h2>
The solution architecture shows the following components and steps:
<ol>
 	<li>In the monitoring account, in AWS Systems Manager Parameter Store, add four parameters for <code>dashboard-prefix</code>, <code>search-key</code>, <code>search-regions</code>, <code>search-values</code> and <code><a href="https://console.aws.amazon.com/systems-manager/parameters/use1/dev/cross-account-policy-name/description?region=us-east-1&amp;tab=Table">cross-account-policy-name</a></code>.</li>
 	<li>Complete steps 1, 2, 4, and 5 in the <a href="https://aws.amazon.com/blogs/mt/automate-customized-deployment-of-cross-account-cross-region-cloudwatch-dashboards-using-tags/">Automate customized deployment of cross-account/cross-region CloudWatch Dashboards using tags</a> blog post.</li>
 	<li>Create an IAM policy for retrieving the AWS Systems Manager Parameter Store parameters.</li>
 	<li>In the monitoring account, use the AWS Lambda console to create a Lambda function and associate IAM polices.</li>
 	<li>Tag your AWS resources in each member account.</li>
</ol>

<hr />

<h3>Step 1: In the monitoring account, add AWS Systems Manager Parameter Store parameters</h3>
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the Systems Manager console, choose <strong>Application Management</strong>, and then choose <strong>Parameter Store</strong>.</li>
 	<li>Under<strong>Parameter Store</strong>, choose <strong>Create Parameter</strong>.</li>
 	<li>In <strong>Parameter details</strong>, enter the following to create the parameters.</li>
</ol>
<p style="margin-left: 40px;"><strong>Name</strong>:<code>/$region/$environment/dashboard-prefix</code>
<strong>Type</strong>: String
<strong>Value</strong>: example-dashboard</p>
<p style="margin-left: 40px;"><strong>Name</strong>:<code>/$region/$environment/search-key</code>
<strong>Type</strong>: String
<strong>Value</strong>: AppName</p>
<p style="margin-left: 40px;"><strong>Name</strong>:<code>/$region/$environment/search-regions</code>
<strong>Type</strong>: StringList
<strong>Value</strong>: us-east-1,us-west-2</p>
<p style="margin-left: 40px;"><strong>Name</strong>:<code>/$region/$environment/search-values</code>
<strong>Type</strong>: StringList
<strong>Value</strong>: AppX,AppY,AppZ</p>
<p style="margin-left: 40px;"><strong>Name</strong>:<code>/$region/$environment/cross-account-policy-name</code>
<strong>Type</strong>: String
<strong>Value</strong>: CrossAccountDashboardDiscoveryPolicy</p>
<img class="aligncenter size-full wp-image-22607" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/08/03/Screen-Shot-2021-05-19-at-4.43.49-PM.png" alt="The Create Parameter page showing all the details that are required to make the parameter." width="1715" height="1608" />
<p style="text-align: center;"><em>Figure 2: Create parameter</em></p>
After you create the parameters, use the <strong>My parameters</strong> tab to confirm that the correct parameter type (in this case, string) appears, as shown in Figure 3:

<img class="aligncenter size-full wp-image-22608" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/08/03/Screen-Shot-2021-05-19-at-4.41.09-PM.png" alt="My parameters page showing the parameters you have created." width="1717" height="732" />
<p style="text-align: center;"><em>Figure 3: My parameters</em></p>
Alternatively, you can use the AWS CLI to add AWS Systems Manager Parameter Store parameters:

<code>aws ssm put-parameter --name "/us-east-1/dev/dashboard-prefix" --type String —value "example-dashboard"</code>

<code>aws ssm put-parameter --name "/us-east-1/dev/search-key" --type String —value "AppName"</code>

<code>aws ssm put-parameter --name "/us-east-1/dev/search-regions" --type StringList —value "us-east-1,us-west-2"</code>

<code>aws ssm put-parameter --name "/us-east-1/dev/search-values" --type StringList —value "AppX,AppY,AppZ"</code>

<code>aws ssm put-parameter --name "/us-east-1/dev/cross-account-policy-name" --type String —value "CrossAccountDashboardDiscoveryPolicy"</code>

For more information, see <a href="https://docs.aws.amazon.com/systems-manager/latest/userguide/param-create-cli.html">Create a Systems Manager parameter (AWS CLI)</a> in the AWS Systems Manager User Guide.

<hr />

<h3>Step 2: Complete the steps from the earlier blog post</h3>
Complete the following steps in the <a href="https://aws.amazon.com/blogs/mt/automate-customized-deployment-of-cross-account-cross-region-cloudwatch-dashboards-using-tags/">Automate customized deployment of cross-account/cross-region CloudWatch dashboards using tags</a> blog post:

Step 1: In accounts X, Y, and Z, set up cross-account functionality in CloudWatch to share data with the monitoring account

Step 2: In the monitoring account, set up cross-account functionality in CloudWatch to access the shared data from accounts X, Y, and Z

Step 4: In accounts X, Y, and Z, create the AllowMonitoringAccountAccess role to provide access to the monitoring account

Step 5: Create CrossAccountDashboardDiscoveryPolicy, CloudWatchDashboardCustomPolicy, and IAMCustomPolicy in the monitoring account

<hr />

<h3>Step 3: Create an IAM policy for retrieving the AWS Systems Manager Parameter Store parameters</h3>
Create an IAM policy in the monitoring account that will allow the Lambda function to retrieve values from AWS Systems Manager Parameter Store.

To create the <code>GetCloudWatchDashboardCreationParametersFromSSM</code> policy:
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the IAM console, choose <strong>Policies</strong>, and then choose <strong>Create policy</strong>.</li>
 	<li>Choose the <strong>JSON</strong></li>
 	<li>Replace the default statement with the following policy. Update the <code>$environment</code>, <code>$region</code>, and <code>$monitoring_account_number</code> variables to match your environment.</li>
</ol>
<div class="hide-language">
<pre><code class="lang-json">{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters"
            ],
            "Resource": "arn:aws:ssm:$region:$monitoring_account_number:parameter/$region/$environment/*",
            "Effect": "Allow"
        }
    ]
}
</code></pre>
</div>
<ol start="5">
 	<li>Choose <strong>Review Policy</strong>.</li>
 	<li>On the <strong>Review policy</strong> page, enter a name (for example, <code>GetCloudWatchDashboardCreationParametersFromSSM</code>)and an optional description, and then choose <strong>Create policy</strong>.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create-console.html">Creating IAM policies</a> in the IAM User Guide.

<hr />

<h3>Step 4: Create a Lambda function, update the IAM policy for the function, and add environment variables in the monitoring account</h3>
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the AWS Lambda console, choose <strong>Functions</strong>, and then choose <strong>Create a function</strong>.</li>
 	<li>Leave <strong>Author from scratch</strong> For <strong>Function name</strong>, enter <code>AutomateLandingZoneDashboards</code>. For <strong>Runtime</strong>, choose <strong>Python 3.8</strong>.</li>
 	<li>Expand <strong>Change default execution role</strong>, make a note of the IAM role that will be created for this Lambda function (for example, AutomateLandingZoneDashboards-role-unlbygt9), and then choose <strong>Create function</strong>.</li>
 	<li>On the <strong>Configuration</strong> tab, choose <strong>Edit</strong>. For <strong>Timeout</strong>, enter 15 seconds, and then choose <strong>Save</strong>.</li>
 	<li>Copy and paste the content of the <code>cw-automatelandingzonedashboard.py</code> file in <a href="https://github.com/aws-samples/amazon-cloudwatch-dashboard-automation">GitHub</a>. Edit line 11 in the Lambda function code. Change the <code>pathprefix</code> value to reflect the AWS Systems Manager Parameter Store path that will be used for the lookup of parameters and values (example, <code>/us-east-1/dev/</code>), and choose <strong>Deploy</strong>.</li>
 	<li>Go to the IAM console, update the IAM role created by the Lambda function (for example, AutomateLandingZoneDashboards-role-unlbygt9), and then attach the following IAM polices:
<ul>
 	<li>CrossAccountDashboardDiscoveryPolicy</li>
 	<li>CloudWatchDashboardCustomPolicy</li>
 	<li>IAMCustomPolicy</li>
 	<li>ResourceGroupsandTagEditorReadOnlyAccess</li>
 	<li>GetCloudWatchDashboardCreationParametersFromSSM</li>
</ul>
</li>
</ol>
<p style="margin-left: 40px;"><strong>Note</strong>: The AWSLambdaBasicExecutionRole-**** managed policy will already be attached to this role.</p>

<ol start="8">
 	<li>Go back to the AWS Lambda console and choose <strong>Lambda function</strong>. Choose <strong>AutomateLandingZoneDashboards</strong>, and then choose <strong>Test</strong>.</li>
 	<li>For <strong>Configure test event</strong>, enter a name for the event, and then choose <strong>Create</strong>.</li>
</ol>
<p style="margin-left: 40px;"><strong>Note</strong>: The Lambda function looks for resources in us-east-1 and us-west-2.</p>
For more information, see <a href="https://docs.aws.amazon.com/lambda/latest/dg/getting-started-create-function.html">Create a Lambda function with the console</a> in the AWS Lambda Developer Guide.

<hr />

<h3>Step 5: Tag your AWS resources</h3>
<ol>
 	<li>From each member account, obtain the resource tag that is governing the resources relevant to particular application stack.</li>
 	<li>For the tag key, use <code>AppName</code>. For the tag value, use <code>AppX</code>.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html">Tagging AWS resources</a> in the AWS General Reference.

<hr />

<h3>Step 6: Configure or update EventBridge in the monitoring account</h3>
In the monitoring account where the Lambda function is located, add a trigger for EventBridge (CloudWatch Events) to make the Lambda function run every 5 minutes. If you add or remove tags, the CloudWatch dashboard will be automatically updated at regular intervals. You can customize the trigger time to your requirements.
<ol>
 	<li>Sign in to the monitoring account.</li>
 	<li>In the AWS Lambda console, choose <strong>Functions</strong>, and then choose <strong>AutomateLandingZoneDashboards</strong>.</li>
 	<li>In the <strong>Designer</strong> section, choose <strong>Add trigger</strong>, and then choose a trigger of EventBridge (CloudWatch Events).</li>
 	<li>Under <strong>Rule</strong>, choose <strong>Create a new rule</strong>.</li>
 	<li>For <strong>Rule name</strong>, enter <code>EventBridgeAutomateLandingZoneDashboards</code>. For <strong>Rule type</strong>, choose <strong>Schedule expression</strong>. You can enter the expression that best fits your use case. In this post, we use every 5 minutes.</li>
</ol>
For more information, see <a href="https://docs.aws.amazon.com/eventbridge/latest/userguide/run-lambda-schedule.html">Schedule AWS Lambda Functions Using EventBridge</a> in the Amazon EventBridge User Guide.

After the Lambda function runs and identifies each app, it creates a dashboard for each app. The dashboards are displayed in Custom Dashboards, as shown in Figure 4.

<img class="aligncenter size-full wp-image-22612" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/08/03/dashboard.png" alt="Example of AWS CloudWatch Dashboard showing the different dashboards that were created per application." width="902" height="281" />
<p style="text-align: center;"><em>Figure 4: Custom dashboards</em></p>
After the solution has been deployed and all application stacks and resources we want to monitor have been tagged, here are some examples of the CloudWatch dashboards:

<img class="aligncenter size-full wp-image-22609" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/08/03/CWDashboardExample1.png" alt="Example dashboard showing metrics being collected by resources." width="3790" height="1910" />
<p style="text-align: center;"><em>Figure 5: CloudWatch dashboard example</em></p>
<img class="aligncenter size-full wp-image-22610" src="https://d2908q01vomqb2.cloudfront.net/972a67c48192728a34979d9a35164c1295401b71/2021/08/03/CWDashboardExample2.png" alt="Second example dashboard showing metrics being collected by resources." width="3793" height="1810" />
<p style="text-align: center;"><em>Figure 6: CloudWatch dashboard alt </em><i>example</i></p>

<h2>Conclusion</h2>
In this blog post, we showed you how to create the IAM policy that is required to retrieve details from the AWS Systems Manager Parameter Store to dynamically generate Amazon CloudWatch dashboards. This solution solves the problem of manually managing and updating a CloudWatch dashboards for application stacks in your landing zone. By using tags and the automation of EventBridge and Lambda, you can achieve observability automation at scale.
<h3>About the authors</h3>
<footer>

</div>
</footer>
