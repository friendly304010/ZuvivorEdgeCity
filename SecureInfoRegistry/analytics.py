from models import Report
from utils import decrypt_data
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta

def get_report_trends():
    reports = Report.query.all()
    
    # Initialize analytics data structures
    perpetrator_frequency = Counter()
    time_distribution = defaultdict(int)
    overlap_distribution = defaultdict(int)
    location_patterns = Counter()
    
    # Process each report
    for report in reports:
        try:
            # Analyze perpetrator frequency
            perpetrator_frequency[report.perpetrator_name] += 1
            
            # Analyze time patterns (by hour)
            hour = report.created_at.hour
            time_distribution[hour] += 1
            
            # Analyze overlap patterns
            overlap_distribution[report.overlap_count] += 1
            
            # Analyze location patterns from encrypted data
            decrypted_data = json.loads(decrypt_data(report.encrypted_data))
            if 'location' in decrypted_data:
                location_patterns[decrypted_data['location']] += 1
                
        except Exception as e:
            print(f"Error processing report {report.id}: {str(e)}")
    
    # Prepare analysis results
    analysis = {
        'total_reports': len(reports),
        'unique_perpetrators': len(perpetrator_frequency),
        'repeat_offenders': {name: count for name, count in perpetrator_frequency.items() if count > 1},
        'hourly_distribution': dict(time_distribution),
        'overlap_statistics': dict(overlap_distribution),
        'location_hotspots': dict(location_patterns),
        'recent_trend': _calculate_recent_trend()
    }
    
    return analysis

def _calculate_recent_trend():
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Get reports from last week
    recent_reports = Report.query.filter(Report.created_at >= week_ago).all()
    
    # Group by day
    daily_counts = defaultdict(int)
    for report in recent_reports:
        day = report.created_at.date()
        daily_counts[day] += 1
    
    # Calculate trend
    trend_data = []
    for i in range(7):
        day = (now - timedelta(days=i)).date()
        trend_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': daily_counts[day]
        })
    
    return trend_data
