import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class EnhancedRoadmapGenerator:
    def __init__(self):
        """Initialize the roadmap generator"""
        self.lambda_client = boto3.client('lambda')
        self.COST_ESTIMATOR_FUNCTION = os.environ.get('COST_ESTIMATOR_FUNCTION')
        self.risk_levels = {
            'Low': {'score': 1, 'multiplier': 1.0},
            'Medium': {'score': 2, 'multiplier': 1.5},
            'High': {'score': 3, 'multiplier': 2.0}
        }

    def generate_migration_roadmap(self, servers: List[dict], start_date: Optional[str] = None) -> dict:
        """Generate comprehensive migration roadmap"""
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
            
        # Convert start_date string to datetime
        current_date = datetime.strptime(start_date, '%Y-%m-%d')

        # Sort servers by priority and dependencies
        sorted_servers = self.prioritize_servers(servers)
        
        # Generate phases for each server
        timeline = []
        all_risks = []
        total_cost = 0
        
        for server in sorted_servers:
            # Calculate phase durations and details
            server_phases = self.generate_server_phases(server, current_date)
            
            # Calculate server-specific risks
            risks = self.assess_server_risks(server)
            all_risks.extend(risks)
            
            # Get cost estimates
            cost_estimate = self.get_cost_estimate(server)
            total_cost += cost_estimate.get('total', 0)
            
            # Create timeline entry
            timeline_entry = {
                'server': {
                    'id': server['serverId'],
                    'name': server['serverName'],
                    'type': server.get('serverType', 'unknown')
                },
                'phases': server_phases,
                'startDate': current_date.strftime('%Y-%m-%d'),
                'endDate': (current_date + self.calculate_total_duration(server_phases)).strftime('%Y-%m-%d'),
                'risks': risks,
                'mitigationStrategies': self.generate_mitigation_strategies(risks),
                'costEstimate': cost_estimate,
                'dependencies': server.get('dependencies', []),
                'criticalPath': self.is_critical_path(server, sorted_servers)
            }
            
            timeline.append(timeline_entry)
            # Update current_date for next server
            current_date += self.calculate_total_duration(server_phases) + timedelta(days=7)  # 1 week buffer

        # Generate comprehensive project plan
        project_plan = {
            'timeline': timeline,
            'summary': self.generate_project_summary(timeline, total_cost, all_risks),
            'riskManagement': self.generate_risk_management_plan(all_risks),
            'milestones': self.generate_key_milestones(timeline),
            'recommendations': self.generate_recommendations(timeline)
        }

        return project_plan

    def prioritize_servers(self, servers: List[dict]) -> List[dict]:
        """Prioritize servers based on multiple factors"""
        scored_servers = []
        for server in servers:
            score = self.calculate_priority_score(server)
            scored_servers.append((score, server))
            
        # Sort by score in descending order
        scored_servers.sort(reverse=True, key=lambda x: x[0])
        return [server for score, server in scored_servers]

    def calculate_priority_score(self, server: dict) -> float:
        """Calculate priority score for server"""
        score = 0
        
        # Complexity factor
        complexity = server.get('complexity', {}).get('level', 'Medium')
        score += self.risk_levels[complexity]['score'] * 2

        # Dependencies factor
        dependencies = len(server.get('dependencies', []))
        score += min(dependencies * 0.5, 5)  # Cap at 5 points

        # Resource utilization
        metrics = server.get('metrics', {})
        if metrics:
            cpu_util = metrics.get('cpu', {}).get('utilization', 0)
            mem_util = metrics.get('memory', {}).get('utilization', 0)
            avg_util = (cpu_util + mem_util) / 2
            score += avg_util / 20  # Max 5 points

        # Business impact
        if server.get('businessCritical', False):
            score += 3

        return score

    def generate_server_phases(self, server: dict, start_date: datetime) -> List[dict]:
        """Generate detailed phases for server migration"""
        strategy = server.get('migrationStrategy', {}).get('strategy', 'Rehost')
        complexity = server.get('complexity', {}).get('level', 'Medium')
        
        phase_templates = {
            'Rehost': [
                {
                    'name': 'Assessment',
                    'duration': 5,
                    'tasks': [
                        'Infrastructure assessment',
                        'Dependency mapping',
                        'Performance baseline creation',
                        'Migration tool selection'
                    ],
                    'deliverables': [
                        'Assessment report',
                        'Dependency map',
                        'Performance baseline document'
                    ],
                    'validation': [
                        'Infrastructure compatibility verified',
                        'All dependencies identified',
                        'Baseline metrics established'
                    ]
                },
                {
                    'name': 'Planning',
                    'duration': 7,
                    'tasks': [
                        'Migration strategy documentation',
                        'Resource allocation',
                        'Schedule creation',
                        'Risk mitigation planning'
                    ],
                    'deliverables': [
                        'Detailed migration plan',
                        'Resource allocation plan',
                        'Risk mitigation plan'
                    ],
                    'validation': [
                        'Plan approved by stakeholders',
                        'Resources confirmed',
                        'Risks documented and assessed'
                    ]
                },
                {
                    'name': 'Preparation',
                    'duration': 10,
                    'tasks': [
                        'Target environment setup',
                        'Migration tools installation',
                        'Backup verification',
                        'Test migration run'
                    ],
                    'deliverables': [
                        'Environment readiness report',
                        'Backup verification report',
                        'Test migration results'
                    ],
                    'validation': [
                        'Target environment ready',
                        'Backups verified',
                        'Test migration successful'
                    ]
                },
                {
                    'name': 'Migration',
                    'duration': 5,
                    'tasks': [
                        'Data migration',
                        'Application migration',
                        'Configuration migration',
                        'Initial testing'
                    ],
                    'deliverables': [
                        'Migration execution report',
                        'Initial test results'
                    ],
                    'validation': [
                        'All components migrated',
                        'Initial tests passed'
                    ]
                },
                {
                    'name': 'Validation',
                    'duration': 7,
                    'tasks': [
                        'Comprehensive testing',
                        'Performance validation',
                        'Security validation',
                        'User acceptance testing'
                    ],
                    'deliverables': [
                        'Test results report',
                        'Performance validation report',
                        'Security validation report',
                        'UAT sign-off'
                    ],
                    'validation': [
                        'All tests passed',
                        'Performance metrics met',
                        'Security requirements met',
                        'User acceptance received'
                    ]
                },
                {
                    'name': 'Cutover',
                    'duration': 3,
                    'tasks': [
                        'DNS cutover',
                        'Final data sync',
                        'Go-live verification',
                        'Post-migration monitoring'
                    ],
                    'deliverables': [
                        'Cutover checklist',
                        'Go-live report'
                    ],
                    'validation': [
                        'Cutover successful',
                        'System operational',
                        'No critical issues'
                    ]
                }
            ],
            'Replatform': [
                # Similar structure with platform-specific tasks
            ],
            'Refactor': [
                # Similar structure with refactoring-specific tasks
            ]
        }

        # Get base phases for the strategy
        phases = phase_templates.get(strategy, phase_templates['Rehost'])
        
        # Adjust durations based on complexity
        complexity_multiplier = self.risk_levels[complexity]['multiplier']
        current_date = start_date
        
        # Enhance phases with dates and adjusted durations
        enhanced_phases = []
        for phase in phases:
            adjusted_duration = int(phase['duration'] * complexity_multiplier)
            end_date = current_date + timedelta(days=adjusted_duration)
            
            enhanced_phase = {
                'name': phase['name'],
                'startDate': current_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'duration': adjusted_duration,
                'tasks': phase['tasks'],
                'deliverables': phase['deliverables'],
                'validation': phase['validation'],
                'risks': self.assess_phase_risks(phase['name'], strategy, complexity),
                'mitigation': self.get_phase_mitigation_strategies(phase['name'], strategy)
            }
            
            enhanced_phases.append(enhanced_phase)
            current_date = end_date + timedelta(days=1)  # 1 day buffer between phases
            
        return enhanced_phases

    def assess_server_risks(self, server: dict) -> List[dict]:
        """Assess comprehensive risks for server migration"""
        risks = []
        
        # Technical risks
        metrics = server.get('metrics', {})
        if metrics.get('cpu', {}).get('utilization', 0) > 80:
            risks.append({
                'category': 'Technical',
                'type': 'Performance',
                'description': 'High CPU utilization may impact migration',
                'severity': 'High',
                'probability': 'High',
                'impact': 'Migration performance degradation and extended downtime'
            })

        # Dependency risks
        dependencies = server.get('dependencies', [])
        if len(dependencies) > 5:
            risks.append({
                'category': 'Dependencies',
                'type': 'Complexity',
                'description': 'High number of dependencies increases migration complexity',
                'severity': 'Medium',
                'probability': 'High',
                'impact': 'Extended migration timeline and increased failure risk'
            })

        # Data risks
        storage = metrics.get('storage', {})
        if storage.get('used', 0) > storage.get('total', 1) * 0.8:
            risks.append({
                'category': 'Data',
                'type': 'Storage',
                'description': 'High storage utilization',
                'severity': 'Medium',
                'probability': 'Medium',
                'impact': 'Potential data transfer issues and increased migration time'
            })

        # Application risks
        for app in server.get('applications', []):
            if app.get('version', 'unknown') == 'unknown':
                risks.append({
                    'category': 'Application',
                    'type': 'Compatibility',
                    'description': f"Unknown version for {app.get('name')}",
                    'severity': 'Medium',
                    'probability': 'Medium',
                    'impact': 'Potential compatibility issues in cloud environment'
                })

        return risks

    def generate_mitigation_strategies(self, risks: List[dict]) -> List[dict]:
        """Generate mitigation strategies for identified risks"""
        strategies = []
        for risk in risks:
            strategy = {
                'risk': risk['description'],
                'strategies': [],
                'contingency': [],
                'owner': 'Migration Team'
            }

            if risk['category'] == 'Technical':
                strategy['strategies'] = [
                    'Conduct pre-migration performance optimization',
                    'Schedule migration during low-utilization periods',
                    'Provision additional temporary resources'
                ]
                strategy['contingency'] = [
                    'Rollback plan with defined triggers',
                    'Alternative migration approach identification'
                ]

            elif risk['category'] == 'Dependencies':
                strategy['strategies'] = [
                    'Detailed dependency mapping and validation',
                    'Phased migration approach',
                    'Dedicated dependency testing phase'
                ]
                strategy['contingency'] = [
                    'Manual dependency handling procedures',
                    'Temporary maintenance of hybrid connectivity'
                ]

            elif risk['category'] == 'Data':
                strategy['strategies'] = [
                    'Pre-migration data cleanup',
                    'Incremental data transfer approach',
                    'Bandwidth optimization techniques'
                ]
                strategy['contingency'] = [
                    'Alternative data transfer methods',
                    'Emergency storage provisioning plan'
                ]

            strategies.append(strategy)

        return strategies

    def get_cost_estimate(self, server: dict) -> dict:
        """Get cost estimate from cost estimator Lambda"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.COST_ESTIMATOR_FUNCTION,
                InvocationType='RequestResponse',
                Payload=json.dumps({'serverData': server})
            )
            return json.loads(response['Payload'].read())
        except Exception as e:
            print(f"Error getting cost estimate: {str(e)}")
            return {'total': 0, 'error': str(e)}

    def calculate_total_duration(self, phases: List[dict]) -> timedelta:
        """Calculate total duration for all phases"""
        total_days = sum(phase['duration'] for phase in phases)
        return timedelta(days=total_days)

    def is_critical_path(self, server: dict, all_servers: List[dict]) -> bool:
        """Determine if server is on critical path"""
        dependent_count = sum(
            1 for s in all_servers 
            if server['serverId'] in [d['serverId'] for d in s.get('dependencies', [])]
        )
        
        return (
            dependent_count >= 2 or
            server.get('metrics', {}).get('cpu', {}).get('utilization', 0) > 80 or
            server.get('businessCritical', False)
        )

    def assess_phase_risks(self, phase_name: str, strategy: str, complexity: str) -> List[dict]:
        """Assess risks specific to migration phase"""
        risks = []
        
        # Common risks for all phases
        base_risks = {
            'Assessment': [
                {
                    'type': 'Incomplete Discovery',
                    'description': 'Missing critical components or dependencies',
                    'severity': 'High',
                    'mitigation': 'Multiple discovery tools and manual verification'
                },
                {
                    'type': 'Inaccurate Baseline',
                    'description': 'Performance baseline not representative',
                    'severity': 'Medium',
                    'mitigation': 'Extended baseline monitoring period'
                }
            ],
            'Planning': [
                {
                    'type': 'Resource Availability',
                    'description': 'Required resources not available when needed',
                    'severity': 'Medium',
                    'mitigation': 'Early resource booking and backup resource identification'
                },
                {
                    'type': 'Schedule Conflicts',
                    'description': 'Conflicts with other business initiatives',
                    'severity': 'Medium',
                    'mitigation': 'Stakeholder alignment and schedule buffering'
                }
            ],
            'Preparation': [
                {
                    'type': 'Environment Setup',
                    'description': 'Target environment configuration issues',
                    'severity': 'Medium',
                    'mitigation': 'Automated environment validation and testing'
                },
                {
                    'type': 'Tool Compatibility',
                    'description': 'Migration tools compatibility issues',
                    'severity': 'High',
                    'mitigation': 'Pre-migration tool testing and validation'
                }
            ],
            'Migration': [
                {
                    'type': 'Data Transfer',
                    'description': 'Data transfer failures or corruption',
                    'severity': 'High',
                    'mitigation': 'Checksums and incremental transfer validation'
                },
                {
                    'type': 'Extended Downtime',
                    'description': 'Migration takes longer than planned window',
                    'severity': 'High',
                    'mitigation': 'Detailed rehearsal and rollback procedures'
                }
            ],
            'Validation': [
                {
                    'type': 'Test Coverage',
                    'description': 'Insufficient testing scenarios',
                    'severity': 'Medium',
                    'mitigation': 'Comprehensive test plan with business validation'
                },
                {
                    'type': 'Performance Issues',
                    'description': 'Performance not meeting requirements',
                    'severity': 'High',
                    'mitigation': 'Performance testing and optimization cycles'
                }
            ],
            'Cutover': [
                {
                    'type': 'Service Disruption',
                    'description': 'Unexpected service disruption during cutover',
                    'severity': 'High',
                    'mitigation': 'Detailed cutover plan with rollback points'
                },
                {
                    'type': 'Data Synchronization',
                    'description': 'Final data sync issues',
                    'severity': 'High',
                    'mitigation': 'Multiple sync verification points'
                }
            ]
        }

        # Add base risks for the phase
        phase_risks = base_risks.get(phase_name, [])
        risks.extend(phase_risks)

        # Add strategy-specific risks
        if strategy == 'Replatform':
            risks.extend(self._get_replatform_risks(phase_name))
        elif strategy == 'Refactor':
            risks.extend(self._get_refactor_risks(phase_name))

        # Adjust risk severity based on complexity
        if complexity == 'High':
            for risk in risks:
                if risk['severity'] == 'Medium':
                    risk['severity'] = 'High'

        return risks

    def _get_replatform_risks(self, phase_name: str) -> List[dict]:
        """Get risks specific to replatform strategy"""
        strategy_risks = {
            'Assessment': [
                {
                    'type': 'Platform Compatibility',
                    'description': 'Application compatibility with new platform',
                    'severity': 'High',
                    'mitigation': 'Detailed compatibility assessment and testing'
                }
            ],
            'Migration': [
                {
                    'type': 'Configuration Translation',
                    'description': 'Error in platform-specific configuration translation',
                    'severity': 'Medium',
                    'mitigation': 'Automated configuration validation tools'
                }
            ]
        }
        return strategy_risks.get(phase_name, [])

    def _get_refactor_risks(self, phase_name: str) -> List[dict]:
        """Get risks specific to refactor strategy"""
        strategy_risks = {
            'Assessment': [
                {
                    'type': 'Architecture Changes',
                    'description': 'Incomplete understanding of required architectural changes',
                    'severity': 'High',
                    'mitigation': 'Architecture review board validation'
                }
            ],
            'Migration': [
                {
                    'type': 'Code Refactoring',
                    'description': 'Unexpected code dependencies or complexity',
                    'severity': 'High',
                    'mitigation': 'Incremental refactoring approach with testing'
                }
            ]
        }
        return strategy_risks.get(phase_name, [])

    def get_phase_mitigation_strategies(self, phase_name: str, strategy: str) -> List[dict]:
        """Get mitigation strategies for phase risks"""
        mitigation_strategies = []
        
        # Common mitigation strategies
        base_strategies = {
            'Assessment': [
                {
                    'category': 'Discovery',
                    'actions': [
                        'Use multiple discovery tools',
                        'Conduct manual verification',
                        'Validate with stakeholders'
                    ],
                    'verification': 'Complete discovery sign-off checklist'
                }
            ],
            'Planning': [
                {
                    'category': 'Resource Management',
                    'actions': [
                        'Create detailed resource plan',
                        'Identify backup resources',
                        'Establish escalation paths'
                    ],
                    'verification': 'Resource availability confirmation'
                }
            ]
        }
        
        # Get base strategies
        phase_strategies = base_strategies.get(phase_name, [])
        mitigation_strategies.extend(phase_strategies)
        
        # Add strategy-specific mitigations
        if strategy == 'Replatform':
            mitigation_strategies.extend(self._get_replatform_mitigations(phase_name))
        elif strategy == 'Refactor':
            mitigation_strategies.extend(self._get_refactor_mitigations(phase_name))
            
        return mitigation_strategies

    def generate_project_summary(self, timeline: List[dict], total_cost: float, 
                               all_risks: List[dict]) -> dict:
        """Generate comprehensive project summary"""
        start_date = min(entry['startDate'] for entry in timeline)
        end_date = max(entry['endDate'] for entry in timeline)
        
        return {
            'duration': {
                'startDate': start_date,
                'endDate': end_date,
                'totalDays': (datetime.strptime(end_date, '%Y-%m-%d') - 
                            datetime.strptime(start_date, '%Y-%m-%d')).days
            },
            'servers': {
                'total': len(timeline),
                'byStrategy': self._count_servers_by_strategy(timeline),
                'byComplexity': self._count_servers_by_complexity(timeline)
            },
            'costs': {
                'total': total_cost,
                'byCategory': self._break_down_costs_by_category(timeline)
            },
            'risks': {
                'total': len(all_risks),
                'byLevel': self._count_risks_by_level(all_risks),
                'topRisks': self._identify_top_risks(all_risks)
            },
            'dependencies': self._analyze_dependencies(timeline),
            'criticalPath': self._identify_critical_path_summary(timeline)
        }

    def _count_servers_by_strategy(self, timeline: List[dict]) -> dict:
        """Count servers by migration strategy"""
        counts = {'Rehost': 0, 'Replatform': 0, 'Refactor': 0}
        for entry in timeline:
            strategy = entry.get('migrationStrategy', {}).get('strategy', 'Rehost')
            counts[strategy] = counts.get(strategy, 0) + 1
        return counts

    def _break_down_costs_by_category(self, timeline: List[dict]) -> dict:
        """Break down costs by category"""
        costs = {
            'infrastructure': 0,
            'labor': 0,
            'tools': 0,
            'training': 0,
            'contingency': 0
        }
        
        for entry in timeline:
            cost_estimate = entry.get('costEstimate', {})
            costs['infrastructure'] += cost_estimate.get('infrastructure', 0)
            costs['labor'] += cost_estimate.get('labor', 0)
            costs['tools'] += cost_estimate.get('tools', 0)
            costs['training'] += cost_estimate.get('training', 0)
            costs['contingency'] += cost_estimate.get('contingency', 0)
            
        return costs

    def generate_key_milestones(self, timeline: List[dict]) -> List[dict]:
        """Generate key project milestones"""
        milestones = []
        
        # Project start
        start_date = min(entry['startDate'] for entry in timeline)
        milestones.append({
            'name': 'Project Kickoff',
            'date': start_date,
            'type': 'project',
            'description': 'Project initiation and team onboarding',
            'criteria': [
                'Project charter signed',
                'Team onboarded',
                'Initial planning complete'
            ]
        })
        
        # Key server migrations
        for entry in timeline:
            if entry.get('criticalPath'):
                milestones.append({
                    'name': f"Critical Server Migration - {entry['server']['name']}",
                    'date': entry['startDate'],
                    'type': 'migration',
                    'description': f"Migration of critical server {entry['server']['name']}",
                    'criteria': [
                        'Pre-migration validation complete',
                        'All dependencies ready',
                        'Rollback plan approved'
                    ]
                })
                
        # Project completion
        end_date = max(entry['endDate'] for entry in timeline)
        milestones.append({
            'name': 'Project Completion',
            'date': end_date,
            'type': 'project',
            'description': 'Migration project completion and handover',
            'criteria': [
                'All servers migrated',
                'Performance validation complete',
                'Documentation complete',
                'Operations handover complete'
            ]
        })
        
        return milestones

def lambda_handler(event, context):
    """Lambda handler for the roadmap generator"""
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        servers = body.get('servers', [])
        start_date = body.get('startDate')
        
        if not servers:
            raise ValueError("Server data is required")
            
        # Initialize generator and create roadmap
        generator = EnhancedRoadmapGenerator()
        roadmap = generator.generate_migration_roadmap(servers, start_date)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(roadmap)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Error generating migration roadmap: {str(e)}'
            })
        }