'use strict';

const cf = require('@mapbox/cloudfriend');

const stack = {
    Resources: {
        BatchECR: {
            Type: 'AWS::ECR::Repository',
            Properties: {
                RepositoryName: cf.join('-', [cf.stackName, 'ecr'])
            }
        },
        BatchServiceRole: {
            Type: 'AWS::IAM::Role',
            Properties: {
                AssumeRolePolicyDocument: {
                    Version: '2012-10-17',
                    Statement: [{
                        Effect: 'Allow',
                        Principal: {
                            Service: 'batch.amazonaws.com'
                        },
                        Action: 'sts:AssumeRole'
                    }]
                },
                ManagedPolicyArns: ['arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole'],
                Path: '/service-role/'
            }
        },
        BatchInstanceRole: {
            Type: 'AWS::IAM::Role',
            Properties: {
                AssumeRolePolicyDocument: {
                    Version: '2012-10-17',
                    Statement: [{
                        Effect: 'Allow',
                        Principal: {
                            Service: 'ec2.amazonaws.com'
                        },
                        Action: 'sts:AssumeRole'
                    }]
                },
                ManagedPolicyArns: ['arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role'],
                Path: '/'
            }
        },
        BatchInstanceProfile: {
            Type: 'AWS::IAM::InstanceProfile',
            Properties: {
                Roles: [cf.ref('BatchInstanceRole')],
                Path: '/'
            }
        },
        BatchJobRole: {
            Type: 'AWS::IAM::Role',
            Properties: {
                AssumeRolePolicyDocument: {
                    Version: '2012-10-17',
                    Statement: [{
                        Effect: 'Allow',
                        Principal: {
                            Service: 'ecs-tasks.amazonaws.com'
                        },
                        Action: 'sts:AssumeRole'
                    }]
                },
                Policies: [{
                    PolicyName: 'batch-job-policy',
                    PolicyDocument: {
                        Statement: [{
                            Effect: 'Allow',
                            Action: [
                                'ecr:GetAuthorizationToken',
                                'ecr:TagResource',
                                'ecr:GetDownloadUrlForLayer',
                                'ecr:BatchGetImage',
                                'ecr:BatchCheckLayerAvailability',
                                'ecr:PutImage',
                                'ecr:InitiateLayerUpload',
                                'ecr:UploadLayerPart',
                                'ecr:CompleteLayerUpload'
                            ],
                            Resource: [ '*' ]
                        },{
                            Effect: 'Allow',
                            Action: [
                                'batch:DescribeJobs'
                            ],
                            Resource: ['*']
                        },{
                            Effect: 'Allow',
                            Action: [
                                's3:GetObject',
                                's3:DeleteObject',
                                's3:AbortMultipartUpload',
                                's3:GetObjectAcl',
                                's3:ListMultipartUploadParts',
                                's3:PutObject',
                                's3:PutObjectAcl'
                            ],
                            Resource: [ cf.join(['arn:aws:s3:::', cf.ref('MLEnablerBucket'), '/*']) ]
                        }]
                    }
                }],
                Path: '/'
            }
        },
        BatchGpuComputeEnvironment: {
            Type: 'AWS::Batch::ComputeEnvironment',
            Properties: {
                Type: 'MANAGED',
                ServiceRole: cf.getAtt('BatchServiceRole', 'Arn'),
                ComputeEnvironmentName: cf.join('-', ['batch-gpu', cf.ref('AWS::StackName')]),
                ComputeResources: {
                    ImageId: 'ami-07eb64b216d4d3522',
                    MaxvCpus: 128,
                    DesiredvCpus: 32,
                    MinvCpus: 0,
                    SecurityGroupIds: [cf.ref('BatchSecurityGroup')],
                    Subnets:  [
                        cf.ref('MLEnablerSubA'),
                        cf.ref('MLEnablerSubB')
                    ],
                    Type : 'EC2',
                    InstanceRole : cf.getAtt('BatchInstanceProfile', 'Arn'),
                    InstanceTypes : ['p2', 'p3']
                },
                State: 'ENABLED'
            }
        },
        BatchComputeEnvironment: {
            Type: 'AWS::Batch::ComputeEnvironment',
            Properties: {
                Type: 'MANAGED',
                ServiceRole: cf.getAtt('BatchServiceRole', 'Arn'),
                ComputeEnvironmentName: cf.join('-', ['batch', cf.ref('AWS::StackName')]),
                ComputeResources: {
                    ImageId: 'ami-056807e883f197989',
                    MaxvCpus: 128,
                    DesiredvCpus: 32,
                    MinvCpus: 0,
                    SecurityGroupIds: [cf.ref('BatchSecurityGroup')],
                    Subnets:  [
                        cf.ref('MLEnablerSubA'),
                        cf.ref('MLEnablerSubB')
                    ],
                    Type : 'EC2',
                    InstanceRole : cf.getAtt('BatchInstanceProfile', 'Arn'),
                    InstanceTypes : ['optimal']
                },
                State: 'ENABLED'
            }
        },
        BatchGpuJobDefinition: {
            Type: 'AWS::Batch::JobDefinition',
            Properties: {
                Type: 'container',
                JobDefinitionName: cf.join('-', [cf.stackName, 'gpu-job']),
                RetryStrategy: {
                    Attempts: 1
                },
                Parameters: { },
                ContainerProperties: {
                    Command: ['python', './task.py'],
                    Environment: [
                        { Name: 'StackName' , Value: cf.stackName },
                        { Name: 'MACHINE_AUTH', Value: cf.ref('MachineAuth') },
                        { Name: 'AWS_ACCOUNT_ID', Value: cf.accountId },
                        { Name: 'AWS_REGION', Value: cf.region },
                        { Name: 'API_URL', Value: cf.join(['http://', cf.getAtt('MLEnablerELB', 'DNSName')]) },
                        { Name: 'ASSET_BUCKET', Value: cf.ref('MLEnablerBucket') }
                    ],
                    Memory: 4000,
                    Privileged: true,
                    JobRoleArn: cf.getAtt('BatchJobRole', 'Arn'),
                    ReadonlyRootFilesystem: false,
                    Vcpus: 2,
                    Image: cf.join([cf.ref('AWS::AccountId'), '.dkr.ecr.', cf.ref('AWS::Region'), '.amazonaws.com/ml-enabler:task-retrain-', cf.ref('GitSha')])
                }
            }
        },
        BatchGpuJobQueue: {
            'Type': 'AWS::Batch::JobQueue',
            'Properties': {
                'ComputeEnvironmentOrder': [{
                    'Order': 1,
                    'ComputeEnvironment': cf.ref('BatchGpuComputeEnvironment')
                }],
                'State': 'ENABLED',
                'Priority': 1,
                'JobQueueName': cf.join('-', [cf.stackName, 'gpu-queue'])
            }
        },
        BatchJobDefinition: {
            Type: 'AWS::Batch::JobDefinition',
            Properties: {
                Type: 'container',
                JobDefinitionName: cf.join('-', [cf.stackName, 'job']),
                RetryStrategy: {
                    Attempts: 1
                },
                Parameters: { },
                ContainerProperties: {
                    Command: ['./task.js'],
                    Environment: [
                        { Name: 'StackName' , Value: cf.stackName },
                        { Name: 'BATCH_ECR' , Value: cf.ref('BatchECR') },
                        { Name: 'MACHINE_AUTH', Value: cf.ref('MachineAuth') },
                        { Name: 'AWS_ACCOUNT_ID', Value: cf.accountId },
                        { Name: 'AWS_REGION', Value: cf.region },
                        { Name: 'API_URL', Value: cf.join(['http://', cf.getAtt('MLEnablerELB', 'DNSName')]) }
                    ],
                    Memory: 4000,
                    Privileged: true,
                    JobRoleArn: cf.getAtt('BatchJobRole', 'Arn'),
                    ReadonlyRootFilesystem: false,
                    Vcpus: 2,
                    Image: cf.join([cf.ref('AWS::AccountId'), '.dkr.ecr.', cf.ref('AWS::Region'), '.amazonaws.com/ml-enabler:task-build-', cf.ref('GitSha')])
                }
            }
        },
        BatchSecurityGroup: {
            'Type': 'AWS::EC2::SecurityGroup',
            'Properties': {
                'VpcId': cf.ref('MLEnablerVPC'),
                'GroupDescription': 'Batch Security Group',
                SecurityGroupIngress: []
            }
        },
        BatchJobQueue: {
            'Type': 'AWS::Batch::JobQueue',
            'Properties': {
                'ComputeEnvironmentOrder': [{
                    'Order': 1,
                    'ComputeEnvironment': cf.ref('BatchComputeEnvironment')
                }],
                'State': 'ENABLED',
                'Priority': 1,
                'JobQueueName': cf.join('-', [cf.stackName, 'queue'])
            }
        }
    }
};

module.exports = stack;
