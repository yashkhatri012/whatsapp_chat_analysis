import re
import pandas as pd
from datetime import datetime
import re
import pandas as pd

def preprocess(data):
    # Print a sample of the input data for debugging
    print("Sample of input data:")
    print(data[:200] if len(data) > 200 else data)
    
    # Universal regex pattern to capture a wide range of WhatsApp chat formats.
    pattern = re.compile(r"""
        ^                   # Start of the line
        \[?                 # Optional opening bracket
        (\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})  # Date (formats like 16/08/24 or 16-08-2024)
        ,?\s+              # Optional comma then whitespace
        (\d{1,2}:\d{2}(?::\d{2})?)  # Time (hh:mm with optional :ss)
        \s*                # Optional whitespace
        ([AaPp][Mm])?      # Optional AM/PM marker (in any case)
        \]?                # Optional closing bracket
        \s*[-:]\s*         # A separator that can be a hyphen or colon, with optional spaces
        (.*?)              # Non-greedy capture for user name
        \s*:\s*            # Colon separator with optional spaces
        (.+)$              # Capture the rest as the message text (up to end of line)
    """, re.VERBOSE | re.MULTILINE)

    # Find all messages using the universal pattern.
    matches = list(pattern.finditer(data))
    print(f"Found {len(matches)} messages using the universal pattern")

    # Extract data into lists
    dates = []
    users = []
    messages = []

    for match in matches:
        # Extract captured groups.
        date_part = match.group(1)      # e.g., "16/08/24"
        time_part = match.group(2)      # e.g., "8:26" or "8:26:12"
        am_pm = match.group(3)          # e.g., "AM" or None
        user = match.group(4).strip()   # Username
        message = match.group(5).strip()# Message content

        # Ensure the time string always includes seconds.
        if time_part.count(":") == 1:
            time_part = time_part + ":00"

        # Reconstruct the full date string based on presence of AM/PM.
        if am_pm:
            date_str = f"{date_part}, {time_part} {am_pm}"
        else:
            date_str = f"{date_part}, {time_part}"
        
        # Normalize media messages
        if '<Media omitted>' in message or 'Media omitted' in message:
            message = '<Media omitted>'
        
        dates.append(date_str)
        users.append(user)
        messages.append(message)

    print(f"Extracted {len(dates)} messages from the input data")

    # Handle empty results: return an empty DataFrame if nothing was extracted.
    if not dates:
        print("No messages could be extracted from the input data")
        return pd.DataFrame(columns=['date', 'user', 'message', 'year', 'month_num',
                                     'month', 'day', 'hour', 'minute', 'only_date',
                                     'day_name', 'period'])

    # Create a temporary DataFrame.
    df = pd.DataFrame({
        'user': users,
        'message': messages,
        'message_date': dates  # Temporary column for date parsing.
    })

    # Convert date strings to datetime objects.
    try:
        # Determine if any message has an AM/PM marker.
        if any(('AM' in d or 'PM' in d or 'am' in d or 'pm' in d) for d in df['message_date']):
            try:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %I:%M:%S %p')
            except ValueError:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %I:%M:%S %p')
        else:
            try:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %H:%M:%S')
            except ValueError:
                df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %H:%M:%S')
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        print("Trying with dayfirst=True...")
        df['date'] = pd.to_datetime(df['message_date'], dayfirst=True)
    
    # Drop the temporary 'message_date' column.
    df.drop('message_date', axis=1, inplace=True)

    # Extract additional datetime components.
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # Create a 'period' column for hourly intervals.
    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(f"{hour}-00")
        elif hour == 0:
            period.append("00-1")
        else:
            period.append(f"{hour}-{hour+1}")
    df['period'] = period

    return df