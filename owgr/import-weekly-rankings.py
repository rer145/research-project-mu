import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import csv
import pyodbc

RANKINGS_URL = "http://www.owgr.com/en/Ranking.aspx?pageNo={0}&pageSize=300&country=All"


def parse_ranking_table(soup):
    output = []
    table = soup.find('table')

    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        col_idx = 0
        data = {}

        if len(cols) > 0:
            for col in cols:
                text = col.text.strip()
                if text == '-':
                    text = '0'

                if col_idx == 0:
                    data['current_week_rank'] = text
                elif col_idx == 1:
                    data['last_week_rank'] = text
                elif col_idx == 3:
                    img = col.find('img')
                    data['country'] = img['title']
                elif col_idx == 4:
                    data['player_name'] = text
                    u = col.find('a')
                    data['player_id'] = u['href'].rsplit('=')[1]
                elif col_idx == 5:
                    data['avg_points'] = text
                elif col_idx == 6:
                    data['total_points'] = text
                elif col_idx == 7:
                    data['events_played_divisor'] = text
                elif col_idx == 10:
                    data['events_played_all'] = text

                col_idx = col_idx + 1

            output.append(data)

    return output


def parse_ranking_week(soup):
    h2 = soup.find_all('section', attrs={'id': 'ranking_table'})[0].find_all('h2')
    t = soup.find_all('time', attrs={'class': 'sub_header'})

    week_num = int(h2[0].text.replace('WEEK', '').strip())

    temp = t[0].text.strip().split(' ')
    temp[0] = temp[0][:-2]  # remove th, nd, st
    week_date = datetime.strptime(str(temp[1]) + ' ' + str(temp[0]) + ' ' + str(temp[2]), '%B %d %Y')

    return week_num, week_date


def get_soup(url):
    request = urllib.request.urlopen(url)
    html = request.read()
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def download_ranking_table(url):
    soup = get_soup(url)
    table = parse_ranking_table(soup)
    week_num, week_date = parse_ranking_week(soup)

    return week_num, week_date, table


def download_current_week():
    # get current week date
    soup = get_soup(RANKINGS_URL.replace('{0}', "1"))
    week_num, week_date = parse_ranking_week(soup)
    output_file = '../data/owgr-' + str(week_date.year) + '{:02d}'.format(week_date.month) + '{:02d}'.format(
        week_date.day) + '.csv'

    # create header and start of csv file
    header = [['player_id', 'player_name', 'country', 'week_of', 'rank', 'avg_points', 'total_points',
               'events_played_divisor', 'events_played_all']]
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(header)
        f.close()

    # loop through all pages and save data as csv
    for i in range(1, 31):
        soup = get_soup(RANKINGS_URL.replace('{0}', str(i)))
        output = parse_ranking_table(soup)

        csv_data = []
        for item in output:
            item_row = []
            item_row.append(str(item['player_id']))
            item_row.append(item['player_name'])
            item_row.append(item['country'])
            item_row.append(str(week_date))
            item_row.append(str(item['current_week_rank']))
            item_row.append(str(item['avg_points']))
            item_row.append(str(item['total_points']))
            item_row.append(str(item['events_played_divisor']))
            item_row.append(str(item['events_played_all']))
            csv_data.append(item_row)

        with open(output_file, 'a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            f.close()

    return output_file


def parse_full_name(name):
    is_amatuer = '(Am)' in name

    name = name.replace('(Am)', '').split(' ')
    if len(name) > 1:
        first_name = name[0]
        last_name = ' '.join(name[1:])
    else:
        first_name = name[0]
        last_name = ''

    return first_name.strip(), last_name.strip(), is_amatuer


def import_ranking_file(filepath):
    # open file and get all ranking data
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        history = list(reader)

    # loop through file and execute sql statements
    conn = pyodbc.connect(
        "Driver={SQL Server Native Client 11.0}; Server=THISRON; Database=ShotLink; Trusted_Connection=yes;",
        autocommit=True)
    cursor = conn.cursor()

    for row in history[1:]:
        if len(row) == 9:  # full weekly file
            player_id = row[0]
            player_name = row[1]
            country = row[2]
            week_of = row[3]
            ranking = int(row[4])
            avg_points = float(row[5])
            total_points = float(row[6])
            events_played_divisor = int(row[7])
            events_played_all = int(row[8])

        if len(row) == 4:  # full history file
            player_id = row[0]
            player_name = row[1]
            country = ''
            week_of = row[2]
            ranking = int(row[3])
            avg_points = 0.0
            total_points = 0.0
            events_played_divisor = 0
            events_played_all = 0

        first_name, last_name, is_amatuer = parse_full_name(player_name)

        sql = 'exec [ShotLink].[dbo].[OWGR_AddRanking] ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?'
        values = (
            str(player_id), player_name.replace('(Am)', '').strip(), first_name, last_name, country, str(is_amatuer),
            week_of, str(ranking), str(avg_points), str(total_points), str(events_played_divisor),
            str(events_played_all)
        )
        cursor.execute(sql, (values))

    cursor.close()
    conn.close()


print('Dowloading current week')
filepath = download_current_week()

print('Importing file:', filepath)
import_ranking_file(filepath)

print('Done with import')