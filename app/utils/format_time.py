def format_reset_time(seconds: int) -> str:
    """Convert seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return f"{minutes} minute{'s' if minutes > 1 else ''} and {remaining_seconds} second{'s' if remaining_seconds > 1 else ''}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours > 1 else ''} and {minutes} minute{'s' if minutes > 1 else ''}"