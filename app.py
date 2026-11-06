
from flask import Flask, request, render_template_string
import math

app = Flask(__name__)

def poisson(lam, goals):
    return (math.exp(-lam) * lam**goals) / math.factorial(goals)

def analyze(data):
    home = data["home"]
    away = data["away"]

    # Expected goals from attack and defensive weakness
    xh = (data["h_scored"] + data["a_conceded"]) / 2
    xa = (data["a_scored"] + data["h_conceded"]) / 2

    xh = max(0.15, min(xh, 4.5))
    xa = max(0.15, min(xa, 4.5))

    scores = {}
    for h in range(9):
        for a in range(9):
            scores[(h, a)] = poisson(xh, h) * poisson(xa, a)

    total = sum(scores.values())
    scores = {k: v / total for k, v in scores.items()}

    p_home = sum(p for (h, a), p in scores.items() if h > a)
    p_draw = sum(p for (h, a), p in scores.items() if h == a)
    p_away = sum(p for (h, a), p in scores.items() if h < a)

    p_over15 = sum(p for (h, a), p in scores.items() if h + a > 1)
    p_over25 = sum(p for (h, a), p in scores.items() if h + a > 2)
    p_over35 = sum(p for (h, a), p in scores.items() if h + a > 3)

    p_btts = sum(p for (h, a), p in scores.items() if h > 0 and a > 0)

    markets = [
        (home + " Win", p_home),
        ("Draw", p_draw),
        (away + " Win", p_away),
        ("1X - " + home or "1X", p_home + p_draw),
        ("X2 - " + away, p_away + p_draw),
        ("Over 1.5 Goals", p_over15),
        ("Over 2.5 Goals", p_over25),
        ("Over 3.5 Goals", p_over35),
        ("Under 2.5 Goals", 1 - p_over25),
        ("BTTS - Yes", p_btts),
        ("BTTS - No", 1 - p_btts)
    ]

    # Select the highest-probability market
    joker = max(markets, key=lambda x: x[1])
    probability = joker[1]
    fair_odd = 1 / probability if probability > 0 else 0

    best_scores = sorted(
        scores.items(), key=lambda x: x[1], reverse=True
    )[:5]

    return {
        "xh": xh,
        "xa": xa,
        "home": p_home,
        "draw": p_draw,
        "away": p_away,
        "over15": p_over15,
        "over25": p_over25,
        "over35": p_over35,
        "btts": p_btts,
        "joker": joker[0],
        "prob": probability * 100,
        "odd": fair_odd,
        "scores": best_scores
    }


PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>COTE JOKER AI ELITE</title>
<style>
*{box-sizing:border-box}
body{
 background:#09090d;color:#eee;
 font-family:Arial,sans-serif;
 margin:0;padding:20px;
}
.container{max-width:650px;margin:auto}
header{text-align:center;padding:25px 5px}
h1{letter-spacing:3px;font-size:27px}
.red{color:#ff354b}
.card{
 background:#15151b;border:1px solid #34343b;
 padding:20px;border-radius:12px;margin-bottom:18px;
}
h2{font-size:17px;color:#ff4655}
input{
 width:100%;padding:13px;margin:7px 0 14px;
 background:#09090d;border:1px solid #444;
 color:white;border-radius:7px;font-size:16px;
}
button{
 width:100%;padding:16px;background:#ed263b;
 color:white;border:0;border-radius:7px;
 font-weight:bold;font-size:16px;
}
.result{
 border:1px solid #ed3548;
 background:#211217;padding:20px;
 border-radius:10px;text-align:center;
}
.odd{font-size:48px;color:#ff4054;font-weight:bold}
.percent{font-size:27px;color:#fff}
.line{
 display:flex;justify-content:space-between;
 border-bottom:1px solid #333;padding:10px 0;
}
.small{color:#999;font-size:12px;line-height:1.6}
</style>
</head>
<body>
<div class="container">
<header>
<h1>COTE <span class="red">JOKER</span></h1>
<p>MATCH INTELLIGENCE AI V1.0</p>
<p class="small">LOCAL STATISTICAL ENGINE</p>
</header>

<form method="POST">
<div class="card">
<h2>01 / MATCH IDENTIFICATION</h2>
<label>Home Team</label>
<input name="home" placeholder="Celtic" required>
<label>Away Team</label>
<input name="away" placeholder="Besiktas" required>
</div>

<div class="card">
<h2>02 / HOME TEAM STATISTICS</h2>
<label>Home goals scored per match</label>
<input name="h_scored" type="number" step="0.01" min="0" max="8" required>
<label>Home goals conceded per match</label>
<input name="h_conceded" type="number" step="0.01" min="0" max="8" required>
</div>

<div class="card">
<h2>03 / AWAY TEAM STATISTICS</h2>
<label>Away goals scored per match</label>
<input name="a_scored" type="number" step="0.01" min="0" max="8" required>
<label>Away goals conceded per match</label>
<input name="a_conceded" type="number" step="0.01" min="0" max="8" required>
</div>

<button type="submit">⚡ ANALYSE THE MATCH</button>
</form>

{% if result %}
<div class="card">
<h2>ANALYSIS VALIDATED</h2>
<p>{{home}} VS {{away}}</p>
<div class="result">
<p>YOUR JOKER SELECTION</p>
<h2>{{result.joker}}</h2>
<div class="odd">{{"%.2f"|format(result.odd)}}</div>
<p>FAIR ODDS</p>
<div class="percent">{{"%.2f"|format(result.prob)}}%</div>
<p class="small">Estimated probability</p>
</div>
</div>

<div class="card">
<h2>EXPECTED GOALS</h2>
<div class="line"><span>{{home}} xG</span><b>{{"%.2f"|format(result.xh)}}</b></div>
<div class="line"><span>{{away}} xG</span><b>{{"%.2f"|format(result.xa)}}</b></div>
</div>

<div class="card">
<h2>MARKET PROBABILITIES</h2>
{% for name,value in [
("Home Win",result.home),("Draw",result.draw),
("Away Win",result.away),
("Over 1.5",result.over15),
("Over 2.5",result.over25),
("Over 3.5",result.over35),
("BTTS Yes",result.btts)
] %}
<div class="line">
<span>{{name}}</span><b>{{"%.1f"|format(value*100)}}%</b>
</div>
{% endfor %}
</div>

<div class="card">
<h2>TOP EXACT SCORES</h2>
{% for score,p in result.scores %}
<div class="line">
<span>{{score[0]}} - {{score[1]}}</span>
<b>{{"%.2f"|format(p*100)}}%</b>
</div>
{% endfor %}
</div>

<p class="small">
Model estimates only. Fair odds are not bookmaker odds.
No outcome is guaranteed. Limited statistics can reduce accuracy.
</p>
{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    home = ""
    away = ""

    if request.method == "POST":
        try:
            home = request.form["home"].strip()
            away = request.form["away"].strip()

            data = {
                "home": home,
                "away": away,
                "h_scored": float(request.form["h_scored"]),
                "h_conceded": float(request.form["h_conceded"]),
                "a_scored": float(request.form["a_scored"]),
                "a_conceded": float(request.form["a_conceded"])
            }

            if not home or not away:
                raise ValueError("Team names required")

            if any(v < 0 or v > 8 for k, v in data.items()
                   if k not in ("home", "away")):
                raise ValueError("Statistics must be between 0 and 8")

            result = analyze(data)

        except (ValueError, KeyError):
            return "Invalid match data. Please check your inputs.", 400

    return render_template_string(
        PAGE, result=result, home=home, away=away
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
