#!/usr/bin/env python3
"""
Generate a professional Crow's Foot ER diagram matching the reference image.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle
import numpy as np

# Canvas setup
fig = plt.figure(figsize=(16, 26), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1600)
ax.set_ylim(2600, 0)  # Top-down coordinates (0 at top, 2600 at bottom)
ax.axis('off')

# Color palettes matching reference
THEMES = {
    'TEAMS': {
        'border': '#AA55AA',
        'header_bg': '#F6E6F6',
        'row_bg': '#FAF2FA',
        'text': '#551A55',
        'grid': '#D4A8D4'
    },
    'PLAYERS': {
        'border': '#17B8B8',
        'header_bg': '#E6F8F8',
        'row_bg': '#F2FCFC',
        'text': '#0C5E5E',
        'grid': '#9CE0E0'
    },
    'MATCHES': {
        'border': '#E67E22',
        'header_bg': '#FDF0E4',
        'row_bg': '#FEF7F0',
        'text': '#7E3F0A',
        'grid': '#F3C599'
    },
    'USERS': {
        'border': '#2ECC71',
        'header_bg': '#EAF9F0',
        'row_bg': '#F4FCF7',
        'text': '#196F3D',
        'grid': '#A3E4B8'
    },
    'PLAYER_MATCH_STATS': {
        'border': '#17B8B8',
        'header_bg': '#E6F8F8',
        'row_bg': '#F2FCFC',
        'text': '#0C5E5E',
        'grid': '#9CE0E0'
    },
    'USER_TEAMS': {
        'border': '#8E44AD',
        'header_bg': '#F4ECF7',
        'row_bg': '#FAF6FC',
        'text': '#4A235A',
        'grid': '#CBB1DE'
    },
    'CONTESTS': {
        'border': '#F1C40F',
        'header_bg': '#FEF9E7',
        'row_bg': '#FFFDF4',
        'text': '#7D6608',
        'grid': '#F8E285'
    },
    'USER_TEAM_PLAYERS': {
        'border': '#E74C3C',
        'header_bg': '#FDEDEC',
        'row_bg': '#FEF5F5',
        'text': '#78281F',
        'grid': '#F4A49C'
    },
    'CONTEST_ENTRIES': {
        'border': '#4A90E2',
        'header_bg': '#EEF4FC',
        'row_bg': '#F6F9FD',
        'text': '#1C4A7E',
        'grid': '#ADCBEF'
    },
    'WALLET_TRANSACTIONS': {
        'border': '#7BB33B',
        'header_bg': '#F2F8EC',
        'row_bg': '#F8FCF5',
        'text': '#365314',
        'grid': '#C0DE9E'
    },
}

TABLES = {
    'TEAMS': {
        'x': 660, 'y': 60, 'w': 280,
        'cols': [
            ('int', 'team_id', 'PK'),
            ('varchar', 'team_name', ''),
            ('varchar', 'short_name', ''),
            ('varchar', 'team_type', '')
        ]
    },
    'PLAYERS': {
        'x': 200, 'y': 380, 'w': 290,
        'cols': [
            ('int', 'player_id', 'PK'),
            ('varchar', 'full_name', ''),
            ('int', 'team_id', 'FK'),
            ('varchar', 'role', ''),
            ('numeric', 'credits', ''),
            ('boolean', 'is_active', '')
        ]
    },
    'MATCHES': {
        'x': 620, 'y': 360, 'w': 340,
        'cols': [
            ('int', 'match_id', 'PK'),
            ('varchar', 'tournament', ''),
            ('int', 'home_team_id', 'FK'),
            ('int', 'away_team_id', 'FK'),
            ('varchar', 'venue', ''),
            ('timestamptz', 'starts_at', ''),
            ('varchar', 'status', '')
        ]
    },
    'USERS': {
        'x': 1090, 'y': 360, 'w': 330,
        'cols': [
            ('int', 'user_id', 'PK'),
            ('varchar', 'username', 'UK'),
            ('varchar', 'phone', 'UK'),
            ('varchar', 'email', 'UK'),
            ('char', 'state_code', ''),
            ('varchar', 'kyc_status', ''),
            ('timestamptz', 'created_at', '')
        ]
    },
    'PLAYER_MATCH_STATS': {
        'x': 140, 'y': 860, 'w': 340,
        'cols': [
            ('int', 'match_id', 'PK,FK'),
            ('int', 'player_id', 'PK,FK'),
            ('int', 'runs', ''),
            ('int', 'balls_faced', ''),
            ('int', 'fours', ''),
            ('int', 'sixes', ''),
            ('int', 'wickets', ''),
            ('int', 'catches', ''),
            ('numeric', 'fantasy_points', '')
        ]
    },
    'USER_TEAMS': {
        'x': 600, 'y': 880, 'w': 350,
        'cols': [
            ('int', 'user_team_id', 'PK'),
            ('int', 'user_id', 'FK'),
            ('int', 'match_id', 'FK'),
            ('varchar', 'team_label', ''),
            ('int', 'captain_id', 'FK'),
            ('int', 'vice_captain_id', 'FK'),
            ('numeric', 'total_points', ''),
            ('timestamptz', 'created_at', '')
        ]
    },
    'CONTESTS': {
        'x': 1050, 'y': 860, 'w': 330,
        'cols': [
            ('int', 'contest_id', 'PK'),
            ('int', 'match_id', 'FK'),
            ('varchar', 'contest_name', ''),
            ('varchar', 'contest_type', ''),
            ('numeric', 'entry_fee', ''),
            ('int', 'total_spots', ''),
            ('numeric', 'prize_pool', ''),
            ('boolean', 'is_guaranteed', ''),
            ('varchar', 'invite_code', 'UK')
        ]
    },
    'USER_TEAM_PLAYERS': {
        'x': 130, 'y': 1500, 'w': 280,
        'cols': [
            ('int', 'user_team_id', 'PK,FK'),
            ('int', 'player_id', 'PK,FK')
        ]
    },
    'CONTEST_ENTRIES': {
        'x': 750, 'y': 1500, 'w': 330,
        'cols': [
            ('int', 'entry_id', 'PK'),
            ('int', 'contest_id', 'FK'),
            ('int', 'user_team_id', 'FK'),
            ('timestamptz', 'joined_at', ''),
            ('int', 'final_rank', ''),
            ('numeric', 'winnings', '')
        ]
    },
    'WALLET_TRANSACTIONS': {
        'x': 900, 'y': 1950, 'w': 380,
        'cols': [
            ('int', 'txn_id', 'PK'),
            ('int', 'user_id', 'FK'),
            ('varchar', 'txn_type', ''),
            ('numeric', 'amount', ''),
            ('int', 'reference_entry_id', 'FK'),
            ('varchar', 'status', ''),
            ('timestamptz', 'created_at', '')
        ]
    }
}

ROW_H = 34
HDR_H = 40
COL1_W_RATIO = 0.26
COL3_W_RATIO = 0.18

def draw_table(name):
    t = TABLES[name]
    thm = THEMES[name]
    x, y, w = t['x'], t['y'], t['w']
    cols = t['cols']
    num_rows = len(cols)
    total_h = HDR_H + num_rows * ROW_H
    
    col1_w = int(w * COL1_W_RATIO)
    col3_w = int(w * COL3_W_RATIO)
    col2_w = w - col1_w - col3_w
    
    # Outer box background
    ax.add_patch(Rectangle((x, y), w, total_h, facecolor=thm['row_bg'], edgecolor=thm['border'], lw=2, zorder=2))
    
    # Header box
    ax.add_patch(Rectangle((x, y), w, HDR_H, facecolor=thm['header_bg'], edgecolor=thm['border'], lw=1.5, zorder=3))
    ax.text(x + w / 2, y + HDR_H / 2 + 1, name, ha='center', va='center', fontsize=11, fontweight='bold', color=thm['text'], zorder=4)
    
    # Column grid lines
    # Vertical line 1
    ax.plot([x + col1_w, x + col1_w], [y + HDR_H, y + total_h], color=thm['grid'], lw=1.2, zorder=3)
    # Vertical line 2
    ax.plot([x + col1_w + col2_w, x + col1_w + col2_w], [y + HDR_H, y + total_h], color=thm['grid'], lw=1.2, zorder=3)
    
    # Rows
    for i, (dtype, cname, key) in enumerate(cols):
        ry = y + HDR_H + i * ROW_H
        # Horizontal separator
        ax.plot([x, x + w], [ry, ry], color=thm['grid'], lw=1.2, zorder=3)
        
        # Col 1: data type
        ax.text(x + 12, ry + ROW_H / 2, dtype, ha='left', va='center', fontsize=9.5, color='#444444', fontfamily='sans-serif', zorder=4)
        # Col 2: column name
        ax.text(x + col1_w + 12, ry + ROW_H / 2, cname, ha='left', va='center', fontsize=10, fontweight='bold' if key else 'normal', color='#222222', fontfamily='sans-serif', zorder=4)
        # Col 3: key
        kcolor = '#B03A2E' if 'PK' in key else ('#2874A6' if 'FK' in key else ('#7D6608' if 'UK' in key else '#666666'))
        ax.text(x + w - 12, ry + ROW_H / 2, key, ha='right', va='center', fontsize=9, fontweight='bold', color=kcolor, fontfamily='sans-serif', zorder=4)
        
    t['h'] = total_h
    t['b'] = y + total_h

# Draw all tables
for name in TABLES:
    draw_table(name)

# ── CROW'S FOOT NOTATION DRAWING FUNCTIONS ──

LINE_COLOR = '#2B2B2B'
LINE_WIDTH = 1.4

def draw_crows_foot(x, y, direction='top', size=11):
    """
    Draws a crow's foot symbol (circle + 3 spreading prongs) at (x, y).
    direction: which side of the table border this sits on ('top', 'bottom', 'left', 'right')
    """
    # Circle radius
    r = 4.0
    prong_len = size
    prong_spread = size * 0.75
    
    if direction == 'top':
        # Prongs connect to y (table top), spreading out
        # Circle sits slightly higher than prongs
        cy = y - prong_len - r
        cx = x
        ax.add_patch(Circle((cx, cy), r, facecolor='white', edgecolor=LINE_COLOR, lw=LINE_WIDTH, zorder=6))
        # 3 prongs to border at y
        ax.plot([x, x], [cy + r, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([x, x - prong_spread], [cy + r, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([x, x + prong_spread], [cy + r, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        return cy - r
    elif direction == 'bottom':
        # Table is above y. Prongs spread from circle down to y or from circle up to y
        # When child is reached at bottom of line (table top is above? No, table bottom):
        # Child connection at table bottom:
        cy = y + prong_len + r
        cx = x
        ax.add_patch(Circle((cx, cy), r, facecolor='white', edgecolor=LINE_COLOR, lw=LINE_WIDTH, zorder=6))
        ax.plot([x, x], [cy - r, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([x, x - prong_spread], [cy - r, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([x, x + prong_spread], [cy - r, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        return cy + r
    elif direction == 'left':
        # Prongs connect to x (table left border)
        cx = x - prong_len - r
        cy = y
        ax.add_patch(Circle((cx, cy), r, facecolor='white', edgecolor=LINE_COLOR, lw=LINE_WIDTH, zorder=6))
        ax.plot([cx + r, x], [y, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([cx + r, x], [y, y - prong_spread], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([cx + r, x], [y, y + prong_spread], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        return cx - r
    elif direction == 'right':
        # Prongs connect to x (table right border)
        cx = x + prong_len + r
        cy = y
        ax.add_patch(Circle((cx, cy), r, facecolor='white', edgecolor=LINE_COLOR, lw=LINE_WIDTH, zorder=6))
        ax.plot([cx - r, x], [y, y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([cx - r, x], [y, y - prong_spread], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        ax.plot([cx - r, x], [y, y + prong_spread], color=LINE_COLOR, lw=LINE_WIDTH, zorder=5)
        return cx + r

def draw_mandatory_one(x, y, orientation='vertical', offset=12, bar_len=14):
    """
    Draws two parallel tick marks across the line: ||
    orientation: 'vertical' (line is vertical, ticks are horizontal)
                 'horizontal' (line is horizontal, ticks are vertical)
    """
    half = bar_len / 2
    if orientation == 'vertical':
        # ticks are horizontal
        ax.plot([x - half, x + half], [y - 4, y - 4], color=LINE_COLOR, lw=1.6, zorder=6)
        ax.plot([x - half, x + half], [y + 4, y + 4], color=LINE_COLOR, lw=1.6, zorder=6)
    else:
        # ticks are vertical
        ax.plot([x - 4, x - 4], [y - half, y + half], color=LINE_COLOR, lw=1.6, zorder=6)
        ax.plot([x + 4, x + 4], [y - half, y + half], color=LINE_COLOR, lw=1.6, zorder=6)

def draw_optional_one(x, y, orientation='vertical', r=4.0, bar_len=14):
    """
    Draws circle + tick mark: o|
    """
    half = bar_len / 2
    if orientation == 'vertical':
        ax.add_patch(Circle((x, y - 6), r, facecolor='white', edgecolor=LINE_COLOR, lw=LINE_WIDTH, zorder=6))
        ax.plot([x - half, x + half], [y + 6, y + 6], color=LINE_COLOR, lw=1.6, zorder=6)
    else:
        ax.add_patch(Circle((x - 6, y), r, facecolor='white', edgecolor=LINE_COLOR, lw=LINE_WIDTH, zorder=6))
        ax.plot([x + 6, x + 6], [y - half, y + half], color=LINE_COLOR, lw=1.6, zorder=6)

def label_line(x, y, text):
    ax.text(x, y, text, ha='center', va='center', fontsize=9, fontfamily='sans-serif',
            color='#1B2631',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='white', edgecolor='none', alpha=0.95),
            zorder=7)

# ── DRAW ALL RELATIONSHIPS MATCHING REFERENCE ──

# 1. TEAMS -> PLAYERS ("has")
# From TEAMS bottom (left branch) -> PLAYERS top
teams_b = TABLES['TEAMS']['b']
teams_x = TABLES['TEAMS']['x']
t_pt1 = (teams_x + 50, teams_b)
draw_mandatory_one(t_pt1[0], t_pt1[1] + 12, 'vertical')
# line goes down to y=290, then left to players top x=350, then down to players top
p_top_y = TABLES['PLAYERS']['y']
p_x = 350
ax.plot([t_pt1[0], t_pt1[0]], [t_pt1[1], 290], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([t_pt1[0], p_x], [290, 290], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(p_x, p_top_y, 'top')
ax.plot([p_x, p_x], [290, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(p_x, 260, 'has')

# 2. TEAMS -> MATCHES ("home_team")
# From TEAMS bottom (mid-left) -> MATCHES top
t_pt2 = (teams_x + 100, teams_b)
draw_mandatory_one(t_pt2[0], t_pt2[1] + 12, 'vertical')
m_x1 = TABLES['MATCHES']['x'] + 100
m_top_y = TABLES['MATCHES']['y']
ax.plot([t_pt2[0], t_pt2[0]], [t_pt2[1], 310], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([t_pt2[0], m_x1], [310, 310], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(m_x1, m_top_y, 'top')
ax.plot([m_x1, m_x1], [310, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(m_x1, 310, 'home_team')

# 3. TEAMS -> MATCHES ("away_team")
# From TEAMS bottom (mid-right) -> MATCHES top
t_pt3 = (teams_x + 190, teams_b)
draw_mandatory_one(t_pt3[0], t_pt3[1] + 12, 'vertical')
m_x2 = TABLES['MATCHES']['x'] + 230
ax.plot([t_pt3[0], t_pt3[0]], [t_pt3[1], 310], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([t_pt3[0], m_x2], [310, 310], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(m_x2, m_top_y, 'top')
ax.plot([m_x2, m_x2], [310, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(m_x2, 310, 'away_team')

# 4. MATCHES -> PLAYER_MATCH_STATS ("records")
# From MATCHES bottom (left) -> PMS top
m_b = TABLES['MATCHES']['b']
m_pms_x = TABLES['MATCHES']['x'] + 40
draw_mandatory_one(m_pms_x, m_b + 12, 'vertical')
pms_x1 = TABLES['PLAYER_MATCH_STATS']['x'] + 200
pms_top_y = TABLES['PLAYER_MATCH_STATS']['y']
ax.plot([m_pms_x, m_pms_x], [m_b, 780], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([m_pms_x, pms_x1], [780, 780], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(pms_x1, pms_top_y, 'top')
ax.plot([pms_x1, pms_x1], [780, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(pms_x1, 755, 'records')

# 5. PLAYERS -> PLAYER_MATCH_STATS ("has")
# From PLAYERS bottom -> PMS top
p_b = TABLES['PLAYERS']['b']
p_pms_x = TABLES['PLAYERS']['x'] + 170
draw_mandatory_one(p_pms_x, p_b + 12, 'vertical')
pms_x2 = TABLES['PLAYER_MATCH_STATS']['x'] + 280
ax.plot([p_pms_x, p_pms_x], [p_b, 800], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([p_pms_x, pms_x2], [800, 800], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(pms_x2, pms_top_y, 'top')
ax.plot([pms_x2, pms_x2], [800, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(pms_x2, 775, 'has')

# 6. PLAYERS -> USER_TEAMS ("captain")
# From PLAYERS bottom right -> USER_TEAMS top
p_ut_x1 = TABLES['PLAYERS']['x'] + 240
draw_mandatory_one(p_ut_x1, p_b + 12, 'vertical')
ut_x1 = TABLES['USER_TEAMS']['x'] + 60
ut_top_y = TABLES['USER_TEAMS']['y']
ax.plot([p_ut_x1, p_ut_x1], [p_b, 740], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([p_ut_x1, ut_x1], [740, 740], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(ut_x1, ut_top_y, 'top')
ax.plot([ut_x1, ut_x1], [740, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(ut_x1 - 40, 740, 'captain')

# 7. PLAYERS -> USER_TEAMS ("vice_captain for")
p_ut_x2 = TABLES['PLAYERS']['x'] + 270
draw_mandatory_one(p_ut_x2, p_b + 12, 'vertical')
ut_x2 = TABLES['USER_TEAMS']['x'] + 140
ax.plot([p_ut_x2, p_ut_x2], [p_b, 770], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([p_ut_x2, ut_x2], [770, 770], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(ut_x2, ut_top_y, 'top')
ax.plot([ut_x2, ut_x2], [770, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(ut_x2, 750, 'vice_captain for')

# 8. MATCHES -> USER_TEAMS
# Straight down from MATCHES bottom to USER_TEAMS top
m_ut_x = TABLES['MATCHES']['x'] + 170
draw_mandatory_one(m_ut_x, m_b + 12, 'vertical')
ut_x3 = TABLES['USER_TEAMS']['x'] + 210
ax.plot([m_ut_x, m_ut_x], [m_b, 770], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([m_ut_x, ut_x3], [770, 770], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(ut_x3, ut_top_y, 'top')
ax.plot([ut_x3, ut_x3], [770, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)

# 9. USERS -> USER_TEAMS ("creates")
u_b = TABLES['USERS']['b']
u_ut_x = TABLES['USERS']['x'] + 60
draw_mandatory_one(u_ut_x, u_b + 12, 'vertical')
ut_x4 = TABLES['USER_TEAMS']['x'] + 280
ax.plot([u_ut_x, u_ut_x], [u_b, 760], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([u_ut_x, ut_x4], [760, 760], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(ut_x4, ut_top_y, 'top')
ax.plot([ut_x4, ut_x4], [760, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(ut_x4 + 30, 760, 'creates')

# 10. MATCHES -> CONTESTS ("hosts")
m_c_x = TABLES['MATCHES']['x'] + 280
draw_mandatory_one(m_c_x, m_b + 12, 'vertical')
c_top_y = TABLES['CONTESTS']['y']
c_x1 = TABLES['CONTESTS']['x'] + 110
ax.plot([m_c_x, m_c_x], [m_b, 750], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([m_c_x, c_x1], [750, 750], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(c_x1, c_top_y, 'top')
ax.plot([c_x1, c_x1], [750, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(c_x1, 740, 'hosts')

# 11. PLAYERS -> USER_TEAM_PLAYERS ("selected_in")
# Out left from PLAYERS, down far left margin, then in to UTP top
p_l_y = TABLES['PLAYERS']['y'] + 120
p_l_x = TABLES['PLAYERS']['x']
draw_mandatory_one(p_l_x - 12, p_l_y, 'horizontal')
utp_top_y = TABLES['USER_TEAM_PLAYERS']['y']
utp_x1 = TABLES['USER_TEAM_PLAYERS']['x'] + 80
ax.plot([p_l_x, 60], [p_l_y, p_l_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([60, 60], [p_l_y, 1430], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([60, utp_x1], [1430, 1430], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(utp_x1, utp_top_y, 'top')
ax.plot([utp_x1, utp_x1], [1430, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(60, 1100, 'selected_in')

# 12. USER_TEAMS -> USER_TEAM_PLAYERS ("contains")
ut_b = TABLES['USER_TEAMS']['b']
ut_utp_x = TABLES['USER_TEAMS']['x'] + 80
draw_mandatory_one(ut_utp_x, ut_b + 12, 'vertical')
utp_x2 = TABLES['USER_TEAM_PLAYERS']['x'] + 200
ax.plot([ut_utp_x, ut_utp_x], [ut_b, 1380], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([ut_utp_x, utp_x2], [1380, 1380], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(utp_x2, utp_top_y, 'top')
ax.plot([utp_x2, utp_x2], [1380, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(utp_x2 + 40, 1360, 'contains')

# 13. USER_TEAMS -> CONTEST_ENTRIES ("enters")
ut_ce_x = TABLES['USER_TEAMS']['x'] + 260
draw_mandatory_one(ut_ce_x, ut_b + 12, 'vertical')
ce_top_y = TABLES['CONTEST_ENTRIES']['y']
ce_x1 = TABLES['CONTEST_ENTRIES']['x'] + 90
ax.plot([ut_ce_x, ut_ce_x], [ut_b, 1400], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([ut_ce_x, ce_x1], [1400, 1400], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(ce_x1, ce_top_y, 'top')
ax.plot([ce_x1, ce_x1], [1400, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(ce_x1, 1370, 'enters')

# 14. CONTESTS -> CONTEST_ENTRIES ("receives")
c_b = TABLES['CONTESTS']['b']
c_ce_x = TABLES['CONTESTS']['x'] + 150
draw_mandatory_one(c_ce_x, c_b + 12, 'vertical')
ce_x2 = TABLES['CONTEST_ENTRIES']['x'] + 230
ax.plot([c_ce_x, c_ce_x], [c_b, 1420], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([c_ce_x, ce_x2], [1420, 1420], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(ce_x2, ce_top_y, 'top')
ax.plot([ce_x2, ce_x2], [1420, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(ce_x2, 1380, 'receives')

# 15. USERS -> WALLET_TRANSACTIONS ("makes")
# Out right from USERS, down far right margin, then into WT top
u_r_y = TABLES['USERS']['y'] + 140
u_r_x = TABLES['USERS']['x'] + TABLES['USERS']['w']
draw_mandatory_one(u_r_x + 12, u_r_y, 'horizontal')
wt_top_y = TABLES['WALLET_TRANSACTIONS']['y']
wt_x1 = TABLES['WALLET_TRANSACTIONS']['x'] + 280
ax.plot([u_r_x, 1500], [u_r_y, u_r_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([1500, 1500], [u_r_y, 1860], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([1500, wt_x1], [1860, 1860], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(wt_x1, wt_top_y, 'top')
ax.plot([wt_x1, wt_x1], [1860, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(1500, 1400, 'makes')

# 16. CONTEST_ENTRIES -> WALLET_TRANSACTIONS ("referenced_by")
# Optional one (o|) at CE bottom, optional many (o<) at WT top
ce_b = TABLES['CONTEST_ENTRIES']['b']
ce_wt_x = TABLES['CONTEST_ENTRIES']['x'] + 160
draw_optional_one(ce_wt_x, ce_b + 12, 'vertical')
wt_x2 = TABLES['WALLET_TRANSACTIONS']['x'] + 100
ax.plot([ce_wt_x, ce_wt_x], [ce_b, 1840], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
ax.plot([ce_wt_x, wt_x2], [1840, 1840], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
end_y = draw_crows_foot(wt_x2, wt_top_y, 'top')
ax.plot([wt_x2, wt_x2], [1840, end_y], color=LINE_COLOR, lw=LINE_WIDTH, zorder=4)
label_line(ce_wt_x, 1810, 'referenced_by')

# Save high-res image
output_path = '/Users/anuragchoubey/DE_Project_2026/diagrams/er_diagram.png'
plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"ER diagram successfully created at {output_path}")
