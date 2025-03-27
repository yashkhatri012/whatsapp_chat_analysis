import re
import pandas as pd

def preprocess(data):
    # Print a sample of the input data for debugging
    print("Sample of input data:")
    print(data[:200] if len(data) > 200 else data)
    
    # More robust patterns for different WhatsApp chat formats
    # 12-hour format with am/pm
    pattern_12h = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s([ap]m)\s-\s(.+)'
    
    # 24-hour format
    pattern_24h = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s(.+)'
    
    # Try with 12-hour format first
    matches_12h = list(re.finditer(pattern_12h, data))
    
    if matches_12h:
        print(f"Found {len(matches_12h)} messages using 12-hour format")
        time_format = '12h'
        matches = matches_12h
    else:
        # Try with 24-hour format
        matches_24h = list(re.finditer(pattern_24h, data))
        print(f"Found {len(matches_24h)} messages using 24-hour format")
        time_format = '24h'
        matches = matches_24h
    
    # Extract data into lists
    dates = []
    users = []
    messages = []
    
    for match in matches:
        if time_format == '12h':
            # Extract components for 12-hour format
            date = match.group(1)
            time = match.group(2)
            am_pm = match.group(3)
            content = match.group(4)
            
            # Combine date and time
            date_str = f"{date}, {time} {am_pm}"
        else:
            # Extract components for 24-hour format
            date = match.group(1)
            time = match.group(2)
            content = match.group(3)
            
            # Combine date and time
            date_str = f"{date}, {time}"
        
        # Split user and message
        user_message_split = content.split(':', 1)
        if len(user_message_split) > 1:
            user = user_message_split[0].strip()
            message = user_message_split[1].strip()
        else:
            # System message without user
            user = 'group_notification'
            message = content.strip()
        
        dates.append(date_str)
        users.append(user)
        messages.append(message)
    
    # Print the number of matches found
    print(f"Extracted {len(dates)} messages using {time_format} format")
    
    # Handle empty results
    if not dates:
        print("No messages could be extracted from the input data")
        # Create an empty DataFrame with all required columns
        return pd.DataFrame(columns=['date', 'user', 'message', 'year', 'month_num', 'month', 
                                    'day', 'hour', 'minute', 'only_date', 'day_name', 'period'])
    
    # Create DataFrame
    df = pd.DataFrame({
        'user': users,
        'message': messages,
        'message_date': dates  # Temporary column for date parsing
    })
    
    # Convert date strings to datetime based on detected format
    try:
        if time_format == '12h':
            # Try different 12-hour formats (2-digit or 4-digit year)
            try:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %I:%M %p')
            except ValueError:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %I:%M %p')
        else:
            # Try different 24-hour formats (2-digit or 4-digit year)
            try:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %H:%M')
            except ValueError:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %H:%M')
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        print("Trying with dayfirst=True...")
        # Fallback to letting pandas infer the format with dayfirst=True
        df['date'] = pd.to_datetime(df['message_date'], dayfirst=True)
    
    # Drop the temporary message_date column
    df.drop('message_date', axis=1, inplace=True)
    
    # Extract datetime components
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute
    
    # Create period column
    period = []
    for hour in df[['day_name', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))
    
    df['period'] = period
    
    return df