from datetime import datetime

def parse_timestamp(timestamp: str) -> datetime:
    """Parses a BitMEX timestamp into a datetime object"""
    return datetime(timestamp.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S.%f%z')
