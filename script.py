import requests
import gspread
import time
import sys

# Get the arguments passed from the CLI
args = sys.argv


start_match_number = int(args[1])
end_match_number = int(args[2])

gc = gspread.oauth(credentials_filename="/Users/sachinsahoo/Downloads/client_secret_580195250675-q5oepop1meqifubtdlhntml9rnl7rrnu.apps.googleusercontent.com.json")

sh = gc.open("CBL 2023 Leaderboard")

gang = ["Kohli", "Sahoo", "Farji", "Boss", "Mittal", "Sandy", "Rana"]

players_info = sh.worksheet("Player Info").get("A2:D252")
player_dict = {}

for player in players_info:
    player_dict[player[1]] = player

matches_info = sh.worksheet("Match Info").get("A2:G75")

def calc_score(player, playerId, teamId, type, matchDay):
    if player_dict[player][3] != matches_info[matchDay-1][3] and player_dict[player][3] != matches_info[matchDay-1][5]:
        return 0

    url = "https://fantasy.iplt20.com/season/services/feed/player/card-stats?teamId=" + str(teamId) + "&playerId=" + str(playerId) + "&gamedayId=" + str(matchDay)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
    else:
        print("Error:", response.status_code, response.text)

    if data["Data"] is None or data["Data"]["Value"]["GamedayStats"][0]["IsPlayed"] == "0":
        return 0

    points = data["Data"]["Value"]["GamedayPoints"][0]

    print(player)
    if type == "Batting":
        score = int(points["RunsPoints"]) + int(points["FourPoints"]) + float(points["SixPoints"]) + int(points["HalfCenturyPoints"]) + int(points["FullCenturyPoints"]) + int(points["ThirtyBonusPoints"]) + int(points["StrikeRatePoints"]) + int(points["DuckOutPoints"])
    elif type == "Bowling":
        score = int(points["WicketPoints"]) + int(points["WktBonusPoints"]) + int(points["WicketBonusPoints"]) + int(points["MadinBonusPoint"]) + int(points["EconomyRatePoint"])
    else:
        score = int(data["Data"]["Value"]["GamedayStats"][0]["Sixes"])
    
    print(score)
    return score

def fetch_current_player(players_string):
    players_list = players_string.split('+')

    # Use list comprehension to apply strip() method on each substring
    player = players_list[0].strip()
    return player

for match_number in range(start_match_number, end_match_number + 1, 1):
    match_id_str = matches_info[match_number-1][1]
    
    for gang_member in gang:
        print("\n##" + gang_member + "##")
        batsmen = {}
        bowlers = {}
        six_hitters = {}
        scores_for_match = [[]]

        players = sh.worksheet(gang_member).get('B2:Q2')
        for i in range(6):
            player = fetch_current_player(players[0][i])
            # print(player)
            batsmen[player] = calc_score(player, player_dict[player][0], player_dict[player][2], "Batting", match_number)
            scores_for_match[0].append(batsmen[player])

        scores_for_match[0].append("")

        for i in range(6):
            player = fetch_current_player(players[0][7+i])
            # print(player)
            bowlers[player] = calc_score(player, player_dict[player][0], player_dict[player][2], "Bowling", match_number)
            scores_for_match[0].append(bowlers[player])
        
        scores_for_match[0].append("")

        for i in range(2):
            player = fetch_current_player(players[0][14+i])
            # print(player)
            six_hitters[player] = calc_score(player, player_dict[player][0], player_dict[player][2], "Sixes", match_number)
            scores_for_match[0].append(six_hitters[player])

        sh.worksheet(gang_member).update('B' + str(match_number + 2) + ":Q" + str(match_number + 2), scores_for_match)
    time.sleep(10)

time.sleep(20)

score_cols = ['C', 'E', 'G', 'I', 'K', 'M', 'O']

final_scores = {}

for i in range(7):
    scores = sh.worksheet("Leaderboard").get(score_cols[i] + '9:' + score_cols[i] + '24')
    final_scores[gang[i]] = []
    for j in range(16):
        final_scores[gang[i]].append(int(scores[j][0]))

overall_winnings = {}

for gang_member in gang:
    overall_winnings[gang_member] = -10000

for i in range(16):
    bet_size = 450
    if i == 6 or i == 13:
        bet_size = 1850
    total_pool = bet_size * 7
    temp_list = []
    for gang_member in gang:
        temp_list.append((final_scores[gang_member][i], gang_member))
    sorted_list = sorted(temp_list, key=lambda x: x[0], reverse=True)
    for j in range(7):
        print(str(sorted_list[j][0]) + " " + str(sorted_list[j][1]))
    print("\n")
    max_score = sorted_list[0][0]
    second_max_score = sorted_list[1][0]
    first_winners = []
    first_winners_string = ""
    second_winners = []
    second_winners_string = ""
    
    for j in range(7):
        if bet_size != 1850 or max_score == second_max_score:
            if sorted_list[j][0] < max_score:
                break
            first_winners.append(sorted_list[j][1])
            if first_winners_string != "":
                first_winners_string += ", "
            first_winners_string += sorted_list[j][1]
        else:
            if sorted_list[j][0] < second_max_score:
                break
            elif sorted_list[j][0] == max_score:
                first_winners.append(sorted_list[j][1])
                if first_winners_string != "":
                    first_winners_string += ", "
                first_winners_string += sorted_list[j][1]
            else:
                second_winners.append(sorted_list[j][1])
                if second_winners_string != "":
                    second_winners_string += ", "
                second_winners_string += sorted_list[j][1]

    first_winnings_per_person = 0
    second_winnings_per_person = 0
    
    if len(second_winners) == 0:
        first_winnings_per_person = total_pool / len(first_winners)
        for winner in first_winners:
            overall_winnings[winner] += first_winnings_per_person
    else:
        first_pool = 0.7 * total_pool
        second_pool = 0.3 * total_pool
        first_winnings_per_person = first_pool / len(first_winners)
        for winner in first_winners:
            overall_winnings[winner] += first_winnings_per_person

        second_winnings_per_person = second_pool / len(second_winners)
        for winner in second_winners:
            overall_winnings[winner] += second_winnings_per_person

    sh.worksheet("Leaderboard").update('Q' + str(9+i) + ":T" + str(9+i), [[first_winners_string, first_winnings_per_person, second_winners_string, second_winnings_per_person]])

for i in range(7):
    col = chr(ord(score_cols[i]) - 1)
    # print(score_cols[i] + " " + str(overall_winnings[gang[i]]))
    sh.worksheet("Leaderboard").update(col + '27', overall_winnings[gang[i]])
