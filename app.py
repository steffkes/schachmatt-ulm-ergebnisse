import streamlit as st
import pandas as pd
import altair as alt
import itertools
import requests

st.set_page_config(layout="wide", page_title="Schachmatt Ulm")
st.title("Schachmatt Ulm")

fieldNames = [
    "Startnummer",
    "_platz",
    "_bib",
    "Name",
    "Team",
    "qualified",
    "Zeit",
    "_differenz",
]


def dataMapper(entry):
    data = dict(zip(fieldNames, entry))
    data["Zeit"] = "00:0" + data["Zeit"][0:6]
    return data


def dataMapperQuali(row):
    return map(dataMapper, row)


def dataMapperRunde(row):
    [black, white] = row
    black = dataMapper(black)
    white = dataMapper(white)

    return [
        {**black, "Gegner": white["Startnummer"]},
        {**white, "Gegner": black["Startnummer"]},
    ]


def helper(runde, selector):
    r = requests.get(
        "https://my3.raceresult.com/313906/RRPublish/data/list",
        params={
            "key": "5af851eb0259b1c543aeba7da178780e",
            "listname": "01 - Online|Results",
            "page": "results",
            "contest": 1,
            "selectorResult": selector,
        },
    )

    df = pd.json_normalize(
        list(
            itertools.chain.from_iterable(
                map(
                    dataMapperQuali if runde == "Q" else dataMapperRunde,
                    r.json()["data"].values(),
                )
            )
        )
    )
    df["qualified"] = df["qualified"] == "Q"
    df["Runde"] = runde

    return df[df["_platz"] != "DNF"]


df = pd.concat(
    [
        helper(runde, selector)
        for (runde, selector) in [
            ("Q", 1),
            ("1", 2),
            ("2", 3),
            ("3", 4),
            ("4", 5),
            ("5", 6),
            ("6", 7),
            ("7", 8),
            ("7", 9),
        ]
    ]
)


def teamHelper(row):
    return (row["Startnummer"], "#{Startnummer}: {Name} ({Team})".format(**row))


teamLabels = dict(
    teamHelper(row)
    for (_index, row) in df[["Startnummer", "Name", "Team"]]
    .drop_duplicates()
    .iterrows()
)

selected_team = st.selectbox(
    "Für welches Team möchtest du die Ergebnisse sehen?",
    sorted(df["Startnummer"].unique().tolist(), key=int),
    format_func=lambda bib: teamLabels[bib],
)

roundsList = ["Q", "1", "2", "3", "4", "5", "6", "7"]
tooltips = [
    "Runde",
    alt.Tooltip("minutesseconds(Zeit)", title="Zeit"),
    "Startnummer",
    "Name",
    "Team",
    "qualified",
    "Gegner",
]

st.altair_chart(
    alt.layer(
        alt.Chart(df, title=teamLabels[selected_team])
        .mark_point()
        .transform_filter(alt.FieldEqualPredicate(field="Gegner", equal=selected_team))
        .encode(
            x=alt.X("Runde:O"),
            y=alt.Y("Zeit:T", timeUnit="minutesseconds").title("Zeit"),
            color=alt.Color("qualified", legend=None).scale(range=["#f00", "#080"]),
            tooltip=tooltips,
        ),
        alt.Chart(df)
        .mark_point()
        .transform_filter(
            alt.FieldEqualPredicate(field="Startnummer", equal=selected_team)
        )
        .encode(
            x=alt.X("Runde:O"),
            y=alt.Y("Zeit:T", timeUnit="minutesseconds").title("Zeit"),
            color=alt.Color("qualified", legend=None),
            tooltip=tooltips,
        ),
        alt.Chart(df)
        .mark_point(color="black")
        .transform_filter(
            alt.FieldEqualPredicate(field="Startnummer", equal=selected_team)
        )
        .encode(
            x=alt.X("Runde:O").axis(labelAngle=0).scale(domain=roundsList),
            y=alt.Y("Zeit:T", timeUnit="minutesseconds").title("Zeit"),
            tooltip=tooltips,
        ),
    ),
    use_container_width=True,
)

st.altair_chart(
    alt.Chart(df, title="Gelaufene Zeiten pro Runde")
    .mark_point()
    .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())")
    .encode(
        x=alt.X("Runde:O").axis(labelAngle=0).scale(domain=roundsList),
        y=alt.Y("Zeit:T", timeUnit="minutesseconds").title("Zeit"),
        xOffset="jitter:Q",
        color=alt.Color("Runde", legend=None),
        tooltip=[
            "Runde",
            alt.Tooltip("minutesseconds(Zeit)", title="Zeit"),
        ],
    ),
    use_container_width=True,
)

dsq1 = df[(df["Runde"] == "1") & (df["qualified"] == False)]
ll1 = df[
    (df["Startnummer"].isin(dsq1["Startnummer"])) & ~(df["Runde"].isin(["Q", "1"]))
]
grouped = ll1.groupby("Startnummer").agg(
    Runden=("Runde", "max"),
)

st.altair_chart(
    alt.Chart(grouped, title="Wann sind die Lucky Loosers ausgeschieden?")
    .mark_bar()
    .encode(
        x=alt.X("Runden", title="Runde").axis(labelAngle=0).scale(domain=roundsList),
        y=alt.Y("count()", title="Anzahl"),
    ),
    use_container_width=True,
)


if st.checkbox("Rohdaten anzeigen?"):
    st.write(df)
