#!/usr/bin/env python3
"""Fetch FIFA World Cup 2026 standings from api.football-data.org → data.json"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

API_KEY = os.environ.get('FOOTBALL_API_KEY', '')
BASE_URL = 'https://api.football-data.org/v4'
COMPETITION = 'WC'

# API English name → (Chinese name, flag emoji, note)
TEAM_MAP = {
    'Mexico':                           ('墨西哥',       '🇲🇽', '主辦國'),
    'South Korea':                      ('南韓',         '🇰🇷', ''),
    'Korea Republic':                   ('南韓',         '🇰🇷', ''),
    'Czechia':                          ('捷克',         '🇨🇿', ''),
    'Czech Republic':                   ('捷克',         '🇨🇿', ''),
    'South Africa':                     ('南非',         '🇿🇦', ''),
    'Switzerland':                      ('瑞士',         '🇨🇭', ''),
    'Canada':                           ('加拿大',       '🇨🇦', '主辦國'),
    'Bosnia and Herzegovina':           ('波黑',         '🇧🇦', ''),
    'Bosnia & Herzegovina':             ('波黑',         '🇧🇦', ''),
    'Qatar':                            ('卡達',         '🇶🇦', ''),
    'Brazil':                           ('巴西',         '🇧🇷', ''),
    'Morocco':                          ('摩洛哥',       '🇲🇦', ''),
    'Scotland':                         ('蘇格蘭',       '🏴󠁧󠁢󠁳󠁣󠁴󠁿', ''),
    'Haiti':                            ('海地',         '🇭🇹', ''),
    'United States':                    ('美國',         '🇺🇸', '主辦國'),
    'USA':                              ('美國',         '🇺🇸', '主辦國'),
    'Australia':                        ('澳洲',         '🇦🇺', ''),
    'Turkey':                           ('土耳其',       '🇹🇷', ''),
    'Türkiye':                          ('土耳其',       '🇹🇷', ''),
    'Paraguay':                         ('巴拉圭',       '🇵🇾', ''),
    'Germany':                          ('德國',         '🇩🇪', ''),
    "Côte d'Ivoire":                    ('象牙海岸',     '🇨🇮', ''),
    'Ivory Coast':                      ('象牙海岸',     '🇨🇮', ''),
    'Ecuador':                          ('厄瓜多',       '🇪🇨', ''),
    'Curaçao':                          ('庫拉索',       '🇨🇼', ''),
    'Curacao':                          ('庫拉索',       '🇨🇼', ''),
    'Sweden':                           ('瑞典',         '🇸🇪', ''),
    'Netherlands':                      ('荷蘭',         '🇳🇱', ''),
    'Japan':                            ('日本',         '🇯🇵', ''),
    'Tunisia':                          ('突尼西亞',     '🇹🇳', ''),
    'Belgium':                          ('比利時',       '🇧🇪', ''),
    'Egypt':                            ('埃及',         '🇪🇬', ''),
    'Iran':                             ('伊朗',         '🇮🇷', ''),
    'New Zealand':                      ('紐西蘭',       '🇳🇿', ''),
    'Spain':                            ('西班牙',       '🇪🇸', ''),
    'Cape Verde':                       ('維德角',       '🇨🇻', ''),
    'Cabo Verde':                       ('維德角',       '🇨🇻', ''),
    'Saudi Arabia':                     ('沙烏地阿拉伯', '🇸🇦', ''),
    'Uruguay':                          ('烏拉圭',       '🇺🇾', ''),
    'France':                           ('法國',         '🇫🇷', ''),
    'Norway':                           ('挪威',         '🇳🇴', ''),
    'Senegal':                          ('塞內加爾',     '🇸🇳', ''),
    'Iraq':                             ('伊拉克',       '🇮🇶', ''),
    'Argentina':                        ('阿根廷',       '🇦🇷', '衛冕冠軍'),
    'Austria':                          ('奧地利',       '🇦🇹', ''),
    'Jordan':                           ('約旦',         '🇯🇴', ''),
    'Algeria':                          ('阿爾及利亞',   '🇩🇿', ''),
    'Portugal':                         ('葡萄牙',       '🇵🇹', ''),
    'Colombia':                         ('哥倫比亞',     '🇨🇴', ''),
    'DR Congo':                         ('DR剛果',       '🇨🇩', ''),
    'Congo DR':                         ('DR剛果',       '🇨🇩', ''),
    'Democratic Republic of Congo':     ('DR剛果',       '🇨🇩', ''),
    'Uzbekistan':                       ('烏茲別克',     '🇺🇿', ''),
    'England':                          ('英格蘭',       '🏴󠁧󠁢󠁥󠁮󠁧󠁿', ''),
    'Croatia':                          ('克羅埃西亞',   '🇭🇷', ''),
    'Ghana':                            ('加納',         '🇬🇭', ''),
    'Panama':                           ('巴拿馬',       '🇵🇦', ''),
}


def team_info(api_name):
    return TEAM_MAP.get(api_name, (api_name, '🏳️', ''))


def result_str(match):
    hs = match['score']['fullTime']['home']
    as_ = match['score']['fullTime']['away']
    if hs is None:
        return None
    home = team_info(match['homeTeam']['name'])[0]
    away = team_info(match['awayTeam']['name'])[0]
    return f'{home} {hs}–{as_} {away}'


def tie_note(teams):
    """Generate a plain-language tiebreak note when teams share points."""
    i = 0
    notes = []
    while i < len(teams):
        j = i + 1
        while j < len(teams) and teams[j]['pts'] == teams[i]['pts']:
            j += 1
        tied = teams[i:j]
        if len(tied) > 1:
            names = '、'.join(t['name'] for t in tied)
            gds = [t['gf'] - t['ga'] for t in tied]
            gfs = [t['gf'] for t in tied]
            if len(set(gds)) == 1 and len(set(gfs)) == 1:
                notes.append(f'⚠️ {names} 積分/淨球差/進球完全相同，依FIFA排名決定順序')
            elif len(set(gds)) == 1:
                notes.append(f'{names} 同積分同淨球差，依進球數分出名次')
            else:
                leader = max(tied, key=lambda t: t['gf'] - t['ga'])
                notes.append(f'{names} 同積分；{leader["name"]}淨球差較優暫居前')
        i = j
    return '；'.join(notes) if notes else None


def main():
    if not API_KEY:
        print('ERROR: FOOTBALL_API_KEY not set', file=sys.stderr)
        sys.exit(1)

    headers = {'X-Auth-Token': API_KEY}

    print('Fetching standings…')
    r = requests.get(f'{BASE_URL}/competitions/{COMPETITION}/standings',
                     headers=headers, timeout=30)
    r.raise_for_status()
    standings_data = r.json()

    print('Fetching matches…')
    r2 = requests.get(f'{BASE_URL}/competitions/{COMPETITION}/matches',
                      headers=headers, timeout=30)
    r2.raise_for_status()
    matches_data = r2.json()

    # Collect finished results per group
    group_results: dict[str, list[str]] = {}
    group_played: dict[str, int] = {}
    for m in matches_data.get('matches', []):
        if m.get('stage') != 'GROUP_STAGE':
            continue
        grp = m.get('group', '').replace('GROUP_', '')
        if not grp:
            continue
        if m['status'] in ('FINISHED', 'PAUSED'):
            rs = result_str(m)
            if rs:
                group_results.setdefault(grp, []).append(rs)
            group_played[grp] = group_played.get(grp, 0) + 1

    # Build groups list
    groups = []
    seen = set()
    for standing in standings_data.get('standings', []):
        if standing.get('type') != 'TOTAL':
            continue
        grp = standing.get('group', '').replace('GROUP_', '')
        if not grp or grp in seen:
            continue
        seen.add(grp)

        teams = []
        for row in standing.get('table', []):
            name, flag, note = team_info(row['team']['name'])
            teams.append({
                'name': name, 'flag': flag, 'note': note,
                'p': row['playedGames'],
                'w': row['won'], 'd': row['draw'], 'l': row['lost'],
                'gf': row['goalsFor'], 'ga': row['goalsAgainst'],
                'pts': row['points'],
            })

        groups.append({
            'id': grp,
            'played': group_played.get(grp, 0),
            'teams': teams,
            'results': group_results.get(grp, []),
            'tieNote': tie_note(teams),
        })

    groups.sort(key=lambda g: g['id'])

    total_played = sum(g['played'] for g in groups)
    if total_played <= 24:
        round_label = '第1輪'
    elif total_played <= 48:
        round_label = '第2輪'
    else:
        round_label = '第3輪'

    output = {
        'lastUpdated': datetime.now(timezone.utc).strftime('%Y/%m/%d %H:%M UTC'),
        'round': round_label,
        'groups': groups,
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'✓ data.json updated — {len(groups)} groups, {total_played} matches played')


if __name__ == '__main__':
    main()
