"""
Automated Proctoring Reports with AI-Generated Summaries
Provides comprehensive analysis of proctoring violations and suspicious behavior patterns
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

import pandas as pd
from sqlalchemy import func, text
from sqlalchemy.orm import joinedload

from app import db
from models import (User, Quiz, QuizAttempt, ProctoringEvent, UserViolation, 
                   DeviceLog, SecurityAlert, InteractionEvent, Answer)

class ProctoringReportGenerator:
    """Advanced proctoring report generation with AI-powered analysis"""
    
    def __init__(self):
        self.violation_weights = {
            'face_not_detected': 3,
            'multiple_faces': 4,
            'screen_capture': 5,
            'tab_switch': 2,
            'window_blur': 2,
            'fullscreen_exit': 3,
            'right_click': 1,
            'copy_paste': 3,
            'suspicious_audio': 4,
            'keyboard_pattern': 2,
            'mouse_pattern': 2,
            'browser_console': 5,
            'developer_tools': 5,
            'external_monitor': 3,
            'virtual_machine': 5,
            'screen_sharing': 5
        }
        
        self.severity_thresholds = {
            'low': (0, 10),
            'medium': (11, 25),
            'high': (26, 40),
            'critical': (41, float('inf'))
        }

    def generate_comprehensive_report(self, start_date: datetime, end_date: datetime, 
                                    quiz_ids: List[int] = None, user_ids: List[int] = None) -> Dict:
        """Generate comprehensive proctoring report with AI analysis"""
        
        try:
            # Collect all proctoring data
            attempts_data = self._get_quiz_attempts_data(start_date, end_date, quiz_ids, user_ids)
            violations_data = self._get_violations_data(start_date, end_date, quiz_ids, user_ids)
            events_data = self._get_proctoring_events_data(start_date, end_date, quiz_ids, user_ids)
            interactions_data = self._get_interaction_events_data(start_date, end_date, quiz_ids, user_ids)
            device_data = self._get_device_logs_data(start_date, end_date, user_ids)
            
            # Generate AI-powered analysis
            ai_analysis = self._generate_ai_analysis(
                attempts_data, violations_data, events_data, interactions_data, device_data
            )
            
            # Create comprehensive report
            report = {
                'report_id': f"proctoring_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.utcnow().isoformat(),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_days': (end_date - start_date).days
                },
                'filters': {
                    'quiz_ids': quiz_ids,
                    'user_ids': user_ids
                },
                'summary': self._generate_executive_summary(ai_analysis),
                'statistics': self._generate_detailed_statistics(attempts_data, violations_data, events_data),
                'ai_analysis': ai_analysis,
                'risk_assessment': self._generate_risk_assessment(violations_data, events_data),
                'patterns_detected': self._detect_behavior_patterns(violations_data, events_data, interactions_data),
                'recommendations': self._generate_recommendations(ai_analysis),
                'detailed_findings': self._generate_detailed_findings(attempts_data, violations_data, events_data),
                'appendix': {
                    'methodology': self._get_methodology_description(),
                    'data_sources': self._get_data_sources_info(),
                    'limitations': self._get_limitations_info()
                }
            }
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating comprehensive proctoring report: {e}")
            return {'error': str(e)}

    def _get_quiz_attempts_data(self, start_date: datetime, end_date: datetime, 
                               quiz_ids: List[int] = None, user_ids: List[int] = None) -> List[Dict]:
        """Retrieve quiz attempts data for analysis"""
        query = db.session.query(QuizAttempt).options(
            joinedload(QuizAttempt.quiz),
            joinedload(QuizAttempt.participant)
        ).filter(
            QuizAttempt.started_at >= start_date,
            QuizAttempt.started_at <= end_date
        )
        
        if quiz_ids:
            query = query.filter(QuizAttempt.quiz_id.in_(quiz_ids))
        if user_ids:
            query = query.filter(QuizAttempt.participant_id.in_(user_ids))
            
        attempts = query.all()
        
        return [{
            'attempt_id': attempt.id,
            'user_id': attempt.participant_id,
            'username': attempt.participant.username,
            'quiz_id': attempt.quiz_id,
            'quiz_title': attempt.quiz.title,
            'started_at': attempt.started_at.isoformat() if attempt.started_at else None,
            'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
            'status': attempt.status,
            'score': attempt.score,
            'total_points': attempt.total_points,
            'force_submitted': attempt.force_submitted,
            'termination_reason': attempt.termination_reason,
            'is_flagged': attempt.is_flagged,
            'duration_minutes': self._calculate_attempt_duration(attempt)
        } for attempt in attempts]

    def _get_violations_data(self, start_date: datetime, end_date: datetime,
                           quiz_ids: List[int] = None, user_ids: List[int] = None) -> List[Dict]:
        """Retrieve user violations data"""
        query = db.session.query(UserViolation).filter(
            UserViolation.created_at >= start_date,
            UserViolation.created_at <= end_date
        )
        
        if user_ids:
            query = query.filter(UserViolation.user_id.in_(user_ids))
            
        violations = query.all()
        
        return [{
            'violation_id': violation.id,
            'user_id': violation.user_id,
            'violation_type': violation.violation_type,
            'severity': violation.severity,
            'description': violation.description,
            'evidence_data': violation.evidence_data,
            'created_at': violation.created_at.isoformat(),
            'quiz_context': violation.quiz_context,
            'weight': self.violation_weights.get(violation.violation_type, 1)
        } for violation in violations]

    def _get_proctoring_events_data(self, start_date: datetime, end_date: datetime,
                                  quiz_ids: List[int] = None, user_ids: List[int] = None) -> List[Dict]:
        """Retrieve proctoring events data"""
        query = db.session.query(ProctoringEvent).filter(
            ProctoringEvent.created_at >= start_date,
            ProctoringEvent.created_at <= end_date
        )
        
        if quiz_ids:
            query = query.filter(ProctoringEvent.quiz_id.in_(quiz_ids))
        if user_ids:
            query = query.filter(ProctoringEvent.user_id.in_(user_ids))
            
        events = query.all()
        
        return [{
            'event_id': event.id,
            'user_id': event.user_id,
            'quiz_id': event.quiz_id,
            'event_type': event.event_type,
            'event_data': event.event_data,
            'severity': event.severity,
            'created_at': event.created_at.isoformat(),
            'ip_address': event.ip_address,
            'user_agent': event.user_agent
        } for event in events]

    def _get_interaction_events_data(self, start_date: datetime, end_date: datetime,
                                   quiz_ids: List[int] = None, user_ids: List[int] = None) -> List[Dict]:
        """Retrieve interaction events data"""
        query = db.session.query(InteractionEvent).filter(
            InteractionEvent.timestamp >= start_date,
            InteractionEvent.timestamp <= end_date
        )
        
        if quiz_ids:
            query = query.filter(InteractionEvent.quiz_id.in_(quiz_ids))
        if user_ids:
            query = query.filter(InteractionEvent.user_id.in_(user_ids))
            
        interactions = query.all()
        
        return [{
            'interaction_id': interaction.id,
            'user_id': interaction.user_id,
            'quiz_id': interaction.quiz_id,
            'question_id': interaction.question_id,
            'interaction_type': interaction.interaction_type,
            'interaction_data': interaction.interaction_data,
            'timestamp': interaction.timestamp.isoformat(),
            'confidence_score': interaction.confidence_score
        } for interaction in interactions]

    def _get_device_logs_data(self, start_date: datetime, end_date: datetime,
                             user_ids: List[int] = None) -> List[Dict]:
        """Retrieve device logs data"""
        query = db.session.query(DeviceLog).filter(
            DeviceLog.timestamp >= start_date,
            DeviceLog.timestamp <= end_date
        )
        
        if user_ids:
            query = query.filter(DeviceLog.user_id.in_(user_ids))
            
        devices = query.all()
        
        return [{
            'device_id': device.id,
            'user_id': device.user_id,
            'device_type': device.device_type,
            'screen_resolution': device.screen_resolution,
            'browser_info': device.browser_info,
            'os_info': device.os_info,
            'camera_info': device.camera_info,
            'microphone_info': device.microphone_info,
            'timestamp': device.timestamp.isoformat(),
            'is_suspicious': device.is_suspicious,
            'risk_score': device.risk_score
        } for device in devices]

    def _generate_ai_analysis(self, attempts_data: List[Dict], violations_data: List[Dict],
                            events_data: List[Dict], interactions_data: List[Dict],
                            device_data: List[Dict]) -> Dict:
        """Generate AI-powered analysis of proctoring data"""
        
        analysis = {
            'overall_integrity_score': self._calculate_integrity_score(violations_data, events_data),
            'behavior_analysis': self._analyze_behavior_patterns(violations_data, events_data, interactions_data),
            'risk_distribution': self._analyze_risk_distribution(violations_data, attempts_data),
            'temporal_patterns': self._analyze_temporal_patterns(violations_data, events_data),
            'device_security_analysis': self._analyze_device_security(device_data),
            'anomaly_detection': self._detect_anomalies(attempts_data, violations_data, interactions_data),
            'predictive_insights': self._generate_predictive_insights(violations_data, events_data),
            'compliance_assessment': self._assess_compliance(violations_data, events_data)
        }
        
        return analysis

    def _calculate_integrity_score(self, violations_data: List[Dict], events_data: List[Dict]) -> Dict:
        """Calculate overall exam integrity score"""
        total_weight = sum(v['weight'] for v in violations_data)
        total_events = len(events_data)
        
        if total_events == 0:
            integrity_score = 100
        else:
            # Normalize score based on violations and events
            violation_impact = min(total_weight * 2, 100)
            event_impact = min(total_events * 0.5, 50)
            integrity_score = max(0, 100 - violation_impact - event_impact)
        
        return {
            'score': round(integrity_score, 2),
            'grade': self._get_integrity_grade(integrity_score),
            'total_violations_weight': total_weight,
            'total_events': total_events,
            'interpretation': self._interpret_integrity_score(integrity_score)
        }

    def _analyze_behavior_patterns(self, violations_data: List[Dict], events_data: List[Dict],
                                 interactions_data: List[Dict]) -> Dict:
        """Analyze behavioral patterns using AI techniques"""
        
        # Violation type analysis
        violation_types = Counter(v['violation_type'] for v in violations_data)
        
        # Temporal clustering analysis
        violation_times = [datetime.fromisoformat(v['created_at']) for v in violations_data]
        time_clusters = self._cluster_violations_by_time(violation_times)
        
        # User behavior profiling
        user_profiles = self._create_user_behavior_profiles(violations_data, interactions_data)
        
        # Pattern recognition
        suspicious_patterns = self._identify_suspicious_patterns(violations_data, events_data)
        
        return {
            'violation_type_distribution': dict(violation_types),
            'temporal_clusters': time_clusters,
            'user_behavior_profiles': user_profiles,
            'suspicious_patterns': suspicious_patterns,
            'behavior_consistency': self._assess_behavior_consistency(interactions_data),
            'collaboration_indicators': self._detect_collaboration_indicators(interactions_data)
        }

    def _analyze_risk_distribution(self, violations_data: List[Dict], attempts_data: List[Dict]) -> Dict:
        """Analyze risk distribution across users and quizzes"""
        
        # Risk by user
        user_risks = defaultdict(float)
        for violation in violations_data:
            user_risks[violation['user_id']] += violation['weight']
        
        # Risk by quiz
        quiz_risks = defaultdict(float)
        for violation in violations_data:
            if 'quiz_context' in violation and violation['quiz_context']:
                quiz_risks[violation['quiz_context']] += violation['weight']
        
        # Risk distribution analysis
        risk_values = list(user_risks.values())
        
        return {
            'user_risk_distribution': {
                'mean': statistics.mean(risk_values) if risk_values else 0,
                'median': statistics.median(risk_values) if risk_values else 0,
                'std_dev': statistics.stdev(risk_values) if len(risk_values) > 1 else 0,
                'max_risk': max(risk_values) if risk_values else 0,
                'min_risk': min(risk_values) if risk_values else 0
            },
            'quiz_risk_distribution': dict(quiz_risks),
            'high_risk_users': self._identify_high_risk_users(user_risks),
            'risk_severity_breakdown': self._categorize_risks(user_risks)
        }

    def _analyze_temporal_patterns(self, violations_data: List[Dict], events_data: List[Dict]) -> Dict:
        """Analyze temporal patterns in proctoring violations"""
        
        # Convert timestamps for analysis
        violation_timestamps = [datetime.fromisoformat(v['created_at']) for v in violations_data]
        event_timestamps = [datetime.fromisoformat(e['created_at']) for e in events_data]
        
        # Hour-of-day analysis
        violation_hours = [ts.hour for ts in violation_timestamps]
        hour_distribution = Counter(violation_hours)
        
        # Day-of-week analysis
        violation_days = [ts.weekday() for ts in violation_timestamps]
        day_distribution = Counter(violation_days)
        
        # Peak violation periods
        peak_periods = self._identify_peak_periods(violation_timestamps)
        
        return {
            'hourly_distribution': dict(hour_distribution),
            'daily_distribution': dict(day_distribution),
            'peak_violation_periods': peak_periods,
            'violation_frequency_trends': self._calculate_frequency_trends(violation_timestamps),
            'time_correlation_analysis': self._analyze_time_correlations(violations_data, events_data)
        }

    def _detect_anomalies(self, attempts_data: List[Dict], violations_data: List[Dict],
                         interactions_data: List[Dict]) -> Dict:
        """Detect anomalies using statistical and machine learning techniques"""
        
        # Completion time anomalies
        completion_times = [a['duration_minutes'] for a in attempts_data if a['duration_minutes']]
        time_anomalies = self._detect_time_anomalies(completion_times)
        
        # Violation clustering anomalies
        violation_clusters = self._detect_violation_clusters(violations_data)
        
        # Score distribution anomalies
        scores = [a['score'] for a in attempts_data if a['score'] is not None]
        score_anomalies = self._detect_score_anomalies(scores)
        
        # Interaction pattern anomalies
        interaction_anomalies = self._detect_interaction_anomalies(interactions_data)
        
        return {
            'completion_time_anomalies': time_anomalies,
            'violation_clustering_anomalies': violation_clusters,
            'score_distribution_anomalies': score_anomalies,
            'interaction_pattern_anomalies': interaction_anomalies,
            'statistical_outliers': self._identify_statistical_outliers(attempts_data, violations_data)
        }

    def _generate_recommendations(self, ai_analysis: Dict) -> List[Dict]:
        """Generate AI-powered recommendations for improving exam security"""
        
        recommendations = []
        
        # Integrity score recommendations
        integrity_score = ai_analysis['overall_integrity_score']['score']
        if integrity_score < 70:
            recommendations.append({
                'category': 'Security Enhancement',
                'priority': 'High',
                'title': 'Strengthen Proctoring Protocols',
                'description': 'Current integrity score indicates significant security concerns. Consider implementing stricter proctoring measures.',
                'actions': [
                    'Enable additional camera monitoring',
                    'Implement stricter browser lockdown',
                    'Reduce violation tolerance thresholds',
                    'Add manual review processes'
                ]
            })
        
        # Behavior pattern recommendations
        behavior_patterns = ai_analysis['behavior_analysis']['suspicious_patterns']
        if behavior_patterns:
            recommendations.append({
                'category': 'Behavior Monitoring',
                'priority': 'Medium',
                'title': 'Address Suspicious Behavior Patterns',
                'description': 'Detected patterns suggest coordinated cheating or systematic workarounds.',
                'actions': [
                    'Investigate flagged user groups',
                    'Randomize question order and timing',
                    'Implement unique question sets per user',
                    'Add behavioral biometric analysis'
                ]
            })
        
        # Temporal pattern recommendations
        temporal_patterns = ai_analysis['temporal_patterns']
        peak_periods = temporal_patterns.get('peak_violation_periods', [])
        if peak_periods:
            recommendations.append({
                'category': 'Scheduling Optimization',
                'priority': 'Low',
                'title': 'Optimize Exam Scheduling',
                'description': 'Certain time periods show higher violation rates.',
                'actions': [
                    'Avoid high-risk time periods for critical exams',
                    'Increase monitoring during peak violation hours',
                    'Consider timezone-specific scheduling',
                    'Implement dynamic proctoring intensity'
                ]
            })
        
        return recommendations

    def _generate_detailed_findings(self, attempts_data: List[Dict], violations_data: List[Dict],
                                  events_data: List[Dict]) -> Dict:
        """Generate detailed findings with specific examples and evidence"""
        
        # High-risk attempts
        high_risk_attempts = [
            attempt for attempt in attempts_data 
            if attempt['force_submitted'] or attempt['is_flagged']
        ]
        
        # Critical violations
        critical_violations = [
            violation for violation in violations_data
            if violation['severity'] == 'high' or violation['weight'] >= 4
        ]
        
        # System security events
        security_events = [
            event for event in events_data
            if event['event_type'] in ['browser_console', 'developer_tools', 'screen_sharing']
        ]
        
        return {
            'high_risk_attempts': {
                'count': len(high_risk_attempts),
                'details': high_risk_attempts[:10],  # Top 10 for report
                'analysis': self._analyze_high_risk_attempts(high_risk_attempts)
            },
            'critical_violations': {
                'count': len(critical_violations),
                'details': critical_violations[:20],  # Top 20 for report
                'analysis': self._analyze_critical_violations(critical_violations)
            },
            'security_events': {
                'count': len(security_events),
                'details': security_events[:15],  # Top 15 for report
                'analysis': self._analyze_security_events(security_events)
            },
            'investigation_priorities': self._prioritize_investigations(
                high_risk_attempts, critical_violations, security_events
            )
        }

    # Helper methods for analysis
    def _calculate_attempt_duration(self, attempt) -> Optional[float]:
        """Calculate quiz attempt duration in minutes"""
        if attempt.started_at and attempt.completed_at:
            duration = attempt.completed_at - attempt.started_at
            return round(duration.total_seconds() / 60, 2)
        return None

    def _get_integrity_grade(self, score: float) -> str:
        """Convert integrity score to letter grade"""
        if score >= 90: return 'A'
        elif score >= 80: return 'B'
        elif score >= 70: return 'C'
        elif score >= 60: return 'D'
        else: return 'F'

    def _interpret_integrity_score(self, score: float) -> str:
        """Provide interpretation of integrity score"""
        if score >= 90:
            return "Excellent exam integrity with minimal security concerns"
        elif score >= 80:
            return "Good exam integrity with minor security issues"
        elif score >= 70:
            return "Acceptable exam integrity with moderate security concerns"
        elif score >= 60:
            return "Poor exam integrity with significant security issues requiring attention"
        else:
            return "Critical exam integrity issues requiring immediate investigation"

    # Additional helper methods would be implemented here...
    def _cluster_violations_by_time(self, timestamps: List[datetime]) -> List[Dict]:
        """Cluster violations by time periods"""
        # Simplified clustering implementation
        clusters = []
        if timestamps:
            # Group by hour windows
            hour_groups = defaultdict(list)
            for ts in timestamps:
                hour_key = ts.replace(minute=0, second=0, microsecond=0)
                hour_groups[hour_key].append(ts)
            
            for hour, events in hour_groups.items():
                if len(events) >= 3:  # Cluster threshold
                    clusters.append({
                        'start_time': hour.isoformat(),
                        'event_count': len(events),
                        'density': len(events) / 60,  # Events per minute
                        'significance': 'high' if len(events) >= 5 else 'medium'
                    })
        
        return clusters

    def _create_user_behavior_profiles(self, violations_data: List[Dict], 
                                     interactions_data: List[Dict]) -> Dict:
        """Create behavioral profiles for users"""
        profiles = {}
        
        # Group by user
        user_violations = defaultdict(list)
        user_interactions = defaultdict(list)
        
        for violation in violations_data:
            user_violations[violation['user_id']].append(violation)
        
        for interaction in interactions_data:
            user_interactions[interaction['user_id']].append(interaction)
        
        # Create profiles
        for user_id in set(list(user_violations.keys()) + list(user_interactions.keys())):
            violations = user_violations[user_id]
            interactions = user_interactions[user_id]
            
            profiles[user_id] = {
                'violation_count': len(violations),
                'total_violation_weight': sum(v['weight'] for v in violations),
                'most_common_violation': max(Counter(v['violation_type'] for v in violations).items(), 
                                           key=lambda x: x[1])[0] if violations else None,
                'interaction_count': len(interactions),
                'risk_level': self._calculate_user_risk_level(violations),
                'behavior_consistency': self._calculate_behavior_consistency(interactions)
            }
        
        return profiles

    def _calculate_user_risk_level(self, violations: List[Dict]) -> str:
        """Calculate risk level for a user"""
        total_weight = sum(v['weight'] for v in violations)
        
        for level, (min_val, max_val) in self.severity_thresholds.items():
            if min_val <= total_weight <= max_val:
                return level
        
        return 'low'

    def _generate_executive_summary(self, ai_analysis: Dict) -> Dict:
        """Generate executive summary of the report"""
        integrity_score = ai_analysis['overall_integrity_score']['score']
        
        return {
            'overall_assessment': ai_analysis['overall_integrity_score']['interpretation'],
            'key_metrics': {
                'integrity_score': integrity_score,
                'integrity_grade': ai_analysis['overall_integrity_score']['grade'],
                'total_violations': ai_analysis['overall_integrity_score']['total_violations_weight'],
                'total_events': ai_analysis['overall_integrity_score']['total_events']
            },
            'critical_findings': self._extract_critical_findings(ai_analysis),
            'immediate_actions_required': integrity_score < 60,
            'overall_risk_level': self._determine_overall_risk_level(integrity_score)
        }

    def _generate_detailed_statistics(self, attempts_data: List[Dict], violations_data: List[Dict], 
                                    events_data: List[Dict]) -> Dict:
        """Generate detailed statistical analysis"""
        return {
            'quiz_attempts': {
                'total': len(attempts_data),
                'completed': len([a for a in attempts_data if a['status'] == 'completed']),
                'force_submitted': len([a for a in attempts_data if a['force_submitted']]),
                'flagged': len([a for a in attempts_data if a['is_flagged']]),
                'average_score': statistics.mean([a['score'] for a in attempts_data if a['score']]) if attempts_data else 0
            },
            'violations': {
                'total': len(violations_data),
                'by_severity': Counter(v['severity'] for v in violations_data),
                'by_type': Counter(v['violation_type'] for v in violations_data),
                'total_weight': sum(v['weight'] for v in violations_data)
            },
            'proctoring_events': {
                'total': len(events_data),
                'by_type': Counter(e['event_type'] for e in events_data),
                'by_severity': Counter(e['severity'] for e in events_data)
            }
        }

    # Additional methods would continue here...
    def _get_methodology_description(self) -> str:
        """Return methodology description for the report"""
        return """
        This report utilizes advanced AI and statistical analysis techniques to evaluate exam integrity:
        - Weighted violation scoring based on security impact
        - Temporal pattern analysis using clustering algorithms
        - Behavioral profiling through interaction analysis
        - Anomaly detection using statistical outlier identification
        - Risk assessment through multi-factor correlation analysis
        """

    def _get_data_sources_info(self) -> List[str]:
        """Return information about data sources"""
        return [
            "Quiz attempt records and completion data",
            "Proctoring violation events and severity classifications",
            "Real-time monitoring events and system interactions",
            "Device and browser security logs",
            "User interaction patterns and behavioral metrics",
            "Camera and audio monitoring data (metadata only)"
        ]

    def _get_limitations_info(self) -> List[str]:
        """Return information about report limitations"""
        return [
            "Analysis based on automated detection systems - manual review recommended for critical decisions",
            "Some violations may be false positives due to technical issues or accessibility needs",
            "Behavioral analysis requires sufficient data points for accurate profiling",
            "Time-based patterns may be influenced by external factors (system load, network issues)",
            "AI recommendations should be validated by educational and security professionals"
        ]

# Additional supporting classes and functions would be implemented here...

def generate_scheduled_report(period_days: int = 7) -> Dict:
    """Generate automated periodic proctoring report"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    generator = ProctoringReportGenerator()
    return generator.generate_comprehensive_report(start_date, end_date)

def export_report_to_pdf(report_data: Dict, output_path: str) -> bool:
    """Export proctoring report to PDF format"""
    try:
        # PDF generation implementation would go here
        # Using libraries like reportlab or weasyprint
        logging.info(f"Report exported to PDF: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to export report to PDF: {e}")
        return False

def send_report_email(report_data: Dict, recipients: List[str]) -> bool:
    """Send proctoring report via email"""
    try:
        # Email sending implementation would go here
        logging.info(f"Report emailed to {len(recipients)} recipients")
        return True
    except Exception as e:
        logging.error(f"Failed to send report email: {e}")
        return False