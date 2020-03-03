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
                                'ecr:TagResource',
                                'ecr:GetDownloadUrlForLayer',
                                'ecr:BatchGetImage',
                                'ecr:BatchCheckLayerAvailability',
                                'ecr:PutImage',
                                'ecr:InitiateLayerUpload',
                                'ecr:UploadLayerPart',
                                'ecr:CompleteLayerUpload'
                            ],
                            Resource: [ cf.join(['arn:aws:ecr:', cf.region, ':', cf.accountId, ':repository/', cf.ref('BatchECR')]) ]
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
                    Environment: [{
                        Name: 'StackName' ,
                        Value: cf.stackName
                    },{
                        Name: 'AWS_ACCOUNT_ID',
                        Value: cf.accountId
                    },{
                        Name: 'AWS_REGION',
                        Value: cf.region
                    },{
                        Name: 'BATCH_ECR' ,
                        Value: cf.ref('BatchECR')
                    },{
                        Name: 'API_URL',
                        Value: cf.join(['http://', cf.getAtt('MLEnablerELB', 'DNSName')])
                    }],
                    Memory: 4000,
                    Privileged: true,
                    JobRoleArn: cf.getAtt('BatchJobRole', 'Arn'),
                    ReadonlyRootFilesystem: false,
                    Vcpus: 2,
                    Image: cf.join([cf.ref('AWS::AccountId'), '.dkr.ecr.', cf.ref('AWS::Region'), '.amazonaws.com/ml-enabler:task-', cf.ref('GitSha')])
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
