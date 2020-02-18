const cf = require('@mapbox/cloudformation');

const Parameters = {
    GitSha: {
        Type: "String",
        Description: "Gitsha to Deploy"
    }
};

const Resources = {
    "AWSBatchServiceRole": {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "batch.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }]
            },
            "ManagedPolicyArns": [ "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole" ],
            "Path": "/service-role/"
        }
    },
    "BatchInstanceRole": {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }]
            },
            "ManagedPolicyArns": [ "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role" ],
            "Path": "/"
        }
    },
    "BatchInstanceProfile": {
        "Type": "AWS::IAM::InstanceProfile",
        "Properties": {
            "Roles": [ cf.ref('BatchInstanceRole') ],
            "Path": "/"
        }
    },
    "BatchJobRole": {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ecs-tasks.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            "Policies": [{
                "PolicyName": "batch-job-policy",
                "PolicyDocument": {
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [ "s3:GetObject" ],
                        "Resource": [ "arn:aws:s3:::data.openaddresses.io/*" ]
                    }]
                }
            }],
            "Path": "/"
        }
    },
    "BatchComputeEnvironment": {
        "Type" : "AWS::Batch::ComputeEnvironment",
        "Properties" : {
            "Type" : "MANAGED",
            "ServiceRole" : cf.getAtt('AWSBatchServiceRole', 'Arn'),
            "ComputeEnvironmentName" : cf.join('-', ['batch', cf.ref('AWS::StackName')]),
            "ComputeResources" : {
                "ImageId": "ami-056807e883f197989",
                "MaxvCpus" : 128,
                "DesiredvCpus" : 32,
                "MinvCpus" : 0,
                "SecurityGroupIds" : [ cf.ref('SecurityGroup') ],
                "Subnets" :  [
                    'subnet-de35c1f5',
                    'subnet-e67dc7ea',
                    'subnet-38b72502',
                    'subnet-76ae3713',
                    'subnet-35d87242',
                    'subnet-b978ade0'
                ],
                "Type" : "EC2",
                "InstanceRole" : cf.getAtt('BatchInstanceProfile', 'Arn'),
                "InstanceTypes" : [ "optimal" ]
            },
            "State" : "ENABLED"
        }
    },
    "BatchJobDefinition": {
        "Type": "AWS::Batch::JobDefinition",
        "Properties": {
            "Type": "container",
            "JobDefinitionName": "batch-job",
            "RetryStrategy": {
                "Attempts": 1
            },
            "Parameters": { },
            "ContainerProperties": {
                "Command": [ "./task.sh", ],
                "Memory": 4000,
                "Privileged": true,
                "JobRoleArn": cf.getAtt('BatchJobRole', 'Arn'),
                "ReadonlyRootFilesystem": false,
                "Vcpus": 2,
                "Image": cf.join([cf.ref('AWS::AccountId'), '.dkr.ecr.', cf.ref('AWS::Region'), '.amazonaws.com/batch:', cf.ref('GitSha')])
            }
        }
    },
    "SecurityGroup": {
        "Type": "AWS::EC2::SecurityGroup",
        "Properties": {
            "VpcId": "vpc-3f2aa15a",
            "GroupDescription": "Batch Security Group",
            SecurityGroupIngress: []
        }
    },
    "BatchJobQueue": {
        "Type": "AWS::Batch::JobQueue",
        "Properties": {
            "ComputeEnvironmentOrder": [{
                "Order": 1,
                "ComputeEnvironment": cf.ref('BatchComputeEnvironment')
            }],
            "State": "ENABLED",
            "Priority": 1,
            "JobQueueName": "HighPriority"
        }
    },
    "LambdaExecutionRole": {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal":{
                        "Service": [ "lambda.amazonaws.com" ]
                    },
                    "Action": [ "sts:AssumeRole" ]
                }]
            },
            "Path": "/",
            "Policies": [{
                "PolicyName": "lambda-batch",
                "PolicyDocument": {
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [ "batch:SubmitJob" ],
                        "Resource": "arn:aws:batch:*:*:*"
                    }]
                }
            },{
                "PolicyName": "lambda-logs",
                "PolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [ "logs:*" ],
                        "Resource": "arn:aws:logs:*:*:*"
                    }]
                }
            },{
                "PolicyName": "lambda-s3",
                "PolicyDocument": {
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [ "s3:GetObject" ],
                        "Resource": [ 'arn:aws:s3:::openaddresses-lambdas/*' ]
                    }]
                }
            }]
        }
    },
    "LambdaTriggerFunction": {
        "Type": "AWS::Lambda::Function",
        "Properties": {
            "Handler": "index.trigger",
            "Role": cf.getAtt('LambdaExecutionRole', 'Arn'),
            "Code": {
                "S3Bucket": 'openaddresses-lambdas',
                "S3Key": cf.join(['batch/', cf.ref('GitSha'), '.zip' ])
            },
            "Environment": {
                "Variables": {
                    "JOB_DEFINITION": cf.ref('BatchJobDefinition'),
                    "JOB_QUEUE": cf.ref('BatchJobQueue'),
                    "JOB_NAME": "lambda-trigger-job"
                }
            },
            "Runtime": "nodejs12.x",
            "Timeout": "25"
        }
    },
    "ScheduledRule": {
        "Type": "AWS::Events::Rule",
        "Properties": {
            "Description": "ScheduledRule",
            "ScheduleExpression": "rate(10 minutes)",
            "State": "ENABLED",
            "Targets": [{
                "Arn": cf.getAtt('LambdaTriggerFunction', 'Arn'),
                "Id": "TriggerFunction"
            }]
        }
    },
    "PermissionForEventsToInvokeLambda": {
        "Type": "AWS::Lambda::Permission",
        "Properties": {
            "FunctionName": cf.ref('LambdaTriggerFunction'),
            "Action": "lambda:InvokeFunction",
            "Principal": "events.amazonaws.com",
            "SourceArn": cf.getAtt('ScheduledRule', 'Arn')
        }
    }
};

module.exports = {
    Parameters,
    Resources
};
