const cf = require("@mapbox/cloudfriend");
// Why am I getting a 504 error? Do I need- security groups and ECSRoles? probably
const Parameters = {
	ImageTag: {
		Description: "The tag for the docker hub image",
		Type: "String"
	},
	ELBSubnets: {
		Description: "ELB subnets",
		Type: "String"
	},
	ContainerCpu: {
		Description: "How much CPU to give to the container. 1024 is 1 cpu. See aws docs for acceptable cpu/mem combinations",
		Default: 512,
		Type: "Number"
	},
	ContainerMemory: {
		Description: "How much memory in megabytes to give to the container. See aws docs for acceptable cpu/mem combinations",
		Default: 1024,
		Type: "Number"
	},
	SSLCertificateIdentifier: {
    	Type: 'String',
    	Description: 'SSL certificate for HTTPS protocol'
  	},
  	DatabaseSize: {
  		Type: "String",
  		Default: "10",
  		Description: "Size of the database, in GB"
  	},
  	DatabaseName: {
  		Type: "String",
  		Description: "Name of the Database"
  	},
  	DatabaseUser: {
  		Type: "String",
  		Description: "Database Username"
  	},
  	DatabasePassword: {
  		Type: "String",
  		Description: "Database User Password"
  	}
};

const Resources = {
	MLEnablerECSCluster: {
		Type: "AWS::ECS::Cluster",
		Properties: {
			ClusterName: cf.join("-", [cf.stackName, "cluster"])
		}
	},
	MLEnablerTaskDefinition: {
		Type: "AWS::ECS::TaskDefinition",
		Properties: {
			Family: cf.stackName,
			Cpu: cf.ref("ContainerCpu"),
			Memory: cf.ref("ContainerMemory"),
			NetworkMode: "awsvpc",
			RequiresCompatibilities: ["FARGATE"],
			// ExecutionRoleArn: "AWS::NoValue",
			// TaskRoleArn: "AWS::NoValue",
			ContainerDefinitions: [
				{
					Name: "app",
					Image: cf.join(":", ["hotosm/ml-enabler", cf.ref("ImageTag")]),
					// Cpu: 256,
					// Memory: 512,
					PortMappings: [
						{
							ContainerPort: 5000
						}
					],
					Environment: [
						{
							Name:"POSTGRES_DB",
							Value: cf.ref("DatabaseName")
						},
						{
							Name:"POSTGRES_USER",
							Value: cf.ref("DatabaseUser")
						},
						{
							Name:"POSTGRES_PASSWORD",
							Value: cf.ref("DatabasePassword")
						},
						{
							Name:"POSTGRES_ENDPOINT",
							Value: cf.getAtt("MLEnablerRDS", "Endpoint.Address")
						},
						{
							Name:"POSTGRES_PORT",
							Value: "5432"
						},
	      				{
	      					Name: "FLASK_APP",
	      					Value: "ml_enabler"
	      				} 
					],
					Essential: true
				},
				{
					Name: "migration",
					Image: cf.join(":", ["hotosm/ml-enabler", cf.ref("ImageTag")]),
					// Cpu: 256, //cf.ref("ContainerCpu"),
					// Memory: 512,
					Environment: [
						{
							Name:"POSTGRES_DB",
							Value: cf.ref("DatabaseName")
						},
						{
							Name:"POSTGRES_USER",
							Value: cf.ref("DatabaseUser")
						},
						{
							Name:"POSTGRES_PASSWORD",
							Value: cf.ref("DatabasePassword")
						},
						{
							Name:"POSTGRES_ENDPOINT",
							Value: cf.getAtt("MLEnablerRDS", "Endpoint.Address")
						},
						{
							Name:"POSTGRES_PORT",
							Value: "5432"
						},
	      				{
	      					Name: "FLASK_APP",
	      					Value: "ml_enabler"
	      				} 
					],
					PortMappings: [
						{
							ContainerPort: 5432
						}
					],
					Command: ["flask","db", "upgrade"],
					Essential: false
				}
			]
		}
	},
	MLEnablerService: {
		Type: "AWS::ECS::Service",
		//DependsOn: cf.ref("MLEnablerALB"),
		Properties: {
			ServiceName: cf.join("-", [cf.stackName, "Service"]),
			Cluster: cf.ref("MLEnablerECSCluster"),
			TaskDefinition: cf.ref("MLEnablerTaskDefinition"),
			LaunchType: "FARGATE",
			HealthCheckGracePeriodSeconds: 300,
			DesiredCount: 1,
			NetworkConfiguration: {
				AwsvpcConfiguration: {
					AssignPublicIp : "ENABLED",
  					SecurityGroups : [ 
  						cf.importValue(
        			 		cf.join("-", ["hotosm-network-production-production-ec2s-security-group", cf.region])
        				)
        			],
  					Subnets : cf.split(",", cf.ref("ELBSubnets"))
				}
			},
			LoadBalancers: [{
				ContainerName: "app",
				ContainerPort: 5000,
				TargetGroupArn: cf.ref("MLEnablerTargetGroup")
			}]
		}
	},
	MLEnablerTargetGroup: {
		Type: "AWS::ElasticLoadBalancingV2::TargetGroup",
	    Properties: {
	      Port: 5000,
	      Protocol: "HTTP",
	      VpcId: cf.importValue(cf.join("-", ["hotosm-network-production", "default-vpc", cf.region])),
	      TargetType: "ip",
	      Matcher: {
	        HttpCode: "200,202,302,304"
	      }
	  }
	},
	MLEnablerALB: {
		Type: "AWS::ElasticLoadBalancingV2::LoadBalancer",
	    Properties: {
	      Name: cf.stackName,
	      SecurityGroups: [
	        cf.importValue(
	          cf.join("-", ["hotosm-network-production-production-elbs-security-group", cf.region])
	        )
	      ],
	      Subnets: cf.split(",", cf.ref("ELBSubnets")),
	      Type: "application"
	    }
	},
	MLEnablerHTTPSListener: {
		Type: 'AWS::ElasticLoadBalancingV2::Listener',
	    Properties: {
	      Certificates: [ {
	        CertificateArn: cf.arn('acm', cf.ref('SSLCertificateIdentifier'))
	      }],
	      DefaultActions: [{
	        Type: 'forward',
	        TargetGroupArn: cf.ref('MLEnablerTargetGroup')
	      }],
	      LoadBalancerArn: cf.ref('MLEnablerALB'),
	      Port: 443,
	      Protocol: 'HTTPS'
	    }
	},
	MLEnablerHTTPListener: {
		Type: 'AWS::ElasticLoadBalancingV2::Listener',
	    Properties: {
	      DefaultActions: [{
	        Type: 'redirect',
	        RedirectConfig: {
	          Protocol: 'HTTPS',
	          Port: '443',
	          Host: '#{host}',
	          Path: '/#{path}',
	          Query: '#{query}',
	          StatusCode: 'HTTP_301'
	        }
	      }],
	      LoadBalancerArn: cf.ref('MLEnablerALB'),
	      Port: 80,
	      Protocol: 'HTTP'
	    }
	},
	MLEnablerRDS: {
		Type: 'AWS::RDS::DBInstance',
	    Properties: {
	        Engine: 'postgres',
	        DBName: "mlenabler",
	        EngineVersion: '11.2',
	        MasterUsername: "mlenabler",
	        MasterUserPassword: "mlenabler",
	        AllocatedStorage: cf.ref('DatabaseSize'),
	        BackupRetentionPeriod: 10,
	        StorageType: 'gp2',
	        DBInstanceClass: 'db.m4.xlarge', 
	        VPCSecurityGroups: [cf.importValue(cf.join('-', ['hotosm-network-production-production-ec2s-security-group', cf.region]))],
		}
	}
};

module.exports = { Parameters, Resources };