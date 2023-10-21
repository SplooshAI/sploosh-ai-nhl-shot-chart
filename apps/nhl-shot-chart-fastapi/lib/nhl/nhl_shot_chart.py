# Heavily modified but inspired by the work at https://github.com/ztandrews/NHLShotCharts/blob/main/NHLGameShotChart.py

import arrow
import json
import os
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), 'configs')
import matplotlib.pyplot as plt
import pytz
import requests

from datetime import datetime as dt, timezone, timedelta
from fastapi.responses import HTMLResponse
from hockey_rink import NHLRink
from lib.qrcode.qrcode_generator import generate_qr_code_base64, generate_qr_code_for_text, generate_base64_image


# Global settings - Set to False if you do not want to display certain visual elements
SHOW_GOALS = True
SHOW_SHOTS_ON_GOAL = True
SHOW_SHOT_ATTEMPTS = True
SHOW_SHOT_ATTEMPTS_ANNOTATION = False

# Charts and graphs
GOAL_COLOR = "#4bad53"
GOAL_MARKER_SIZE = 20
GOAL_MARKER_TYPE = "*"

SHOT_ON_GOAL_COLOR = "#f0a911"
SHOT_ON_GOAL_MARKER_SIZE = 10
# See https://www.w3schools.com/python/matplotlib_markers.asp
SHOT_ON_GOAL_MARKER_TYPE = "o"

SHOT_ATTEMPT_COLOR = "#000000"
SHOT_ATTEMPT_MARKER_SIZE = 12
SHOT_ATTEMPT_MARKER_TYPE = "x"

OUTPUT_SEPARATOR = "\n\n*****\n\n"
OUTPUT_SHOT_CHART_DIRECTORY_AND_FILENAME_PREFIX = (
    os.getcwd()
    + "/tmp/shot-chart-"
)

# Date and time
LOCAL_DATE_TIME_FORMAT_STRING = "YYYY-MM-DD h:mm A z"  # '2023-01-19 7:00 PM PST'

# NHL API
NHL_API_BASE_URL = "https://statsapi.web.nhl.com/api/v1"
NHL_API_DATE_TIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%S%z"  # '2022-09-27T02:00:00Z'

def convertToLocalDateTimeString(dateTimeString, timezone):
    try:
        # Convert '2022-09-27T02:00:00Z' to '2022-09-26 07:00 PM PDT'
        utc_dt = dt.strptime(dateTimeString, NHL_API_DATE_TIME_FORMAT_STRING)

        # Get the timezone object using pytz
        local_tz = pytz.timezone(timezone)
        localized_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        timezone_abbr = localized_dt.strftime('%Z')  # Get the timezone abbreviation
        result = localized_dt.strftime('%Y-%m-%d %I:%M %p') + ' ' + timezone_abbr

        return result
    except Exception as e:
        print("Error converting to a local datetime string -> ", e)
        return None
    
# Utility method to either log or pretty print JSON data
def printJSON(data, indent=0):
    if indent == 0:
        print(OUTPUT_SEPARATOR + data + OUTPUT_SEPARATOR)
    else:
        print(OUTPUT_SEPARATOR + json.dumps(data, indent=indent) + OUTPUT_SEPARATOR)


# Generate a shot chart for a specific game ID from the NHL API
def generate_shot_chart_html(gameId, timezone):
    try:
        # Get the timezone object corresponding to the provided timezone
        tz = pytz.timezone(timezone)

        # Get the current time with the specified timezone
        server_time = dt.now(tz).isoformat()

        # NHL Gamecenter
        nhl_gamecenter_title = "NHL Gamecenter"
        nhl_gamecenter_url = f"""https://www.nhl.com/gamecenter/{gameId}"""

        # Shot chart
        shot_chart_title = "Shot Chart"
        shot_chart_url = f"""https://nhl-shot-chart-on-vercel-with-fastapi.vercel.app/?gameId={gameId}&timezone={timezone}"""
        shot_chart_img = generate_shot_chart_for_game(gameId, timezone)
        shot_chart_img_base64 = generate_base64_image(shot_chart_img)

        # QR codes
        qr_code_nhl_gamecenter_img_base64 = generate_qr_code_for_text(nhl_gamecenter_url)
        qr_code_shot_chart_img_base64 = generate_qr_code_for_text(shot_chart_url)

        # Generate HTML with captions
        html_content = f"""
        <html>
            <head>
                <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
                <style>
                    .qr-code {{
                        width: 200px;
                        height: 200px;
                    }}
                    .qr-code-container {{
                        display: flex;
                        justify-content: center;
                    }}
                </style>
            </head>
            <body>
                <div align="center">
                    <figure>
                        <img src="data:image/png;base64,{shot_chart_img_base64}" alt="{shot_chart_title}">
                        <figcaption>Shot Chart for Game ID <a href="{nhl_gamecenter_url}" target="_blank">{gameId}</a></figcaption>
                    </figure>
                    <p>Generated at {server_time}</p>
                    <div class="qr-code-container">
                        <figure>
                            <a href="{nhl_gamecenter_url}" target="_blank">
                                <img src="data:image/png;base64,{qr_code_nhl_gamecenter_img_base64}" alt="{nhl_gamecenter_title}" class="qr-code">
                            </a>
                            <figcaption>{nhl_gamecenter_title}</figcaption>
                        </figure>
                        <figure>
                            <a href="{shot_chart_url}" target="_blank">
                                <img src="data:image/png;base64,{qr_code_shot_chart_img_base64}" alt="{shot_chart_title}" class="qr-code">
                            </a>
                            <figcaption>{shot_chart_title}</figcaption>
                        </figure>
                    </div>
                </div>
            </body>
        </html>
        """

        return HTMLResponse(content=html_content, status_code=200)

    except Exception as e:
        error_html_content = f"""
        <html>
        <body>
            <h1>Error Generating Shot Chart</h1>
            <p>
                Sorry. We are unable to generate the shot chart for 
                    <a href="https://www.nhl.com/gamecenter/{gameId}" target="_blank">
                    this game
                    </a>
            </p>
            <pre>{e}</pre>
        </body>
        </html>
        """

        return HTMLResponse(content=error_html_content, status_code=500)

# Generate a shot chart for a specific game ID from the NHL API
def generate_shot_chart_with_schedule_html(gameId, teamId, seasonId, timezone):
    try:
        # Get the timezone object corresponding to the provided timezone
        tz = pytz.timezone(timezone)

        # Get the current time with the specified timezone
        server_time = dt.now(tz).isoformat()

        # NHL Gamecenter
        nhl_gamecenter_title = "NHL Gamecenter"
        nhl_gamecenter_url = f"""https://www.nhl.com/gamecenter/{gameId}"""

        # Shot chart
        shot_chart_title = "Shot Chart"
        shot_chart_url = f"""https://nhl-shot-chart-on-vercel-with-fastapi.vercel.app/?gameId={gameId}&timezone={timezone}"""
        shot_chart_img = generate_shot_chart_for_game(gameId, timezone)
        shot_chart_img_base64 = generate_base64_image(shot_chart_img)

        # QR codes
        qr_code_nhl_gamecenter_img_base64 = generate_qr_code_for_text(nhl_gamecenter_url)
        qr_code_shot_chart_img_base64 = generate_qr_code_for_text(shot_chart_url)

        # Generate HTML with captions
        html_content = f"""
        <html>
            <head>
                <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
                <style>
                    .qr-code {{
                        width: 200px;
                        height: 200px;
                    }}
                    .qr-code-container {{
                        display: flex;
                        justify-content: center;
                    }}
                    #scheduleTable {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0 auto;
                    }}          
                   #scheduleTable table {{
                        border-collapse: collapse;
                        width: 100%;
                        padding: 10px;
                    }}
                    #scheduleTable th, #scheduleTable td {{
                        padding: 8px;
                        border: 1px solid black;
                    }}
                </style>
                <script>
                    const timezone = encodeURIComponent(Intl.DateTimeFormat().resolvedOptions().timeZone);
                    const nhl_schedule = 'https://statsapi.web.nhl.com/api/v1/schedule?teamId={teamId}&season={seasonId}'

                    fetch(nhl_schedule)
                    .then(response => response.json())
                    .then(data => {{
                        const schedule = data.dates;
                        
                        // Create the table header
                        let tableHTML = '<table>';
                        tableHTML += '<tr><th>Date</th><th>gameId</th><th>gameDate</th><th>Away team</th><th>Home team</th></tr>';
                        
                        schedule.forEach(game => {{
                        const date = game.date;
                        const gameId = game.games[0].gamePk;
                        const gameDate = game.games[0].gameDate;
                        const link = game.games[0].link;
                        const awayTeam = game.games[0].teams.away.team.name;
                        const awayTeamId = game.games[0].teams.away.team.id;
                        const awayTeamScore = game.games[0].teams.away.score;
                        const homeTeam = game.games[0].teams.home.team.name;
                        const homeTeamId = game.games[0].teams.home.team.id;
                        const homeTeamScore = game.games[0].teams.home.score;

                        // Format the date in a human-friendly format
                        const formattedDate = new Date(gameDate).toLocaleDateString('en-US', {{
                        weekday: 'long',
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric',
                        hour: 'numeric',
                        minute: 'numeric',
                        timeZoneName: 'short'
                        }});

                        // Create the table row
                        tableHTML += `
                            <tr>
                                <td>${{date}}</td>
                                <td>${{createShotChartHyperlink(gameId)}}</td>
                                <td>${{gameDate}} - ${{formattedDate}}</td>
                                <td>${{createTeamHyperlink(gameId, awayTeamId, awayTeam)}} <strong>${{awayTeamScore}}</strong></td>
                                <td>${{createTeamHyperlink(gameId, homeTeamId, homeTeam)}} <strong>${{homeTeamScore}}</strong></td>
                            </tr>`;
                        }});

                        tableHTML += '</table>';

                        // Display the table in the HTML document
                        document.getElementById('scheduleTable').innerHTML = tableHTML;
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                    }});

                    // Helper function to create a hyperlink
                    function createHyperlink(text, url) {{
                    return `<a href="${{url}}">${{text}}</a>`;
                    }}

                    // Helper function to create a shot chart link
                    function createShotChartHyperlink(gameId) {{
                    return `<a href="/nhl-schedule?gameId=${{gameId}}&timezone=${{timezone}}">${{gameId}}</a>`;
                    }}

                    // Helper function to create a shot chart link
                    function createTeamHyperlink(gameId, teamId, teamName) {{
                    return `<a href="/nhl-schedule?gameId=${{gameId}}&teamId=${{teamId}}&timezone=${{timezone}}">${{teamName}}</a>`;
                    }}
                    
                </script>
            </head>
            <body>
                <div align="center">
                    <figure>
                        <img src="data:image/png;base64,{shot_chart_img_base64}" alt="{shot_chart_title}">
                        <figcaption>Shot Chart for Game ID <a href="{nhl_gamecenter_url}" target="_blank">{gameId}</a></figcaption>
                    </figure>
                    <p>Generated at {server_time}</p>
                    <div class="qr-code-container">
                        <figure>
                            <a href="{nhl_gamecenter_url}" target="_blank">
                                <img src="data:image/png;base64,{qr_code_nhl_gamecenter_img_base64}" alt="{nhl_gamecenter_title}" class="qr-code">
                            </a>
                            <figcaption>{nhl_gamecenter_title}</figcaption>
                        </figure>
                        <figure>
                            <a href="{shot_chart_url}" target="_blank">
                                <img src="data:image/png;base64,{qr_code_shot_chart_img_base64}" alt="{shot_chart_title}" class="qr-code">
                            </a>
                            <figcaption>{shot_chart_title}</figcaption>
                        </figure>
                    </div>
                </div>
                <div id="scheduleTable"></div>
            </body>
        </html>
        """

        return HTMLResponse(content=html_content, status_code=200)

    except Exception as e:
        error_html_content = f"""
        <html>
        <body>
            <h1>Error Generating Shot Chart</h1>
            <p>
                Sorry. We are unable to generate the shot chart for 
                    <a href="https://www.nhl.com/gamecenter/{gameId}" target="_blank">
                    this game
                    </a>
            </p>
            <pre>{e}</pre>
        </body>
        </html>
        """

        return HTMLResponse(content=error_html_content, status_code=500)

# Generate a shot chart for a specific game ID from the NHL API
def generate_shot_chart_for_game(gameId, timezone):
    try:
        data = parse_game_details(gameId, timezone)
    except Exception as e:
        print(f"Error parsing game details: {e}")
        data = {}  # default to empty data dict

    # Set default values
    gameStartLocalDateTime = ""
    currentPeriodTimeRemaining = ""
    currentPeriodOrdinal = ""
    away_team = "AWAY"
    away_goals = 0
    away_sog = 0
    away_shot_attempts = 0
    home_team = "HOME"
    home_goals = 0
    home_sog = 0
    home_shot_attempts = 0

    # Attempt to fetch actual values
    if "game" in data:
        result = data["game"]
        gameStartLocalDateTime = result.get("gameStart", gameStartLocalDateTime)
        currentPeriodTimeRemaining = result.get("currentPeriodTimeRemaining", currentPeriodTimeRemaining)
        currentPeriodOrdinal = result.get("currentPeriodOrdinal", currentPeriodOrdinal)
        away_team = result.get("awayTeam", away_team)
        away_goals = result.get("awayGoals", away_goals)
        away_sog = result.get("awayShotsOnGoal", away_sog)
        away_shot_attempts = result.get("awayShotAttempts", away_shot_attempts)
        home_team = result.get("homeTeam", home_team)
        home_goals = result.get("homeGoals", home_goals)
        home_sog = result.get("homeShotsOnGoal", home_sog)
        home_shot_attempts = result.get("homeShotAttempts", home_shot_attempts)

    title = (
        away_team
        + " "
        + str(away_goals)
        + " vs. "
        + home_team
        + " "
        + str(home_goals)
        + "\n"
        + currentPeriodTimeRemaining
        + " "
        + currentPeriodOrdinal
    )
    detail_line = (
        away_team
        + " - "
        + str(away_sog)
        + " SOG ("
        + str(away_shot_attempts)
        + " Total Shot Attempts) "
        + "     "
        + home_team
        + " - "
        + str(home_sog)
        + " SOG ("
        + str(home_shot_attempts)
        + " Total Shot Attempts)"
        + "\n"
        + gameStartLocalDateTime
    )

    fig = plt.figure(figsize=(10, 10))
    plt.xlim([0, 100])
    plt.ylim([-42.5, 42.5])

    rink = NHLRink()
    ax = rink.draw()

    if "game" in data and "charts" in data["game"] and "shotChart" in data["game"]["charts"]:
        elements = data["game"]["charts"]["shotChart"]["data"]
        for e in elements:
            plt.plot(
                e["x_calculated_shot_chart"],
                e["y_calculated_shot_chart"],
                e["markertype"],
                color=e["color"],
                markersize=int(e["markersize"]),
            )

            if SHOW_SHOT_ATTEMPTS_ANNOTATION:
                plt.text(
                    e["x_calculated_shot_chart"] - 1.2,
                    e["y_calculated_shot_chart"] - 1,
                    e["shot_attempts"],
                    horizontalalignment="left",
                    size="medium",
                    color="black",
                    weight="normal",
                )

    plt.title(title)
    plt.text(0, -53, detail_line, ha="center", fontsize=11, alpha=0.9)

    return plt

# Load live data for a specific game ID from the NHL API
def load_live_data_for_game(gameId):
    # https://statsapi.web.nhl.com/api/v1/game/2022020728/feed/live
    NHL_API_LIVE_GAME_DATA_URL = (
        NHL_API_BASE_URL + "/game/" + str(gameId) + "/feed/live"
    )
    live_data = requests.get(NHL_API_LIVE_GAME_DATA_URL).json()
    return live_data

def parse_game_details(gameId, timezone):
    # Initialize counters for processing all plays from the game
    home_shot_attempts = 0
    home_sog = 0
    home_goals = 0
    home_shootout_goals = 0
    away_shot_attempts = 0
    away_sog = 0
    away_goals = 0
    away_shootout_goals = 0

    try:
        # Load data for a specific game ID from the NHL API
        content = load_live_data_for_game(gameId)

        # Game details
        game_data = content["gameData"]
        eventDescription = content["liveData"]

        date = game_data["datetime"]
        gameStartLocalDateTime = convertToLocalDateTimeString(date["dateTime"], timezone)

        teams = game_data["teams"]
        away = teams["away"]
        home = teams["home"]
        away_team = away["abbreviation"]
        home_team = home["abbreviation"]

        linescore = eventDescription.get("linescore", {})

        try:
            currentPeriodTimeRemaining = linescore["currentPeriodTimeRemaining"]
        except KeyError:
            currentPeriodTimeRemaining = ""  # or any default value you'd like to provide

        try:
            currentPeriodOrdinal = linescore["currentPeriodOrdinal"]
        except KeyError:
            currentPeriodOrdinal = ""  # or any default value you'd like to provide

    except Exception as e:
        print(f"Error while parsing game details: {e}")
        return {
            "error": f"Error while parsing game details: {e}"
        }

    response = {
        "game": {
            "gameStart": gameStartLocalDateTime,
            "currentPeriodTimeRemaining": currentPeriodTimeRemaining,
            "currentPeriodOrdinal": currentPeriodOrdinal,
            "charts": {
                "shotChart": {
                    "data": []
                }
            },
            "awayTeam": away_team,
            "homeTeam": home_team
        },
        "source_data": content
    }

    # Process all event data
    try:
        # Charts and graphs
        charts = response["game"]["charts"]

        # Shot chart
        shotChart = charts["shotChart"]
        chartElements = shotChart["data"]

        plays = eventDescription["plays"]
        all_plays = plays["allPlays"]

        for event in all_plays:
            result = event["result"]  # Details for the event

            # Description of the event (e.g. Game Scheduled, Goal, Shot, Missed Shot, etc.)
            eventDescription = result["event"]

            if (
                eventDescription == "Goal"
                or eventDescription == "Shot"
                or eventDescription == "Missed Shot"
            ):
                datapoint = dict()
                eventDetails = event["about"]

                # Which team fired this shot?
                team_info = event["team"]
                team = team_info["triCode"]

                # Let's determine what counters we need to update at the end of our processing
                isHomeTeam = team == home_team
                isGoal = False
                isShotAttempt = False
                isShotOnGoal = False

                # Where did this event take place?
                coords = event["coordinates"]
                x = int(coords["x"])
                y = int(coords["y"])

                # For shot charts, we need to adjust the (x,y) location when both teams switch ends
                if isHomeTeam:
                    if x < 0:
                        x_calculated_shot_chart = abs(x)
                        y_calculated_shot_chart = y * -1
                    else:
                        x_calculated_shot_chart = x
                        y_calculated_shot_chart = y
                else:
                    if x > 0:
                        x_calculated_shot_chart = -x
                        y_calculated_shot_chart = -y
                    else:
                        x_calculated_shot_chart = x
                        y_calculated_shot_chart = y

                # Is this a goal?
                if eventDescription == "Goal":
                    # Account for shootout shots and goals
                    if event["about"]["periodType"] == "SHOOTOUT":
                        isGoal = False
                        isShotOnGoal = False
                        isShotAttempt = False

                        # Keep track of shootout goals separately
                        if isHomeTeam:
                            home_shootout_goals += 1
                        else:
                            away_shootout_goals += 1
                    else:
                        isGoal = True
                        isShotOnGoal = True
                        # FUTURE - Should isShotAttempt be set to False here? 🤔
                        isShotAttempt = True

                        # Track our goal - shootout or otherwise
                        datapoint["event_description"] = eventDescription
                        datapoint["x"] = x
                        datapoint["y"] = y
                        datapoint["x_calculated_shot_chart"] = x_calculated_shot_chart
                        datapoint["y_calculated_shot_chart"] = y_calculated_shot_chart
                        datapoint["markertype"] = GOAL_MARKER_TYPE
                        datapoint["color"] = GOAL_COLOR
                        datapoint["markersize"] = GOAL_MARKER_SIZE
                        datapoint["event_details"] = eventDetails
                        datapoint["team"] = team

                        if isHomeTeam:
                            datapoint["shot_attempts"] = home_shot_attempts
                        else:
                            datapoint["shot_attempts"] = away_shot_attempts

                        if SHOW_GOALS:
                            chartElements.append(datapoint)

                elif eventDescription == "Shot":
                    # Is this a shot on goal?
                    isShotAttempt = True
                    isShotOnGoal = True

                    datapoint["event_description"] = eventDescription
                    datapoint["x"] = x
                    datapoint["y"] = y
                    datapoint["x_calculated_shot_chart"] = x_calculated_shot_chart
                    datapoint["y_calculated_shot_chart"] = y_calculated_shot_chart
                    datapoint["markertype"] = SHOT_ON_GOAL_MARKER_TYPE
                    datapoint["color"] = SHOT_ON_GOAL_COLOR
                    datapoint["markersize"] = SHOT_ON_GOAL_MARKER_SIZE
                    datapoint["event_details"] = eventDetails
                    datapoint["team"] = team

                    if isHomeTeam:
                        datapoint["shot_attempts"] = home_shot_attempts
                    else:
                        datapoint["shot_attempts"] = away_shot_attempts

                    if SHOW_SHOTS_ON_GOAL:
                        chartElements.append(datapoint)
                else:
                    # Is this a missed shot?
                    isShotAttempt = True
                    isShotOnGoal = False

                    datapoint["event_description"] = eventDescription
                    datapoint["x"] = x
                    datapoint["y"] = y
                    datapoint["x_calculated_shot_chart"] = x_calculated_shot_chart
                    datapoint["y_calculated_shot_chart"] = y_calculated_shot_chart
                    datapoint["markertype"] = SHOT_ATTEMPT_MARKER_TYPE
                    datapoint["color"] = SHOT_ATTEMPT_COLOR
                    datapoint["markersize"] = SHOT_ATTEMPT_MARKER_SIZE
                    datapoint["event_details"] = eventDetails
                    datapoint["team"] = team

                    if isHomeTeam:
                        datapoint["shot_attempts"] = home_shot_attempts
                    else:
                        datapoint["shot_attempts"] = away_shot_attempts

                    if SHOW_SHOT_ATTEMPTS:
                        chartElements.append(datapoint)
            else:
                continue

            # Increment the appropriate counters
            if isHomeTeam:
                if isShotAttempt and event["about"]["periodType"] != "SHOOTOUT":
                    home_shot_attempts += 1

                if isGoal and event["about"]["periodType"] != "SHOOTOUT":
                    home_goals += 1

                if isShotOnGoal and event["about"]["periodType"] != "SHOOTOUT":
                    home_sog += 1
            else:
                if event["about"]["periodType"] != "SHOOTOUT":
                    if isShotAttempt and event["about"]["periodType"] != "SHOOTOUT":
                        away_shot_attempts += 1

                    if isGoal and event["about"]["periodType"] != "SHOOTOUT":
                        away_goals += 1
                    if isShotOnGoal and event["about"]["periodType"] != "SHOOTOUT":
                        away_sog += 1

            # Reset our booleans
            isShotAttempt = False
            isShotOnGoal = False
            isGoal = False


    except Exception as e:
        print(f"Error processing event data: {e}")

    # The final section for updating the response with team information, shot attempts, and goals
    # Add +1 goal to whomever has the most shootout goals
    if home_shootout_goals > away_shootout_goals:
        home_goals += 1
    elif away_shootout_goals > home_shootout_goals:
        away_goals += 1

    # Add away and home team information to our response
    # Away team stats and information
    response["game"]["awayTeam"] = away_team
    response["game"]["awayShotAttempts"] = away_shot_attempts
    response["game"]["awayShotsOnGoal"] = away_sog
    response["game"]["awayGoals"] = away_goals

    # Home team stats and information
    response["game"]["homeTeam"] = home_team
    response["game"]["homeShotAttempts"] = home_shot_attempts
    response["game"]["homeShotsOnGoal"] = home_sog
    response["game"]["homeGoals"] = home_goals

    return response