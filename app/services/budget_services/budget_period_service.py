from datetime import date, timedelta

def get_current_period(budget):
    today = date.today()
    
    if budget['start_date'] and today < budget['start_date']:
        return None
    
    if budget['period_type'] == 'custom':
        if budget['end_date'] and today > budget['end_date']:
            return None
        return budget['start_date'], budget['end_date']
    
    if budget['period_type'] == 'monthly':
        start = date(today.year, today.month, 1)
        
        if today.month == 12:
            end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)
            
        return start, end
    
    if budget['period_type'] == 'weekly':
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        
        return start, end
    
    return None