#!/usr/bin/env python3
"""Compare de-identified GSC snapshots. Standard library only; no network calls."""
import argparse
import json
import math
from datetime import date
from pathlib import Path


def window_days(window):
    start, end = (date.fromisoformat(window[k]) for k in ('start', 'end'))
    if end < start:
        raise ValueError('Window end precedes start')
    return (end - start).days + 1


def validate_metrics(metrics):
    for key in ('clicks', 'impressions'):
        value = metrics[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f'{key} must be a nonnegative integer')
    if metrics['clicks'] > metrics['impressions']:
        raise ValueError('Clicks exceed impressions')
    position = metrics.get('average_position')
    if position is not None and (isinstance(position, bool) or not isinstance(position, (int, float)) or not math.isfinite(position) or position < 1):
        raise ValueError('Invalid average position')


def compare(data):
    before, after = data['before_window'], data['after_window']
    days = window_days(before)
    if days != window_days(after):
        raise ValueError('Equal complete-day windows are required')
    if before['end'] >= after['start']:
        raise ValueError('Comparison windows must be ordered and non-overlapping')
    if date.fromisoformat(data['complete_through']) < date.fromisoformat(after['end']):
        raise ValueError('The after window is not complete')
    if not data['cohorts']:
        raise ValueError('At least one cohort is required')
    result = {'days_per_window': days, 'interpretation': 'observational_not_causal', 'cohorts': {}}
    for name, cohort in data['cohorts'].items():
        a, b = cohort['before'], cohort['after']
        validate_metrics(a)
        validate_metrics(b)
        delta = {}
        for key in ('clicks', 'impressions'):
            delta[key + '_change'] = b[key] - a[key]
            delta[key + '_change_percent'] = round(100 * (b[key] - a[key]) / a[key], 2) if a[key] else None
        ctr_a = a['clicks'] / a['impressions'] * 100 if a['impressions'] else None
        ctr_b = b['clicks'] / b['impressions'] * 100 if b['impressions'] else None
        delta['ctr_before_percent'] = round(ctr_a, 3) if ctr_a is not None else None
        delta['ctr_after_percent'] = round(ctr_b, 3) if ctr_b is not None else None
        delta['ctr_change_percentage_points'] = round(ctr_b - ctr_a, 3) if ctr_a is not None and ctr_b is not None else None
        if a.get('average_position') is not None and b.get('average_position') is not None:
            delta['average_position_improvement'] = round(a['average_position'] - b['average_position'], 2)
        delta['caution'] = 'Changing query mix, crawl timing and small samples prevent causal attribution; lower impressions can coexist with a better average position.'
        result['cohorts'][name] = delta
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(compare(json.loads(args.snapshot.read_text())), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError) as error:
        parser.exit(2, f'Invalid snapshot: {error}\n')
